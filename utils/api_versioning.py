"""
API Versioning Module for ICAP Enterprise
=========================================
Support for multiple API versions with backward compatibility.
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional, Dict, Any
import logging
from enum import Enum

logger = logging.getLogger("API_Versioning")

class APIVersion(str, Enum):
    """Supported API versions."""
    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"

class APIVersionConfig:
    """Configuration for API versioning."""
    
    def __init__(self):
        self.default_version = APIVersion.V1
        self.supported_versions = [APIVersion.V1, APIVersion.V2]
        self.deprecated_versions = []
        self.version_headers = {
            APIVersion.V1: "application/vnd.icap.v1+json",
            APIVersion.V2: "application/vnd.icap.v2+json"
        }
        self.version_paths = {
            APIVersion.V1: "/api/v1",
            APIVersion.V2: "/api/v2"
        }

# Global version configuration
version_config = APIVersionConfig()

def get_api_version(
    request: Request,
    accept: Optional[str] = Header(None),
    api_version: Optional[str] = Header(None, alias="API-Version")
) -> APIVersion:
    """
    Extract API version from request headers or query parameters.
    
    Priority:
    1. API-Version header
    2. Accept header with vendor-specific media type
    3. URL path
    4. Default version
    
    Args:
        request: FastAPI request object
        accept: Accept header value
        api_version: API-Version header value
    
    Returns:
        API version enum value
    
    Raises:
        HTTPException: If version is not supported
    """
    # Check API-Version header
    if api_version:
        try:
            version = APIVersion(api_version.lower())
            if version in version_config.supported_versions:
                return version
            elif version in version_config.deprecated_versions:
                logger.warning(f"Deprecated API version requested: {version}")
                return version
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported API version: {api_version}. "
                           f"Supported versions: {[v.value for v in version_config.supported_versions]}"
                )
        except ValueError:
            pass
    
    # Check Accept header for vendor-specific media type
    if accept:
        for version, media_type in version_config.version_headers.items():
            if media_type in accept:
                return version
    
    # Check URL path
    path = request.url.path
    for version, path_prefix in version_config.version_paths.items():
        if path.startswith(path_prefix):
            return version
    
    # Return default version
    return version_config.default_version

def version_response(
    data: Any,
    version: APIVersion,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Wrap response data with version information.
    
    Args:
        data: Response data
        version: API version used
        metadata: Additional metadata to include
    
    Returns:
        Versioned response dictionary
    """
    response = {
        "data": data,
        "version": version.value,
        "metadata": {
            "timestamp": None,  # Will be set by middleware
            "request_id": None,  # Will be set by middleware
            **(metadata or {})
        }
    }
    return response

def check_version_compatibility(
    requested_version: APIVersion,
    required_version: APIVersion = APIVersion.V1
) -> bool:
    """
    Check if requested version is compatible with required version.
    
    Args:
        requested_version: Version requested by client
        required_version: Minimum version required
    
    Returns:
        True if compatible, False otherwise
    """
    version_order = [APIVersion.V1, APIVersion.V2]
    
    try:
        requested_index = version_order.index(requested_version)
        required_index = version_order.index(required_version)
        return requested_index >= required_index
    except ValueError:
        return False

def deprecate_version(version: APIVersion, sunset_date: str, migration_guide: str):
    """
    Mark an API version as deprecated.
    
    Args:
        version: Version to deprecate
        sunset_date: Date when version will be removed
        migration_guide: URL to migration guide
    """
    if version not in version_config.deprecated_versions:
        version_config.deprecated_versions.append(version)
        logger.warning(
            f"API version {version.value} deprecated. "
            f"Sunset date: {sunset_date}. "
            f"Migration guide: {migration_guide}"
        )

def add_version_headers(response: Any, version: APIVersion):
    """
    Add version-related headers to response.
    
    Args:
        response: FastAPI response object
        version: API version used
    """
    response.headers["API-Version"] = version.value
    response.headers["X-API-Supported-Versions"] = ",".join([v.value for v in version_config.supported_versions])
    
    if version in version_config.deprecated_versions:
        response.headers["X-API-Deprecated"] = "true"
        response.headers["X-API-Sunset-Date"] = "2026-12-31"  # Example sunset date
        response.headers["X-API-Migration-Guide"] = "https://docs.icap-enterprise.com/migration"

class VersionedAPIRouter(APIRouter):
    """
    API Router with versioning support.
    """
    
    def __init__(self, version: APIVersion, **kwargs):
        """
        Initialize versioned router.
        
        Args:
            version: API version for this router
            **kwargs: Additional arguments for APIRouter
        """
        prefix = kwargs.get('prefix', '')
        if prefix and not prefix.startswith('/api/'):
            prefix = f"/api/{version.value}{prefix}"
        kwargs['prefix'] = prefix
        kwargs['tags'] = kwargs.get('tags', []) + [f"API {version.value}"]
        super().__init__(**kwargs)
        self.version = version

# Version-specific response transformers
class ResponseTransformer:
    """Transform responses based on API version."""
    
    @staticmethod
    def transform_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform v1 response format to v2 format.
        
        Args:
            data: v1 format data
        
        Returns:
            v2 format data
        """
        # Example transformation logic
        if "delta_e" in data:
            # v1 uses delta_e, v2 uses deltaE
            data["deltaE"] = data.pop("delta_e")
        
        if "lab_sample" in data:
            # v1 uses list, v2 uses object
            data["labSample"] = {
                "L": data["lab_sample"][0],
                "a": data["lab_sample"][1],
                "b": data["lab_sample"][2]
            }
            del data["lab_sample"]
        
        return data
    
    @staticmethod
    def transform_v2_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform v2 response format to v1 format.
        
        Args:
            data: v2 format data
        
        Returns:
            v1 format data
        """
        # Example transformation logic
        if "deltaE" in data:
            # v2 uses deltaE, v1 uses delta_e
            data["delta_e"] = data.pop("deltaE")
        
        if "labSample" in data:
            # v2 uses object, v1 uses list
            data["lab_sample"] = [
                data["labSample"]["L"],
                data["labSample"]["a"],
                data["labSample"]["b"]
            ]
            del data["labSample"]
        
        return data

def transform_response(data: Any, from_version: APIVersion, to_version: APIVersion) -> Any:
    """
    Transform response data between API versions.
    
    Args:
        data: Response data to transform
        from_version: Source version
        to_version: Target version
    
    Returns:
        Transformed data
    """
    if from_version == to_version:
        return data
    
    transformer = ResponseTransformer()
    
    if from_version == APIVersion.V1 and to_version == APIVersion.V2:
        return transformer.transform_v1_to_v2(data)
    elif from_version == APIVersion.V2 and to_version == APIVersion.V1:
        return transformer.transform_v2_to_v1(data)
    else:
        # No transformation defined
        return data

# Version negotiation middleware
async def version_middleware(request: Request, call_next):
    """
    Middleware to handle API versioning.
    
    Args:
        request: FastAPI request
        call_next: Next middleware or route handler
    
    Returns:
        Response with version headers
    """
    # Extract version from request
    accept = request.headers.get("accept")
    api_version = request.headers.get("API-Version")
    
    try:
        version = get_api_version(request, accept, api_version)
        request.state.api_version = version
    except HTTPException:
        # Let the exception propagate
        pass
    
    response = await call_next(request)
    
    # Add version headers to response
    if hasattr(request.state, 'api_version'):
        add_version_headers(response, request.state.api_version)
    
    return response
