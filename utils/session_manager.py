"""
Session Management and Concurrency Control for ICAP
===================================================
Session tracking and concurrency control for enterprise deployments.
"""

import os
import time
import logging
import uuid
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import threading

logger = logging.getLogger("SessionManager")

# Session configuration
SESSION_TIMEOUT_MINUTES = int(os.environ.get("ICAP_SESSION_TIMEOUT", "480"))
MAX_CONCURRENT_SESSIONS = int(os.environ.get("ICAP_MAX_CONCURRENT_SESSIONS", "10"))
MAX_CONCURRENT_OPERATIONS = int(os.environ.get("ICAP_MAX_CONCURRENT_OPERATIONS", "5"))

class Session:
    """User session representation."""
    
    def __init__(
        self,
        session_id: str,
        user_id: str,
        user_role: str,
        tenant_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.user_role = user_role
        self.tenant_id = tenant_id
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        self.is_active = True
        self.operations: Set[str] = set()  # Track active operations
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, timeout_minutes: int = SESSION_TIMEOUT_MINUTES) -> bool:
        """Check if session is expired."""
        expiry_time = self.last_activity + timedelta(minutes=timeout_minutes)
        return datetime.utcnow() > expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "tenant_id": self.tenant_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_active": self.is_active,
            "active_operations": len(self.operations)
        }

