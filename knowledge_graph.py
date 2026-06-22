"""
Knowledge Graph Core — Industrial Color AI Platform (ICAP)
========================================================
Модул за изграждане и обхождане на индустриален граф на знанието.
Свързва документация, машини и исторически събития.
"""

import networkx as nx
import json
import logging
import os
import asyncio
import requests
import time
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KnowledgeGraph")

class IndustrialKG:
    def __init__(self, storage_path="Docs/knowledge_graph.json"):
        self.storage_path = storage_path
        self.graph = nx.DiGraph()
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Възстановяване на графа от JSON (node-link format)
                    from networkx.readwrite import json_graph
                    # Изрично задаваме имената на полетата за съвместимост с по-нови версии на NetworkX
                    self.graph = json_graph.node_link_graph(data, nodes="nodes", edges="links")
                logger.info(f"Графът на знанието е зареден: {len(self.graph.nodes)} възела.")
            except Exception as e:
                logger.error(f"Грешка при зареждане на графа: {e}")
                self._build_default_ontology()
        else:
            self._build_default_ontology()

    def _build_default_ontology(self):
        """Изгражда базова индустриална онтология ако няма съществуваща."""
        logger.info("Изграждане на базова онтология...")

        # Машини и компоненти
        self.graph.add_node("Machine_P3", type="Machine", label="Машина №3", usage_hours=520)
        self.graph.add_node("Mixer_01", type="Machine", label="Миксер Основен")

        # Параметри и проблеми
        self.graph.add_node("Yellow_Drift", type="Issue", label="Отклонение в жълтия спектър")
        self.graph.add_node("Maintenance_Interval", type="Rule", label="Лимит 500 часа")

        # Връзки
        self.graph.add_edge("Machine_P3", "Mixer_01", relation="FEEDS")
        self.graph.add_edge("Machine_P3", "Yellow_Drift", relation="CAUSES", condition="usage > 500h")
        self.graph.add_edge("Yellow_Drift", "Maintenance_Interval", relation="TRIGGERED_BY")

        # Enterprise RCA Hierarchies (v8)
        self.graph.add_node("Operator_Shift_A", type="Person", label="Смяна А")
        self.graph.add_node("Batch_4421", type="Production", label="Партида #4421")
        self.graph.add_node("High_Humidity", type="Environment", label="Висока Влажност > 70%")

        self.graph.add_edge("Batch_4421", "Yellow_Drift", relation="AFFECTED_BY")
        self.graph.add_edge("Operator_Shift_A", "Batch_4421", relation="PRODUCED")
        self.graph.add_edge("High_Humidity", "Yellow_Drift", relation="ROOT_CAUSE", confidence=0.92)

        self.save()

    def save(self):
        try:
            from networkx.readwrite import json_graph
            # Изрично задаваме имената на полетата за съвместимост с по-нови версии на NetworkX
            data = json_graph.node_link_data(self.graph, nodes="nodes", edges="links")
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Грешка при запис на графа: {e}")

    def add_event(self, machine_id, issue_id, relation="PREDICTED", metadata=None):
        """Добавя ново събитие към графа с времево клеймо."""
        if machine_id in self.graph.nodes and issue_id in self.graph.nodes:
            params = {"relation": relation, "timestamp": time.time()}
            if metadata:
                params.update(metadata)
            self.graph.add_edge(machine_id, issue_id, **params)
            self.save()

    async def extract_entities_and_relations(self, text: str, ollama_url: str, model: str):
        """
        Извлича ентитети и връзки от текст чрез LLM (Ollama).
        Използва асинхронен httpx клиент, за да не блокира главната нишка.
        """
        prompt = f"""
        Analyze the following industrial text and extract entities and their relationships.
        Use only these entity types: Machine, Material, Issue, Sensor, Production, Person.
        Return the result ONLY as a JSON list of triplets: [["entity1", "relation", "entity2", "type1", "type2"], ...]

        Text: {text[:2000]}
        """

        timeout = float(os.environ.get("OLLAMA_TIMEOUT", "180.0"))
        try:
            import httpx
            from utils.circuit_breaker import ollama_breaker
            
            async def _call_ollama():
                async with httpx.AsyncClient(timeout=timeout) as client:
                    payload = {
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                    response = await client.post(ollama_url, json=payload)
                if response.status_code != 200:
                    raise Exception(f"Ollama returned status {response.status_code}")
                return response.json()

            result = await ollama_breaker.call_async(_call_ollama)
            
            triplets = json.loads(result.get("response", "[]"))
            for t in triplets:
                if len(t) >= 3:
                    e1, rel, e2 = t[0], t[1], t[2]
                    t1 = t[3] if len(t) > 3 else "Unknown"
                    t2 = t[4] if len(t) > 4 else "Unknown"

                    # Entity Resolution: Simple normalization
                    e1, e2 = e1.strip(), e2.strip()

                    self.graph.add_node(e1, type=t1, label=e1)
                    self.graph.add_node(e2, type=t2, label=e2)
                    self.graph.add_edge(e1, e2, relation=rel)

            self.save()
            return len(triplets)
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
        return 0

    def get_communities(self):
        """Групира графа в клъстери (communities) чрез алгоритъм на Louvain."""
        try:
            from networkx.algorithms import community
            # Louvain изисква ненасочен граф
            undirected = self.graph.to_undirected()
            communities = list(community.louvain_communities(undirected))
            return communities
        except Exception as e:
            logger.error(f"Community detection error: {e}")
            return []

    def get_related_entities(self, entity_name: str, depth: int = 1):
        """Намира свързани ентитети на определена дълбочина."""
        if entity_name not in self.graph:
            return []

        related = set()
        current_layer = {entity_name}

        for _ in range(depth):
            next_layer = set()
            for node in current_layer:
                neighbors = set(self.graph.neighbors(node)) | set(self.graph.predecessors(node))
                next_layer.update(neighbors)
            related.update(next_layer)
            current_layer = next_layer

        related.discard(entity_name)
        return list(related)

    def search_entities_in_text(self, text: str):
        """Проста проверка за съществуващи в графа ентитети в текста."""
        found = []
        text_lower = text.lower()
        for node in self.graph.nodes:
            if node.lower() in text_lower:
                found.append(node)
        return found

    def get_temporal_evolution(self, entity_label):
        """Показва как са се променяли връзките на даден обект във времето."""
        target_node = None
        for node, data in self.graph.nodes(data=True):
            if data.get("label") == entity_label or node == entity_label:
                target_node = node
                break

        if not target_node: return []

        evolution = []
        # Проверяваме входящи и изходящи ребра
        for u, v, data in self.graph.in_edges(target_node, data=True):
            evolution.append({
                "source": u, "target": v, "relation": data.get("relation"),
                "timestamp": data.get("timestamp", 0), "type": "incoming"
            })
        for u, v, data in self.graph.out_edges(target_node, data=True):
            evolution.append({
                "source": u, "target": v, "relation": data.get("relation"),
                "timestamp": data.get("timestamp", 0), "type": "outgoing"
            })

        return sorted(evolution, key=lambda x: x['timestamp'])

    def find_reasoning_path(self, issue_label, depth=3):
        """
        Търси верижен логически път за даден проблем (Chain RCA).
        Обхожда графа назад до определена дълбочина.
        """
        target_node = None
        for node, data in self.graph.nodes(data=True):
            if data.get("label") == issue_label or node == issue_label:
                target_node = node
                break

        if not target_node:
            return "Не бе открита логическа връзка в графа за: " + str(issue_label)

        def get_predecessors_recursive(current_node, current_depth):
            if current_depth <= 0:
                return []

            chain = []
            for pred in self.graph.predecessors(current_node):
                edge_data = self.graph.get_edge_data(pred, current_node)
                pred_data = self.graph.nodes[pred]

                step = {
                    "source": pred_data.get("label", pred),
                    "relation": edge_data.get("relation"),
                    "condition": edge_data.get("condition", ""),
                    "type": pred_data.get("type", "Unknown"),
                    "confidence": edge_data.get("confidence", 1.0),
                    "sub_steps": get_predecessors_recursive(pred, current_depth - 1)
                }
                chain.append(step)
            return chain

        return get_predecessors_recursive(target_node, depth)

if __name__ == "__main__":
    kg = IndustrialKG()
    print("Industrial Knowledge Graph Core Ready.")
    path = kg.find_reasoning_path("Yellow_Drift")
    print(f"Примерно разсъждение: {path}")
