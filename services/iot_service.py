import time
import pandas as pd
import os
import logging
import json

logger = logging.getLogger("IOT_Service")

# Симулация на персистентно състояние за IoT
_latest_iot_data = {
    "Machine_P3": {"status": "Warning", "load": "85%", "temp": "92.4°C", "timestamp": time.time()},
    "Mixer_01": {"status": "OK", "load": "42%", "temp": "45.1°C", "timestamp": time.time()}
}

def get_latest_iot_data():
    return _latest_iot_data

def update_iot_data(sensor_id, data):
    payload = {
        "status": data.get("status", "OK"),
        "load": data.get("load", "0%"),
        "temp": f"{data.get('value', 0)}°C",
        "timestamp": time.time()
    }
    _latest_iot_data[sensor_id] = payload
    return payload

def calculate_kpi(audit_log_file):
    try:
        if not os.path.exists(audit_log_file):
            return default_kpis()

        df = pd.read_csv(audit_log_file)
        if df.empty:
            return default_kpis()

        total_count = len(df)
        pass_count = len(df[df['status'] == 'Pass'])
        scrap_rate = round(((total_count - pass_count) / total_count * 100), 2) if total_count > 0 else 0.0

        # Симулирано OEE базирано на качеството
        quality_score = (pass_count / total_count * 100) if total_count > 0 else 100.0
        oee = round(0.92 * 0.95 * (quality_score/100) * 100, 1) # A * P * Q

        return {
            "OEE": oee,
            "Scrap_Rate": scrap_rate,
            "Defect_Rate": round(100 - quality_score, 2),
            "MTBF": "520h",
            "Color_Stability_Index": 0.96,
            "Availability": 92.0,
            "Performance": 95.0,
            "Quality": round(quality_score, 1),
            "rag_indexing": 88,
            "kg_density": 65,
            "vision_reliability": 94,
            "agent_autonomy": 45
        }
    except Exception as e:
        logger.error(f"KPI calculation error: {e}")
        return default_kpis()

def default_kpis():
    return {
        "OEE": 0.0, "Scrap_Rate": 0.0, "Defect_Rate": 0.0, "MTBF": "N/A",
        "Color_Stability_Index": 0, "Availability": 0, "Performance": 0, "Quality": 0
    }

def get_fleet_status():
    """Edge Fleet Management. Връща статус на отдалечените устройства от флот регистър."""
    fleet_file = "fleet_registry.json"
    if os.path.exists(fleet_file):
        try:
            with open(fleet_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading fleet registry: {e}")

    # Fallback към дефиниран списък, ако файлът липсва
    return [
        {
            "id": "JETSON-NODE-01",
            "status": "Online",
            "load": "45%",
            "temp": "52°C",
            "model_version": "v8.4.3",
            "uptime": "120h"
        },
        {
            "id": "JETSON-NODE-02",
            "status": "Online",
            "load": "12%",
            "temp": "40°C",
            "model_version": "v8.4.3",
            "uptime": "240h"
        }
    ]
