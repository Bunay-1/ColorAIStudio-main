from fastapi import APIRouter, Request
from services.iot_service import get_latest_iot_data, update_iot_data, calculate_kpi, get_fleet_status
import os

router = APIRouter(prefix="/iot", tags=["Industrial IoT"])

AUDIT_LOG_FILE = os.environ.get("AUDIT_LOG_PATH", "AuditTrail/measurements_log.csv")

@router.get("/data")
async def get_iot_data():
    return get_latest_iot_data()

@router.get("/kpi")
async def get_kpi_data():
    return calculate_kpi(AUDIT_LOG_FILE)

@router.get("/fleet")
async def api_get_fleet_status():
    return get_fleet_status()

@router.post("/update")
async def update_iot(data: dict, req: Request):
    sensor_id = data.get("sensor_id", "Unknown")
    payload = update_iot_data(sensor_id, data)
    await req.app.state.manager.broadcast({
        "type": "iot_update",
        "sensor_id": sensor_id,
        "data": payload
    })
    return {"message": "Data updated"}
