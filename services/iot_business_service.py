"""
IoT Service for ICAP Enterprise
===============================
Business logic for IoT data processing and fleet management.
"""

import logging
from services.iot_service import calculate_kpi, get_fleet_status as svc_fleet

logger = logging.getLogger("IoT_Service")

async def get_kpi_data():
    """Връща KPI данни от IoT сензори."""
    # Note: calculate_kpi expects audit_log_file path
    return calculate_kpi("AuditTrail/measurements_log.csv")

async def get_fleet_status():
    """Връща статуса на целия флот от устройства."""
    return svc_fleet()
