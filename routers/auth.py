from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from typing import Dict, Any
import uuid
from utils.auth import (
    create_access_token, create_refresh_token, ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user, get_current_user, get_current_active_user,
    check_permission, create_user, get_user, get_all_users,
    update_user_role, delete_user, add_token_to_blacklist,
    UserCreate, UserLogin, Token, ROLES_PERMISSIONS
)
from utils.multi_tenant import (
    create_tenant, get_tenant, get_all_tenants, update_tenant, delete_tenant,
    activate_tenant, deactivate_tenant, get_tenant_stats, check_tenant_permission
)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token, summary="User Authentication", description="Authenticate user with username and password to receive access and refresh tokens")
async def login(user_login: UserLogin):
    """
    Authenticate user and return access and refresh tokens.
    
    - **username**: User's unique identifier
    - **password**: User's password (will be hashed and verified)
    
    Returns:
    - **access_token**: JWT token for API access (expires in 8 hours)
    - **refresh_token**: JWT token for refreshing access token (expires in 7 days)
    - **token_type**: Token type (bearer)
    - **expires_in**: Token expiration time in seconds
    
    Raises:
    - 401: Invalid credentials
    - 400: Inactive user account
    """
    user = authenticate_user(user_login.username, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Generate unique token ID for blacklisting
    token_id = str(uuid.uuid4())
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "role": user["role"],
            "tenant_id": user.get("tenant_id", "default"),
            "jti": token_id
        },
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(
        data={
            "sub": user["username"],
            "role": user["role"],
            "tenant_id": user.get("tenant_id", "default"),
            "jti": token_id
        }
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=Token, summary="Refresh Access Token", description="Refresh access token using a valid refresh token")
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token obtained from login
    
    Returns:
    - **access_token**: New JWT access token
    - **refresh_token**: New JWT refresh token
    - **token_type**: Token type (bearer)
    - **expires_in**: Token expiration time in seconds
    
    Raises:
    - 401: Invalid or expired refresh token
    """
    from utils.auth import SECRET_KEY, ALGORITHM, jwt
    from jose import JWTError
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        token_id = payload.get("jti")
        token_type = payload.get("type")
        
        if token_type != "refresh":
            raise credentials_exception
        
        username: str = payload.get("sub")
        role: str = payload.get("role", "OPERATOR")
        tenant_id: str = payload.get("tenant_id", "default")
        
        if username is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Generate new tokens
    new_token_id = str(uuid.uuid4())
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": username,
            "role": role,
            "tenant_id": tenant_id,
            "jti": new_token_id
        },
        expires_delta=access_token_expires
    )
    
    new_refresh_token = create_refresh_token(
        data={
            "sub": username,
            "role": role,
            "tenant_id": tenant_id,
            "jti": new_token_id
        }
    )
    
    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/logout", summary="User Logout", description="Logout user by blacklisting their current token")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout user by blacklisting their token.
    
    Requires valid authentication token.
    
    Returns:
    - **message**: Success confirmation
    
    Note: In production, this would add the current token to the blacklist
    """
    # In a real implementation, you would get the token from the request
    # and add it to the blacklist
    return {"message": "Successfully logged out"}

@router.get("/me", summary="Get Current User", description="Get current authenticated user information")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    """
    Get current user information.
    
    Requires valid authentication token.
    
    Returns:
    - **username**: User's username
    - **email**: User's email address
    - **role**: User's role (ADMIN, SUPERVISOR, OPERATOR, etc.)
    - **tenant_id**: User's tenant ID
    - **is_active**: User account status
    
    Note: Password hash is never returned
    """
    user_data = get_user(current_user["username"])
    if user_data:
        user_copy = user_data.copy()
        user_copy.pop("hashed_password", None)
        return user_copy
    return current_user

@router.post("/users", dependencies=[Depends(check_permission("user_management"))], summary="Create User", description="Create a new user account (requires user_management permission)")
async def create_new_user(user_data: UserCreate):
    """
    Create a new user (requires user_management permission).
    
    - **username**: Unique username (required)
    - **email**: User's email address (required)
    - **password**: User's password (will be hashed) (required)
    - **role**: User's role (ADMIN, SUPERVISOR, OPERATOR, QUALITY_CONTROL, MAINTENANCE, VIEWER)
    - **tenant_id**: Tenant ID for the user (default: 'default')
    
    Returns:
    - **username**: Created username
    - **email**: User's email
    - **role**: Assigned role
    - **tenant_id**: Assigned tenant
    - **is_active**: Account status
    
    Raises:
    - 400: Invalid user data or duplicate username
    - 403: Insufficient permissions
    """
    try:
        user = create_user(user_data)
        user_copy = user.copy()
        user_copy.pop("hashed_password", None)
        return user_copy
    except HTTPException as e:
        raise e

