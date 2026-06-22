"""
IRM OPC-UA Connector
====================
Модул за връзка с индустриални контролери (PLC) чрез OPC-UA протокол.
Позволява четене на данни в реално време и автоматична диагностика.
"""

import os
import asyncio
import json
import time
import requests
from asyncua import Client, ua
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Конфигурация от environment variables
OPC_UA_SERVER_URL = os.environ.get("OPC_UA_SERVER_URL", "opc.tcp://localhost:4840/freeopcua/server/")
API_URL = os.environ.get("API_URL", "http://localhost:8000") + "/diagnose"
# Списък с Node IDs за наблюдение (може да се конфигурира чрез environment variable)
NODES_TO_WATCH_STR = os.environ.get("OPC_UA_NODES_TO_WATCH", "ns=2;i=2,ns=2;i=3")
NODES_TO_WATCH = NODES_TO_WATCH_STR.split(",") if NODES_TO_WATCH_STR else [
    "ns=2;i=2", # Температура
    "ns=2;i=3", # Налягане
]

class IRM_OPCUA_Connector:
    def __init__(self, endpoint=OPC_UA_SERVER_URL):
        self.endpoint = endpoint
        self.client = Client(url=self.endpoint)
        self.running = True

    async def connect(self):
        """Свързване към OPC-UA сървъра."""
        try:
            await self.client.connect()
            print(f"✅ Свързан към OPC-UA сървър: {self.endpoint}")
            return True
        except Exception as e:
            print(f"❌ Грешка при свързване към OPC-UA: {e}")
            return False

    async def monitor_nodes(self):
        """Наблюдение на зададените нодове за промени."""
        while self.running:
            for node_id in NODES_TO_WATCH:
                try:
                    node = self.client.get_node(node_id)
                    value = await node.read_value()
                    browse_name = await node.read_browse_name()
                    
                    print(f"📊 {browse_name.Name}: {value}")
                    
                    # Примерна логика за аларма (напр. температура > 85)
                    if "Temp" in browse_name.Name and value > 85:
                        await self.send_to_irm(browse_name.Name, value)
                        
                except Exception as e:
                    print(f"⚠️ Грешка при четене на {node_id}: {e}")
            
            await asyncio.sleep(5) # Интервал на сканиране

    async def send_to_irm(self, name, value):
        """Изпращане на аномалия към IRM API за анализ."""
        print(f"🚨 Аномалия открита: {name} = {value}. Изпращане за анализ...")
        
        payload = {
            "prompt": f"Индустриален сензор {name} отчете критична стойност: {value}.",
            "context": f"Протокол: OPC-UA, Стойност: {value}, Праг: 85.0",
            "use_rag": True
        }
        
        try:
            # Използваме синхронно requests за простота в този пример, 
            # но в продукция е по-добре httpx (async)
            response = requests.post(API_URL, json=payload, timeout=10)
            if response.status_code == 200:
                analysis = response.json().get("analysis")
                print(f"🤖 IRM Анализ: {analysis}")
            else:
                print(f"❌ API Грешка: {response.status_code}")
        except Exception as e:
            print(f"❌ Неуспешна връзка с IRM API: {e}")

    async def run(self):
        if await self.connect():
            try:
                await self.monitor_nodes()
            except Exception as e:
                print(f"❌ Проблем по време на работа: {e}")
            finally:
                await self.client.disconnect()
                print("🔌 OPC-UA връзката е прекъсната.")

if __name__ == "__main__":
    connector = IRM_OPCUA_Connector()
    try:
        asyncio.run(connector.run())
    except KeyboardInterrupt:
        print("⏹️ Конекторът е спрян.")
