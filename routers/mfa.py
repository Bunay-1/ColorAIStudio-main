"""
MFA Router for ICAP Enterprise
==============================
REST API endpoints for multi-factor authentication management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List, Optional
import logging

from utils.mfa_service import (
    MFAService, MFASetup, MFAVerification, MFAMethod
)
from utils.auth import get_current_user

router = APIRouter(prefix="/mfa", tags=["MFA"])
logger = logging.getLogger("MFA_Router")

mfa_service = MFAService()

@router.post("/setup")
async def setup_mfa(
    current_user: dict = Depends(get_current_user)
):
    """
    Set up MFA for the current user.
    
    Returns secret, QR code, and backup codes for initial setup.
    """
    try:
        setup = mfa_service.setup_mfa(current_user["username"])
        
        return {
            "user_id": setup.user_id,
            "secret": setup.secret,
            "qr_code": setup.qr_code,
            "backup_codes": setup.backup_codes,
            "created_at": setup.created_at
        }
        
    except Exception as e:
        logger.error(f"Error setting up MFA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enable")
async def enable_mfa(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Enable MFA for the current user after verification.
    
    - **secret**: TOTP secret from setup
    - **verification_code**: Verification code from authenticator app
    """
    try:
        success = mfa_service.enable_mfa(
            user_id=current_user["username"],
            secret=data["secret"],
            verification_code=data["verification_code"]
        )
        
        if success:
            return {"status": "success", "message": "MFA enabled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Invalid verification code")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling MFA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disable")
async def disable_mfa(
    current_user: dict = Depends(get_current_user)
):
    """Disable MFA for the current user."""
    try:
        success = mfa_service.disable_mfa(current_user["username"])
        
        if success:
            return {"status": "success", "message": "MFA disabled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to disable MFA")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling MFA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify")
async def verify_mfa(
    data: dict,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Verify MFA code for the current user.
    
    - **code**: MFA code to verify
    - **method**: MFA method (totp, backup_codes)
    """
    try:
        method = MFAMethod(data.get("method", "totp"))
        
        verification = mfa_service.verify_mfa(
            user_id=current_user["username"],
            code=data["code"],
            method=method,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        if verification.success:
            return {
                "status": "success",
                "method": verification.method.value,
                "verified_at": verification.verified_at
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid MFA code")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying MFA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_mfa_status(
    current_user: dict = Depends(get_current_user)
):
    """Get MFA status for the current user."""
    try:
        is_enabled = mfa_service.is_mfa_enabled(current_user["username"])
        
        return {
            "user_id": current_user["username"],
            "mfa_enabled": is_enabled,
            "method": "totp" if is_enabled else None
        }
        
    except Exception as e:
        logger.error(f"Error getting MFA status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backup-codes")
async def get_backup_codes(
    current_user: dict = Depends(get_current_user)
):
    """Get remaining unused backup codes for the current user."""
    try:
        if not mfa_service.is_mfa_enabled(current_user["username"]):
            raise HTTPException(status_code=400, detail="MFA is not enabled")
        
        codes = mfa_service.get_remaining_backup_codes(current_user["username"])
        
        return {
            "user_id": current_user["username"],
            "remaining_codes": len(codes),
            "codes": codes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backup codes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backup-codes/regenerate")
async def regenerate_backup_codes(
    current_user: dict = Depends(get_current_user)
):
    """Regenerate backup codes for the current user."""
    try:
        if not mfa_service.is_mfa_enabled(current_user["username"]):
            raise HTTPException(status_code=400, detail="MFA is not enabled")
        
        new_codes = mfa_service.regenerate_backup_codes(current_user["username"])
        
        return {
            "user_id": current_user["username"],
            "backup_codes": new_codes,
            "message": "Backup codes regenerated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating backup codes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
