"""
Configuration Validation Module for ICAP
==========================================
Validates environment configuration at startup to prevent runtime errors.
"""

import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

logger = logging.getLogger("ConfigValidator")

class DatabaseConfig(BaseModel):
    """Database configuration validation."""
    database_url: str = Field(default="AuditTrail/icap_enterprise.db")
    
    @validator('database_url')
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("Database URL cannot be empty")
        return v

class OllamaConfig(BaseModel):
    """Ollama LLM configuration validation."""
    url: str = Field(default="http://localhost:11434/api/generate")
    model: str = Field(default="irm-industrial")
    timeout: int = Field(default=120)
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith('http'):
            raise ValueError("Ollama URL must start with http:// or https://")
        return v
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("Ollama timeout must be positive")
        return v

class QdrantConfig(BaseModel):
    """Qdrant vector database configuration validation."""
    url: str = Field(default="")
    
    @validator('url')
    def validate_url(cls, v):
        # Empty URL means local storage mode
        if v and not v.startswith('http'):
            raise ValueError("Qdrant URL must be empty (for local) or start with http://")
        return v

class SecurityConfig(BaseModel):
    """Security configuration validation."""
    environment: str = Field(default="development")
    allowed_origins: str = Field(default="http://localhost:3000,http://localhost:8000")
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ['development', 'staging', 'production']
        if v.lower() not in valid_envs:
            logger.warning(f"Invalid environment '{v}'. Defaulting to 'development'")
            return 'development'
        return v.lower()
    
    @validator('allowed_origins')
    def validate_origins(cls, v):
        if not v:
            raise ValueError("Allowed origins cannot be empty")
        return v

class IoTConfig(BaseModel):
    """IoT connectivity configuration validation."""
    mqtt_broker: str = Field(default="192.168.1.50")
    mqtt_port: int = Field(default=1883)
    opc_ua_server_url: str = Field(default="opc.tcp://192.168.1.100:4840/")
    
    @validator('mqtt_port')
    def validate_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError("MQTT port must be between 1 and 65535")
        return v
    
    @validator('opc_ua_server_url')
    def validate_opc_url(cls, v):
        if not v.startswith('opc.tcp://'):
            raise ValueError("OPC UA URL must start with opc.tcp://")
        return v

class ICAPConfig(BaseModel):
    """Main ICAP configuration."""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    iot: IoTConfig = Field(default_factory=IoTConfig)

def validate_config() -> Dict[str, Any]:
    """
    Validate all configuration and return validated config.
    Raises ValueError if critical configuration is invalid.
    Returns dictionary with validation results.
    """
    load_dotenv()
    
    results = {
        "valid": True,
        "warnings": [],
        "errors": [],
        "config": {}
    }
    
    try:
        # Validate Database Config
        db_config = DatabaseConfig(
            database_url=os.environ.get("ICAP_DATABASE_URL", "AuditTrail/icap_enterprise.db")
        )
        results["config"]["database"] = db_config.dict()
        logger.info("✅ Database configuration valid")
        
    except Exception as e:
        results["errors"].append(f"Database config error: {str(e)}")
        results["valid"] = False
    
    try:
        # Validate Ollama Config
        ollama_config = OllamaConfig(
            url=os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate"),
            model=os.environ.get("OLLAMA_MODEL", "irm-industrial"),
            timeout=int(os.environ.get("OLLAMA_TIMEOUT", "120"))
        )
        results["config"]["ollama"] = ollama_config.dict()
        logger.info("✅ Ollama configuration valid")
        
    except Exception as e:
        results["errors"].append(f"Ollama config error: {str(e)}")
        results["valid"] = False
    
    try:
        # Validate Qdrant Config
        qdrant_config = QdrantConfig(
            url=os.environ.get("QDRANT_URL", "")
        )
        results["config"]["qdrant"] = qdrant_config.dict()
        logger.info("✅ Qdrant configuration valid")
        
    except Exception as e:
        results["errors"].append(f"Qdrant config error: {str(e)}")
        results["valid"] = False
    
    try:
        # Validate Security Config
        security_config = SecurityConfig(
            environment=os.environ.get("ICAP_ENVIRONMENT", "development"),
            allowed_origins=os.environ.get("ICAP_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000")
        )
        results["config"]["security"] = security_config.dict()
        
        # Security warnings
        if security_config.environment == "production":
            if "*" in security_config.allowed_origins:
                results["warnings"].append("⚠️  SECURITY: CORS wildcard (*) enabled in production!")
            if os.environ.get("ICAP_ALLOWED_ORIGINS", "").startswith("*"):
                results["warnings"].append("⚠️  SECURITY: Using wildcard CORS origins is not recommended")
        
        logger.info("✅ Security configuration valid")
        
    except Exception as e:
        results["errors"].append(f"Security config error: {str(e)}")
        results["valid"] = False
    
    try:
        # Validate IoT Config
        iot_config = IoTConfig(
            mqtt_broker=os.environ.get("MQTT_BROKER", "192.168.1.50"),
            mqtt_port=int(os.environ.get("MQTT_PORT", "1883")),
            opc_ua_server_url=os.environ.get("OPC_UA_SERVER_URL", "opc.tcp://192.168.1.100:4840/")
        )
        results["config"]["iot"] = iot_config.dict()
        logger.info("✅ IoT configuration valid")
        
    except Exception as e:
        results["errors"].append(f"IoT config error: {str(e)}")
        results["valid"] = False
    
    # Print warnings
    for warning in results["warnings"]:
        logger.warning(warning)
    
    # Print errors
    for error in results["errors"]:
        logger.error(f"❌ {error}")
    
    if results["valid"]:
        logger.info("✅ All configuration validated successfully")
    else:
        logger.error("❌ Configuration validation failed. Please fix the errors above.")
    
    return results

def check_service_connectivity() -> Dict[str, bool]:
    """
    Check connectivity to external services.
    Returns dictionary with service availability status.
    """
    import httpx
    results = {}
    
    # Check Ollama
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    base_url = ollama_url.replace("/api/generate", "")
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(base_url)
            results["ollama"] = response.status_code == 200
            if results["ollama"]:
                logger.info("✅ Ollama service is reachable")
            else:
                logger.warning("⚠️  Ollama service returned non-200 status")
    except Exception as e:
        results["ollama"] = False
        logger.warning(f"⚠️  Ollama service not reachable: {str(e)}")
    
    # Check Qdrant (if URL is set)
    qdrant_url = os.environ.get("QDRANT_URL", "")
    if qdrant_url:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{qdrant_url}/health")
                results["qdrant"] = response.status_code == 200
                if results["qdrant"]:
                    logger.info("✅ Qdrant service is reachable")
                else:
                    logger.warning("⚠️  Qdrant service returned non-200 status")
        except Exception as e:
            results["qdrant"] = False
            logger.warning(f"⚠️  Qdrant service not reachable: {str(e)}")
    else:
        results["qdrant"] = True  # Local mode, no connectivity check needed
        logger.info("✅ Qdrant in local storage mode")
    
    return results