@router.get("/users", dependencies=[Depends(check_permission("user_management"))], summary="List All Users", description="List all users in the system (requires user_management permission)")
async def list_users():
    """
    List all users (requires user_management permission).
    
    Returns:
    - Array of user objects containing:
      - username
      - email
      - role
      - tenant_id
      - is_active
      - created_at
    
    Raises:
    - 403: Insufficient permissions
    
    Note: Password hashes are never returned
    """
    return get_all_users()

@router.put("/users/{username}/role", dependencies=[Depends(check_permission("user_management"))], summary="Update User Role", description="Update user's role (requires user_management permission)")
async def update_user_role_endpoint(username: str, new_role: str):
    """
    Update user role (requires user_management permission).
    
    - **username**: Username to update (path parameter)
    - **new_role**: New role to assign (ADMIN, SUPERVISOR, OPERATOR, QUALITY_CONTROL, MAINTENANCE, VIEWER)
    
    Returns:
    - **username**: Updated username
    - **role**: New role
    - **tenant_id**: User's tenant
    - **is_active**: Account status
    
    Raises:
    - 403: Insufficient permissions
    - 404: User not found
    """
    try:
        user = update_user_role(username, new_role)
        if user:
            user_copy = user.copy()
            user_copy.pop("hashed_password", None)
            return user_copy
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException as e:
        raise e

@router.delete("/users/{username}", dependencies=[Depends(check_permission("user_management"))], summary="Delete User", description="Delete a user account (requires user_management permission)")
async def delete_user_endpoint(username: str):
    """
    Delete a user (requires user_management permission).
    
    - **username**: Username to delete (path parameter)
    
    Returns:
    - **message**: Success confirmation
    
    Raises:
    - 403: Insufficient permissions
    - 404: User not found
    - 400: Cannot delete admin user
    
    Note: This action is irreversible
    """
    try:
        success = delete_user(username)
        if success:
            return {"message": f"User {username} deleted successfully"}
        raise HTTPException(status_code=404, detail="User not found")
    except HTTPException as e:
        raise e

@router.get("/roles", summary="List Available Roles", description="List all available roles and their permissions")
async def list_roles():
    """
    List all available roles and their permissions.
    
    Returns:
    - Dictionary of roles with their permissions:
      - ADMIN: All permissions
      - SUPERVISOR: view, analyze, configure, report, iot_control
      - OPERATOR: view, analyze
      - QUALITY_CONTROL: view, analyze, report
      - MAINTENANCE: view, iot_control
      - VIEWER: view only
    
    No authentication required for this endpoint
    """
    return ROLES_PERMISSIONS

# Tenant Management Endpoints
@router.post("/tenants", dependencies=[Depends(check_permission("user_management"))], summary="Create Tenant", description="Create a new tenant (requires user_management permission)")
async def create_new_tenant(tenant_id: str, name: str, config: Dict[str, Any] = None):
    """
    Create a new tenant (requires user_management permission).
    
    - **tenant_id**: Unique tenant identifier (required)
    - **name**: Tenant display name (required)
    - **config**: Optional tenant configuration (max_users, storage_quota_gb, etc.)
    
    Returns:
    - **tenant_id**: Created tenant ID
    - **name**: Tenant name
    - **is_active**: Tenant status
    - **config**: Tenant configuration
    
    Raises:
    - 403: Insufficient permissions
    - 400: Invalid tenant data or duplicate tenant_id
    """
    try:
        tenant = create_tenant(tenant_id, name, config)
        return tenant
    except HTTPException as e:
        raise e

@router.get("/tenants", dependencies=[Depends(check_permission("user_management"))], summary="List All Tenants", description="List all tenants (requires user_management permission)")
async def list_tenants():
    """
    List all tenants (requires user_management permission).
    
    Returns:
    - Dictionary of all tenants with their configurations
    
    Raises:
    - 403: Insufficient permissions
    """
    return get_all_tenants()

