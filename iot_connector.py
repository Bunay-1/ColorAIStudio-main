"""
IRM IoT Connector — MQTT Client
===============================
Клиент за приемане на данни от сензори в реално време.
Интегрира се с IRM API за автоматичен анализ на аномалии.
"""

import os
import paho.mqtt.client as mqtt
import json
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Конфигурация от environment variables
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "factory/sensors/#")
API_URL = os.environ.get("API_URL", "http://localhost:8000") + "/diagnose"

class IRM_IoT_Connector:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.sensor_data = {}
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # seconds
        self.connected = False

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Свързан към MQTT Broker: {MQTT_BROKER}")
            self.client.subscribe(MQTT_TOPIC)
            self.reconnect_attempts = 0
            self.connected = True
        else:
            print(f"❌ Грешка при свързване: {rc}")
            self.connected = False

    def on_disconnect(self, client, userdata, rc):
        print(f"⚠️ MQTT Disconnect detected. RC: {rc}")
        self.connected = False
        if rc != 0:
            print("🔄 Attempting to reconnect...")
            self.reconnect()

    def reconnect(self):
        """MQTT reconnection logic with exponential backoff."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print(f"❌ Max reconnection attempts ({self.max_reconnect_attempts}) reached. Giving up.")
            return

        delay = min(self.reconnect_delay * (2 ** self.reconnect_attempts), 60)  # Max 60 seconds
        print(f"⏳ Reconnecting in {delay} seconds... (Attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
        
        time.sleep(delay)
        self.reconnect_attempts += 1
        
        try:
            self.client.reconnect()
        except Exception as e:
            print(f"❌ Reconnection failed: {e}")
            self.reconnect()

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            print(f"📥 Данни от {topic}: {payload}")
            
            # Запазваме последните данни
            self.sensor_data[topic] = {
                "value": payload.get("value"),
                "unit": payload.get("unit"),
                "timestamp": time.time()
            }
            
            # Проверка за критични стойности (примерна логика)
            if payload.get("status") == "CRITICAL":
                self.analyze_anomaly(topic, payload)
                
        except Exception as e:
            print(f"⚠️ Грешка при обработка на съобщение: {e}")

    def analyze_anomaly(self, sensor, data):
        """Изпраща критични данни към IRM API за анализ."""
        print(f"🚨 Анализиране на аномалия за {sensor}...")
        
        prompt = f"Сензор {sensor} отчете критична стойност: {data.get('value')} {data.get('unit')}."
        context = f"Пълни данни от сензора: {json.dumps(data)}"
        
        try:
            response = requests.post(API_URL, json={
                "prompt": prompt,
                "context": context
            })
            if response.status_code == 200:
                analysis = response.json().get("analysis")
                print(f"🤖 IRM Анализ: {analysis}")
            else:
                print(f"❌ API Грешка: {response.status_code}")
        except Exception as e:
            print(f"❌ Неуспешна връзка с IRM API: {e}")

    def run(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("⏹️ IoT Connector спрян.")
        except Exception as e:
            print(f"❌ Грешка: {e}")

if __name__ == "__main__":
    # Стартиране: python iot_connector.py
    # За тест може да използвате: mosquitto_pub -t "factory/sensors/temp" -m '{"value": 98, "unit": "°C", "status": "CRITICAL"}'
    connector = IRM_IoT_Connector()
    connector.run()
