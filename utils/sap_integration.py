"""
SAP ERP Integration Module
===========================
Integration with SAP ERP system for enterprise resource planning.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests
from dataclasses import dataclass
import json

logger = logging.getLogger("SAPIntegration")

@dataclass
class SAPConfig:
    """SAP configuration settings."""
    base_url: str
    client_id: str
    client_secret: str
    system_id: str
    username: str
    password: str
    timeout: int = 30

class SAPIntegration:
    """
    SAP ERP integration for ICAP Platform.
    Handles communication with SAP ERP system via OData/REST API.
    """
    
    def __init__(self, config: SAPConfig):
        self.config = config
        self.base_url = config.base_url
        self.auth_token = None
        self.token_expiry = None
    
    def get_auth_token(self) -> str:
        """
        Get OAuth token for SAP API authentication.
        """
        try:
            auth_url = f"{self.base_url}/oauth/token"
            data = {
                "grant_type": "password",
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "username": self.config.username,
                "password": self.config.password
            }
            
            response = requests.post(
                auth_url,
                data=data,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.auth_token = token_data["access_token"]
            self.token_expiry = datetime.utcnow().timestamp() + token_data.get("expires_in", 3600)
            
            return self.auth_token
        except Exception as e:
            logger.error(f"Error getting SAP auth token: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        if not self.auth_token or (self.token_expiry and datetime.utcnow().timestamp() >= self.token_expiry):
            self.get_auth_token()
        
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_material_data(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch material data from SAP.
        
        Args:
            material_id: SAP material identifier
        
        Returns:
            Material data dictionary or None if not found
        """
        try:
            url = f"{self.base_url}/sap/opu/odata/sap/ZMATERIAL_SRV/Materials('{material_id}')"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            return response.json().get("d", {})
        except Exception as e:
            logger.error(f"Error fetching material data: {e}")
            return None
    
    def get_production_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch production order data from SAP.
        
        Args:
            order_id: Production order identifier
        
        Returns:
            Production order data dictionary or None if not found
        """
        try:
            url = f"{self.base_url}/sap/opu/odata/sap/ZPRODUCTION_SRV/ProductionOrders('{order_id}')"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            return response.json().get("d", {})
        except Exception as e:
            logger.error(f"Error fetching production order: {e}")
            return None
    
    def create_quality_notification(
        self,
        notification_type: str,
        material_id: str,
        batch_id: str,
        defect_description: str,
        severity: str = "MEDIUM"
    ) -> Optional[str]:
        """
        Create a quality notification in SAP.
        
        Args:
            notification_type: Type of notification (e.g., Q1, Q2)
            material_id: Material identifier
            batch_id: Batch identifier
            defect_description: Description of the defect
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
        
        Returns:
            Notification ID if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/sap/opu/odata/sap/ZQUALITY_SRV/QualityNotifications"
            
            payload = {
                "NotificationType": notification_type,
                "MaterialId": material_id,
                "BatchId": batch_id,
                "DefectDescription": defect_description,
                "Severity": severity,
                "CreatedAt": datetime.utcnow().isoformat(),
                "CreatedBy": "ICAP_SYSTEM"
            }
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("d", {}).get("NotificationId")
        except Exception as e:
            logger.error(f"Error creating quality notification: {e}")
            return None
    
    def update_quality_result(
        self,
        inspection_lot: str,
        result: str,
        delta_e: float,
        status: str
    ) -> bool:
        """
        Update quality inspection result in SAP.
        
        Args:
            inspection_lot: Inspection lot identifier
            result: Quality result (PASS/FAIL)
            delta_e: Delta E value
            status: Final status
        
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/sap/opu/odata/sap/ZQUALITY_SRV/InspectionLots('{inspection_lot}')"
            
            payload = {
                "Result": result,
                "DeltaE": delta_e,
                "Status": status,
                "UpdatedAt": datetime.utcnow().isoformat(),
                "UpdatedBy": "ICAP_SYSTEM"
            }
            
            response = requests.patch(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            return True
        except Exception as e:
            logger.error(f"Error updating quality result: {e}")
            return False
    
    def get_batch_data(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch batch data from SAP.
        
        Args:
            batch_id: Batch identifier
        
        Returns:
            Batch data dictionary or None if not found
        """
        try:
            url = f"{self.base_url}/sap/opu/odata/sap/ZBATCH_SRV/Batches('{batch_id}')"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            return response.json().get("d", {})
        except Exception as e:
            logger.error(f"Error fetching batch data: {e}")
            return None
    
    def sync_measurements_to_sap(self, measurements: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Synchronize measurement data to SAP.
        
        Args:
            measurements: List of measurement dictionaries
        
        Returns:
            Dictionary with success and failure counts
        """
        success_count = 0
        failure_count = 0
        
        for measurement in measurements:
            try:
                # Create quality notification for failed measurements
                if measurement.get("status") == "Fail":
                    notification_id = self.create_quality_notification(
                        notification_type="Q1",
                        material_id=measurement.get("client_id", ""),
                        batch_id=measurement.get("batch_id", ""),
                        defect_description=f"Delta E {measurement.get('delta_e')} exceeds tolerance",
                        severity="HIGH"
                    )
                    
                    if notification_id:
                        success_count += 1
                    else:
                        failure_count += 1
                else:
                    # Update quality result for passed measurements
                    inspection_lot = measurement.get("batch_id", "")
                    if self.update_quality_result(
                        inspection_lot=inspection_lot,
                        result="PASS",
                        delta_e=measurement.get("delta_e", 0.0),
                        status="APPROVED"
                    ):
                        success_count += 1
                    else:
                        failure_count += 1
            except Exception as e:
                logger.error(f"Error syncing measurement: {e}")
                failure_count += 1
        
        return {
            "success": success_count,
            "failure": failure_count,
            "total": len(measurements)
        }
    
    def get_inventory_data(self, material_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch inventory data from SAP.
        
        Args:
            material_id: Material identifier
        
        Returns:
            Inventory data dictionary or None if not found
        """
        try:
            url = f"{self.base_url}/sap/opu/odata/sap/ZINVENTORY_SRV/Inventory(MaterialId='{material_id}')"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            return response.json().get("d", {})
        except Exception as e:
            logger.error(f"Error fetching inventory data: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection to SAP system.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.base_url}/sap/opu/odata/sap/ZTEST_SRV/TestConnection"
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            logger.info("SAP connection test successful")
            return True
        except Exception as e:
            logger.error(f"SAP connection test failed: {e}")
            return False

# Global SAP integration instance (will be initialized with config)
sap_integration: Optional[SAPIntegration] = None

def initialize_sap_integration(config: SAPConfig) -> SAPIntegration:
    """
    Initialize SAP integration with configuration.
    
    Args:
        config: SAP configuration
    
    Returns:
        SAPIntegration instance
    """
    global sap_integration
    sap_integration = SAPIntegration(config)
    return sap_integration

def get_sap_integration() -> Optional[SAPIntegration]:
    """
    Get the global SAP integration instance.
    
    Returns:
        SAPIntegration instance or None if not initialized
    """
    return sap_integration