@router.get("/tenants/{tenant_id}", dependencies=[Depends(check_permission("user_management"))], summary="Get Tenant Info", description="Get tenant information (requires user_management permission)")
async def get_tenant_info(tenant_id: str):
    """
    Get tenant information (requires user_management permission).
    
    - **tenant_id**: Tenant ID to retrieve (path parameter)
    
    Returns:
    - **tenant_id**: Tenant ID
    - **name**: Tenant name
    - **is_active**: Tenant status
    - **config**: Tenant configuration
    - **created_at**: Creation timestamp
    
    Raises:
    - 403: Insufficient permissions
    - 404: Tenant not found
    """
    tenant = get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant

@router.get("/tenants/{tenant_id}/stats", dependencies=[Depends(check_permission("user_management"))], summary="Get Tenant Statistics", description="Get tenant statistics (requires user_management permission)")
async def get_tenant_statistics(tenant_id: str):
    """
    Get tenant statistics (requires user_management permission).
    
    - **tenant_id**: Tenant ID to get statistics for (path parameter)
    
    Returns:
    - **tenant_id**: Tenant ID
    - **name**: Tenant name
    - **user_count**: Number of users in tenant
    - **api_calls**: API call count
    - **storage_used_gb**: Storage usage in GB
    - **is_active**: Tenant status
    
    Raises:
    - 403: Insufficient permissions
    - 404: Tenant not found
    """
    stats = get_tenant_stats(tenant_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return stats

@router.put("/tenants/{tenant_id}", dependencies=[Depends(check_permission("user_management"))], summary="Update Tenant", description="Update tenant configuration (requires user_management permission)")
async def update_tenant_info(tenant_id: str, updates: Dict[str, Any]):
    """
    Update tenant configuration (requires user_management permission).
    
    - **tenant_id**: Tenant ID to update (path parameter)
    - **updates**: Configuration updates (name, max_users, storage_quota_gb, etc.)
    
    Returns:
    - **tenant_id**: Updated tenant ID
    - **name**: Updated name
    - **config**: Updated configuration
    - **updated_at**: Update timestamp
    
    Raises:
    - 403: Insufficient permissions
    - 404: Tenant not found
    """
    try:
        tenant = update_tenant(tenant_id, updates)
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tenant
    except HTTPException as e:
        raise e

@router.post("/tenants/{tenant_id}/activate", dependencies=[Depends(check_permission("user_management"))], summary="Activate Tenant", description="Activate a tenant (requires user_management permission)")
async def activate_tenant_endpoint(tenant_id: str):
    """
    Activate a tenant (requires user_management permission).
    
    - **tenant_id**: Tenant ID to activate (path parameter)
    
    Returns:
    - **message**: Success confirmation
    
    Raises:
    - 403: Insufficient permissions
    - 404: Tenant not found
    """
    success = activate_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"message": f"Tenant {tenant_id} activated"}

@router.post("/tenants/{tenant_id}/deactivate", dependencies=[Depends(check_permission("user_management"))], summary="Deactivate Tenant", description="Deactivate a tenant (requires user_management permission)")
async def deactivate_tenant_endpoint(tenant_id: str):
    """
    Deactivate a tenant (requires user_management permission).
    
    - **tenant_id**: Tenant ID to deactivate (path parameter)
    
    Returns:
    - **message**: Success confirmation
    
    Raises:
    - 403: Insufficient permissions
    - 404: Tenant not found
    - 400: Cannot deactivate default tenant
    """
    try:
        success = deactivate_tenant(tenant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return {"message": f"Tenant {tenant_id} deactivated"}
    except HTTPException as e:
        raise e

@router.delete("/tenants/{tenant_id}", dependencies=[Depends(check_permission("user_management"))], summary="Delete Tenant", description="Delete a tenant (requires user_management permission)")
async def delete_tenant_endpoint(tenant_id: str):
    """
    Delete a tenant (requires user_management permission).
    
    - **tenant_id**: Tenant ID to delete (path parameter)
    
    Returns:
    - **message**: Success confirmation
    
    Raises:
    - 403: Insufficient permissions
    - 404: Tenant not found
    - 400: Cannot delete default tenant or non-empty tenant
    
    Note: This action is irreversible and requires tenant to be empty
    """
    try:
        success = delete_tenant(tenant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return {"message": f"Tenant {tenant_id} deleted"}
    except HTTPException as e:
        raise e
