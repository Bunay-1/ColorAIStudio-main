"""
IoT Service for ICAP Enterprise
===============================
Business logic for IoT data processing and fleet management.
"""

import logging
from services.iot_service import get_kpi_data as svc_kpi, api_get_fleet_status as svc_fleet

logger = logging.getLogger("IoT_Service")

async def get_kpi_data():
    """Връща KPI данни от IoT сензори."""
    return svc_kpi()

async def get_fleet_status():
    """Връща статуса на целия флот от устройства."""
    return svc_fleet()