class SessionManager:
    """Manager for user sessions and concurrency control."""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}  # session_id -> Session
        self.user_sessions: Dict[str, Set[str]] = defaultdict(set)  # user_id -> session_ids
        self.tenant_sessions: Dict[str, Set[str]] = defaultdict(set)  # tenant_id -> session_ids
        self.active_operations: Dict[str, Set[str]] = defaultdict(set)  # user_id -> operation_ids
        
        self._lock = threading.Lock()
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def create_session(
        self,
        user_id: str,
        user_role: str,
        tenant_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Session:
        """
        Create a new user session.
        
        Args:
            user_id: User ID
            user_role: User role
            tenant_id: Tenant ID
            ip_address: IP address
            user_agent: User agent string
            
        Returns:
            Created session
        """
        with self._lock:
            # Check max concurrent sessions per user
            user_session_count = len(self.user_sessions[user_id])
            if user_session_count >= MAX_CONCURRENT_SESSIONS:
                # Remove oldest inactive session
                oldest_session_id = None
                oldest_time = None
                
                for session_id in self.user_sessions[user_id]:
                    session = self.sessions.get(session_id)
                    if session and (oldest_time is None or session.last_activity < oldest_time):
                        oldest_time = session.last_activity
                        oldest_session_id = session_id
                
                if oldest_session_id:
                    self.terminate_session(oldest_session_id)
            
            # Create new session
            session_id = str(uuid.uuid4())
            session = Session(
                session_id=session_id,
                user_id=user_id,
                user_role=user_role,
                tenant_id=tenant_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.sessions[session_id] = session
            self.user_sessions[user_id].add(session_id)
            self.tenant_sessions[tenant_id].add(session_id)
            
            logger.info(f"Session created: {session_id} for user {user_id}")
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and session.is_active and not session.is_expired():
                session.update_activity()
                return session
            elif session and session.is_expired():
                self.terminate_session(session_id)
            return None
    
    def terminate_session(self, session_id: str) -> bool:
        """
        Terminate a session.
        
        Args:
            session_id: Session ID to terminate
            
        Returns:
            True if session was terminated, False if not found
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            # Mark as inactive
            session.is_active = False
            
            # Remove from tracking
            self.user_sessions[session.user_id].discard(session_id)
            self.tenant_sessions[session.tenant_id].discard(session_id)
            
            # Clean up empty sets
            if not self.user_sessions[session.user_id]:
                del self.user_sessions[session.user_id]
            if not self.tenant_sessions[session.tenant_id]:
                del self.tenant_sessions[session.tenant_id]
            
            # Remove from sessions dict
            del self.sessions[session_id]
            
            logger.info(f"Session terminated: {session_id}")
            return True
    
    def terminate_user_sessions(self, user_id: str) -> int:
        """
        Terminate all sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions terminated
        """
        with self._lock:
            session_ids = list(self.user_sessions.get(user_id, set()))
            count = 0
            for session_id in session_ids:
                if self.terminate_session(session_id):
                    count += 1
            return count
    
    def terminate_tenant_sessions(self, tenant_id: str) -> int:
        """
        Terminate all sessions for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Number of sessions terminated
        """
        with self._lock:
            session_ids = list(self.tenant_sessions.get(tenant_id, set()))
            count = 0
            for session_id in session_ids:
                if self.terminate_session(session_id):
                    count += 1
            return count
    
    def start_operation(
        self,
        session_id: str,
        operation_id: str,
        operation_type: str
    ) -> bool:
        """
        Start a new operation within a session.
        
        Args:
            session_id: Session ID
            operation_id: Operation ID
            operation_type: Type of operation
            
        Returns:
            True if operation started, False if limit reached
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if not session or not session.is_active:
                return False
            
            user_id = session.user_id
            
            # Check max concurrent operations per user
            operation_count = len(self.active_operations[user_id])
            if operation_count >= MAX_CONCURRENT_OPERATIONS:
                logger.warning(f"Max concurrent operations reached for user {user_id}")
                return False
            
            # Start operation
            session.operations.add(operation_id)
            self.active_operations[user_id].add(operation_id)
            
            logger.info(f"Operation started: {operation_id} ({operation_type}) for user {user_id}")
            return True
    
    def end_operation(self, session_id: str, operation_id: str):
        """
        End an operation within a session.
        
        Args:
            session_id: Session ID
            operation_id: Operation ID
        """
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.operations.discard(operation_id)
                self.active_operations[session.user_id].discard(operation_id)
                
                # Clean up empty sets
                if not self.active_operations[session.user_id]:
                    del self.active_operations[session.user_id]
                
                logger.info(f"Operation ended: {operation_id}")
    
    def get_user_sessions(self, user_id: str) -> list:
        """Get all active sessions for a user."""
        with self._lock:
            session_ids = self.user_sessions.get(user_id, set())
            sessions = []
            for session_id in session_ids:
                session = self.sessions.get(session_id)
                if session and session.is_active and not session.is_expired():
                    sessions.append(session.to_dict())
            return sessions
    
    def get_tenant_sessions(self, tenant_id: str) -> list:
        """Get all active sessions for a tenant."""
        with self._lock:
            session_ids = self.tenant_sessions.get(tenant_id, set())
            sessions = []
            for session_id in session_ids:
                session = self.sessions.get(session_id)
                if session and session.is_active and not session.is_expired():
                    sessions.append(session.to_dict())
            return sessions
    
    def get_all_sessions(self) -> list:
        """Get all active sessions."""
        with self._lock:
            sessions = []
            for session in self.sessions.values():
                if session.is_active and not session.is_expired():
                    sessions.append(session.to_dict())
            return sessions
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        with self._lock:
            active_sessions = sum(1 for s in self.sessions.values() if s.is_active and not s.is_expired())
            total_users = len(self.user_sessions)
            total_tenants = len(self.tenant_sessions)
            active_operations = sum(len(ops) for ops in self.active_operations.values())
            
            return {
                "active_sessions": active_sessions,
                "total_users": total_users,
                "total_tenants": total_tenants,
                "active_operations": active_operations,
                "max_concurrent_sessions": MAX_CONCURRENT_SESSIONS,
                "max_concurrent_operations": MAX_CONCURRENT_OPERATIONS
            }
    
    def _start_cleanup_thread(self):
        """Start background thread to clean up expired sessions."""
        def cleanup():
            while True:
                try:
                    time.sleep(60)  # Check every minute
                    self._cleanup_expired_sessions()
                except Exception as e:
                    logger.error(f"Error in cleanup thread: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
        logger.info("Session cleanup thread started")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        with self._lock:
            expired_sessions = []
            for session_id, session in self.sessions.items():
                if session.is_expired():
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                self.terminate_session(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

# Global session manager instance
session_manager = SessionManager()

# Convenience functions
def create_user_session(
    user_id: str,
    user_role: str,
    tenant_id: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Session:
    """Convenience function to create a user session."""
    return session_manager.create_session(
        user_id=user_id,
        user_role=user_role,
        tenant_id=tenant_id,
        ip_address=ip_address,
        user_agent=user_agent
    )

def get_active_session(session_id: str) -> Optional[Session]:
    """Convenience function to get an active session."""
    return session_manager.get_session(session_id)

def end_user_session(session_id: str) -> bool:
    """Convenience function to end a user session."""
    return session_manager.terminate_session(session_id)
