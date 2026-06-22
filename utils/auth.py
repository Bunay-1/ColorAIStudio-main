from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
import os
import logging
from collections import defaultdict

logger = logging.getLogger("Auth")

SECRET_KEY = os.environ.get("ICAP_SECRET_KEY", "industrial-super-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ICAP_ACCESS_TOKEN_EXPIRE", "480"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("ICAP_REFRESH_TOKEN_EXPIRE", "7"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

# Role-based permissions
ROLES_PERMISSIONS = {
    "ADMIN": ["view", "analyze", "configure", "train", "delete", "report", "iot_control", "user_management"],
    "SUPERVISOR": ["view", "analyze", "configure", "report", "iot_control"],
    "OPERATOR": ["view", "analyze"],
    "QUALITY_CONTROL": ["view", "analyze", "report"],
    "MAINTENANCE": ["view", "iot_control"],
    "VIEWER": ["view"]
}

# Token blacklist for logout functionality
_token_blacklist = defaultdict(dict)  # token_id -> expiry_time

# Pydantic models
class User(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    role: str = "OPERATOR"
    tenant_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = datetime.utcnow()

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    password: str
    role: str = "OPERATOR"
    tenant_id: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

# In-memory user storage (in production, use database)
_users_db: Dict[str, Dict[str, Any]] = {
    "admin": {
        "username": "admin",
        "email": "admin@icap-enterprise.com",
        "hashed_password": pwd_context.hash("admin"),  # Change in production!
        "role": "ADMIN",
        "tenant_id": "default",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create an access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def add_token_to_blacklist(token_id: str, expiry_time: datetime):
    """Add a token to the blacklist."""
    _token_blacklist[token_id] = expiry_time
    logger.info(f"Token {token_id} added to blacklist")

def is_token_blacklisted(token_id: str) -> bool:
    """Check if a token is blacklisted."""
    if token_id in _token_blacklist:
        # Clean up expired blacklisted tokens
        if datetime.utcnow() > _token_blacklist[token_id]:
            del _token_blacklist[token_id]
            return False
        return True
    return False

def clean_expired_blacklisted_tokens():
    """Clean up expired tokens from blacklist."""
    now = datetime.utcnow()
    expired_tokens = [tid for tid, exp in _token_blacklist.items() if now > exp]
    for tid in expired_tokens:
        del _token_blacklist[tid]
    if expired_tokens:
        logger.info(f"Cleaned {len(expired_tokens)} expired blacklisted tokens")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get the current user from the JWT token.
    Supports legacy mode for backward compatibility.
    """
    # Legacy support: if no token and development mode, return default Admin
    if not token and os.environ.get("ICAP_ENVIRONMENT", "development") == "development":
        logger.warning("No token provided in development mode, returning default admin")
        return {"username": "admin", "role": "ADMIN", "tenant_id": "default"}

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_id = payload.get("jti")
        
        # Check if token is blacklisted
        if token_id and is_token_blacklisted(token_id):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        username: str = payload.get("sub")
        role: str = payload.get("role", "OPERATOR")
        tenant_id: str = payload.get("tenant_id", "default")
        token_type: str = payload.get("type", "access")
        
        if username is None:
            raise credentials_exception
        
        # Ensure it's an access token
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {"username": username, "role": role, "tenant_id": tenant_id}
        
    except JWTError as e:
        logger.error(f"JWT error: {e}")
        raise credentials_exception

async def get_current_active_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Get the current active user."""
    username = current_user.get("username")
    if username in _users_db:
        user_data = _users_db[username]
        if not user_data.get("is_active", True):
            raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def check_permission(required_perm: str):
    """
    Dependency to check if the current user has the required permission.
    """
    async def permission_dependency(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_role = current_user.get("role")
        user_perms = ROLES_PERMISSIONS.get(user_role, [])
        
        if required_perm not in user_perms:
            logger.warning(f"User {current_user.get('username')} with role {user_role} attempted to access resource requiring '{required_perm}'")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: '{required_perm}'"
            )
        return current_user
    return permission_dependency

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user with username and password."""
    user = _users_db.get(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_user(user_data: UserCreate) -> Dict[str, Any]:
    """Create a new user."""
    if user_data.username in _users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = get_password_hash(user_data.password)
    
    user = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "role": user_data.role,
        "tenant_id": user_data.tenant_id or "default",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    _users_db[user_data.username] = user
    logger.info(f"User {user_data.username} created with role {user_data.role}")
    return user

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get a user by username."""
    return _users_db.get(username)

def get_all_users() -> List[Dict[str, Any]]:
    """Get all users (excluding sensitive data)."""
    users = []
    for user_data in _users_db.values():
        user_copy = user_data.copy()
        user_copy.pop("hashed_password", None)
        users.append(user_copy)
    return users

def update_user_role(username: str, new_role: str) -> Optional[Dict[str, Any]]:
    """Update a user's role."""
    if username not in _users_db:
        return None
    if new_role not in ROLES_PERMISSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid role: {new_role}")
    
    _users_db[username]["role"] = new_role
    logger.info(f"User {username} role updated to {new_role}")
    return _users_db[username]

def delete_user(username: str) -> bool:
    """Delete a user."""
    if username not in _users_db:
        return False
    if username == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin user")
    
    del _users_db[username]
    logger.info(f"User {username} deleted")
    return True
