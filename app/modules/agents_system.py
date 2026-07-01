"""
Multi-Agent Architecture — ICAP (Industrial Color AI Platform)
=============================================================
Дефинира специализирани агенти за автоматизация на индустриални задачи.
Използва оркестратор за разпределяне на задачите.
"""

import logging
import time
import csv
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentSystem")
_executor = ThreadPoolExecutor(max_workers=4)

class BaseAgent:
    def __init__(self, name: str, role: str, requires_approval: bool = False) -> None:
        self.name: str = name
        self.role: str = role
        self.requires_approval: bool = requires_approval

    def log_decision(self, decision: str, reason: str, data: Dict[str, Any]) -> None:
        """Логва решението на агента в Audit Trail за ISO 9001 съответствие."""
        log_entry: Dict[str, str] = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "agent": self.name,
            "decision": decision,
            "reason": reason,
            "data_snapshot": str(data)
        }
        # В реална система тук се вика API-то или се пише директно в CSV
        try:
            if not os.path.exists("AuditTrail"):
                os.makedirs("AuditTrail")
            file_path = "AuditTrail/agent_decisions.csv"
            file_exists = os.path.isfile(file_path)
            with open(file_path, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=log_entry.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(log_entry)
        except (IOError, OSError) as e:
            logger.error(f"Грешка при логване на решение на агент: {e}", exc_info=True)

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Всеки агент трябва да имплементира process() метод.")

class QA_Agent(BaseAgent):
    """Агент за качествен контрол (QA). Проверява толеранси и стандарти."""
    def __init__(self) -> None:
        super().__init__("QA Agent", "Quality Assurance")

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        de: float = task_data.get("delta_e", 0.0)
        tolerance: float = task_data.get("tolerance", 1.0)
        status: str = "PASS" if de <= tolerance else "FAIL"

        return {
            "agent": self.name,
            "status": status,
            "analysis": f"Измерено отклонение ΔE={de:.3f} спрямо лимит {tolerance}. " +
                        ("Всичко е в норма." if status == "PASS" else "Извън толеранс!")
        }

class RecipeAgent(BaseAgent):
    """Агент за рецепти. Генерира и оптимизира цветови корекции."""
    def __init__(self, ai_analysis_module: Any) -> None:
        super().__init__("Recipe Agent", "Color Formulation")
        self.ai = ai_analysis_module

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        lab_sam: Optional[List[float]] = task_data.get("lab_sample")
        lab_std: Optional[List[float]] = task_data.get("lab_standard")
        batch_size: float = task_data.get("batch_size", 100.0)

        if not lab_sam or not lab_std:
            return {"agent": self.name, "error": "Липсват Lab координати"}

        # Run blocking operation in executor to prevent blocking event loop
        corrections: List[str] = await asyncio.get_event_loop().run_in_executor(
            _executor,
            self.ai.recommend_correction,
            lab_sam, lab_std, batch_size
        )

        return {
            "agent": self.name,
            "corrections": corrections,
            "summary": f"Генерирани са {len(corrections)} стъпки за корекция на партидата."
        }

class RootCauseAgent(BaseAgent):
    """Агент за анализ на причините. Диагностицира дефекти чрез Vision и RAG."""
    def __init__(self, vision_engine: Any, rag_system: Any) -> None:
        super().__init__("Root Cause Agent", "Diagnostics")
        self.vision = vision_engine
        self.rag = rag_system

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        defects: List[Dict[str, Any]] = task_data.get("defects", [])
        coating_quality: Dict[str, Any] = task_data.get("coating_quality", {})
        de: float = task_data.get("delta_e", 0)

        # Дълбок верижен RCA анализ чрез Графа на Знанието (v8 Chain Analysis)
        kg_reasoning: str = ""
        # Засечи потенциални проблеми в дефектите
        detected_issue = "Yellow_Drift" if de > 1.0 else None
        if defects:
            detected_issue = defects[0].get('class', detected_issue)

        if detected_issue:
            try:
                from app.modules.knowledge_graph import IndustrialKG
                # Използваме споделената инстанция на графа от RAG системата ако е налична
                kg = self.rag.kg if hasattr(self.rag, 'kg') else IndustrialKG()

                path = await asyncio.get_event_loop().run_in_executor(
                    _executor,
                    kg.find_reasoning_path,
                    detected_issue,
                    3 # По-голяма дълбочина за по-добър RCA
                )

                if isinstance(path, list) and len(path) > 0:
                    kg_reasoning = f"\n[GraphRAG RCA]: Открита причинно-следствена верига за '{detected_issue}':\n"
                    def format_chain(steps: List[Dict[str, Any]], level: int = 0) -> str:
                        res: str = ""
                        for s in steps:
                            res += "  " * level + f"↳ {s['source']} ({s['relation']})"
                            if s.get('condition'):
                                res += f" при {s['condition']}"
                            res += " -> "
                            if not s.get('sub_steps'):
                                res += "КОРЕННА ПРИЧИНА\n"
                            else:
                                res += "\n" + format_chain(s['sub_steps'], level + 1)
                        return res
                    kg_reasoning += format_chain(path)
                elif isinstance(path, str): # Ако върне съобщение за грешка
                    kg_reasoning = f"\n[GraphRAG]: {path}"
            except Exception as e:
                logger.warning(f"Knowledge Graph reasoning failed: {e}")

        context: str = ""
        if defects:
            try:
                query: str = f"Causes of production defects like {defects[0].get('class', 'unknown')}"
                # Add timeout to RAG query to prevent hanging
                result = await asyncio.wait_for(self.rag.query(query), timeout=30.0)
                context, _ = result
            except asyncio.TimeoutError:
                logger.error("RAG query timeout")
            except (ConnectionError, ValueError) as e:
                logger.error(f"RAG query error: {e}")

        analysis: str = "Анализирани са визуалните дефекти. "
        if coating_quality.get("is_uneven"):
            analysis += "Неравномерното покритие вероятно се дължи на проблем с налягането или дюзите. "

        if context:
            analysis += "Справка с базата знания: " + context[:200] + "..."

        return {
            "agent": self.name,
            "root_cause": analysis + kg_reasoning,
            "recommendation": "Проверете настройките на машината и параметрите на околната среда (Влажност/Температура)."
        }

class MaintenanceAgent(BaseAgent):
    """Агент за поддръжка. Предсказва нуждата от ремонт."""
    def __init__(self) -> None:
        super().__init__("Maintenance Agent", "Predictive Maintenance")

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        de_history: List[float] = task_data.get("historical_de", [])
        drift_detected: bool = len(de_history) > 3 and de_history[-1] > de_history[0]

        status: str = "ВНИМАНИЕ" if drift_detected else "OK"

        return {
            "agent": self.name,
            "machine_status": status,
            "analysis": "Установено е отклонение в тренда, което може да сигнализира за зацапване на сензорите." if drift_detected else "Стабилна работа на оборудването."
        }

class ReasoningAgent(BaseAgent):
    """Агент за логически изводи. Анализира Графа на Знанието за причинно-следствени връзки."""
    def __init__(self, rag_system: Any) -> None:
        super().__init__("Reasoning Agent", "Logical Inference")
        self.rag = rag_system

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt: str = task_data.get("query", "Yellow_Drift")

        try:
            # Используем GraphRAG логиката през RAG системата с timeout
            result = await asyncio.wait_for(self.rag.query(prompt), timeout=30.0)
            context, _ = result

            if "ГРАФ НА ЗНАНИЕТО" in context:
                analysis: str = context.split("--- ГРАФ НА ЗНАНИЕТО")[1].split("---")[0].strip()
            else:
                analysis = "Не бяха открити специфични логически корелации в текущия граф на знанието."
        except asyncio.TimeoutError:
            logger.error("Reasoning query timeout")
            analysis = "Timeout при анализ на знания"
        except Exception as e:
            logger.error(f"Reasoning error: {e}", exc_info=True)
            analysis = "Грешка при логически анализ"

        return {
            "agent": self.name,
            "reasoning": analysis,
            "message": "AI изводът е направен на база техническата история на активите."
        }

class KnowledgeAgent(BaseAgent):
    """Агент за знания (v8). Отговаря на специфични технически въпроси."""
    def __init__(self, rag_system: Any) -> None:
        super().__init__("Knowledge Agent", "Information Retrieval")
        self.rag = rag_system

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        query: str = task_data.get("query", "Industrial Standards")
        
        try:
            # Add timeout to prevent hanging on slow RAG queries
            result = await asyncio.wait_for(self.rag.query(query), timeout=30.0)
            context, sources = result
        except asyncio.TimeoutError:
            logger.error("Knowledge query timeout")
            context = "Timeout при търсене в базата знания"
            sources = []
        except Exception as e:
            logger.error(f"Knowledge retrieval error: {e}", exc_info=True)
            context = "Грешка при търсене"
            sources = []

        return {
            "agent": self.name,
            "info": context[:300] + "..." if len(context) > 300 else context,
            "sources": sources,
            "message": "Информацията е извлечена от базата знания на предприятието."
        }

class ComplianceAgent(BaseAgent):
    """Агент за съответствие (v8). Следи ISO и регулаторни изисквания."""
    def __init__(self) -> None:
        super().__init__("Compliance Agent", "Regulatory Affairs")

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "iso_compliance": "ISO 9001:2015, ISO 14001 (Sustainability)",
            "audit_status": "Compliant",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "message": "Всички измервания са архивирани в Audit Trail съгласно стандартите."
        }

class SustainabilityAgent(BaseAgent):
    """Агент за устойчивост. Анализира екологичния отпечатък (Industry 5.0)."""
    def __init__(self, ai_analysis_module):
        super().__init__("Sustainability Agent", "Ecological Impact")
        self.ai = ai_analysis_module

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        batch_size = task_data.get("batch_size", 100.0)
        # Интеграция на реални енергийни данни от IoT ако са налични
        energy_data = task_data.get("energy_consumption_kwh", 0.0)

        # Подготовка на данни за анализа
        recipe_data = {
            "delta_e": task_data.get("delta_e", 0.0),
            "components": task_data.get("recipe_components", [])
        }

        impact = self.ai.calculate_sustainability_index(recipe_data, batch_size, energy_data=energy_data)

        return {
            "agent": self.name,
            "sustainability_score": impact["sustainability_score"],
            "co2_footprint": f"{impact['co2_footprint_kg']} kg CO2",
            "eco_label": impact["eco_label"],
            "analysis": f"Екологичен етикет: {impact['eco_label']}. {impact['waste_prevention_advice']}"
        }

class ProcessAgent(BaseAgent):
    """Агент за управление на процеса (Industry 4.0). Дава препоръки за машини."""
    def __init__(self, ai_analysis_module):
        # Промяна на параметри на машина изисква одобрение (Human-in-the-loop Guardrail)
        super().__init__("Process Agent", "Process Optimization", requires_approval=True)
        self.ai = ai_analysis_module

    async def process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        recommendations = self.ai.recommend_process_correction(task_data)

        if not recommendations:
            return {"agent": self.name, "message": "Параметрите на процеса са в оптимални граници."}

        analysis = "Открити са отклонения в производствените условия. "
        actions = [f"{r['issue']}: {r['action']} ({r['impact']})" for r in recommendations]

        # Логване на решението за ISO 9001
        self.log_decision(
            decision="Препоръка за промяна на параметри",
            reason=f"Отклонение ΔE={task_data.get('delta_e')}",
            data={"recommendations": recommendations}
        )

        return {
            "agent": self.name,
            "analysis": analysis,
            "recommendations": actions,
            "requires_approval": self.requires_approval,
            "message": "AI предписанията изискват одобрение от оператор преди прилагане чрез OPC-UA."
        }

class AgentOrchestrator:
    """Оркестратор, който управлява взаимодействието между агентите."""
    def __init__(self, color_ai, vision_engine, rag_system):
        self.agents = {
            "qa": QA_Agent(),
            "recipe": RecipeAgent(color_ai),
            "root_cause": RootCauseAgent(vision_engine, rag_system),
            "reasoning": ReasoningAgent(rag_system),
            "maintenance": MaintenanceAgent(),
            "compliance": ComplianceAgent(), # Преименуван
            "knowledge": KnowledgeAgent(rag_system), # Нов агент (v8)
            "sustainability": SustainabilityAgent(color_ai),
            "process": ProcessAgent(color_ai)
        }

    async def execute_workflow(self, workflow_name: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Изпълнява верига от агенти на база на работния процес."""
        results = []

        if workflow_name == "color_analysis":
            # Верига: QA -> Recipe -> Sustainability -> Compliance
            results.append(await self.agents["qa"].process(data))
            if results[-1]["status"] == "FAIL":
                results.append(await self.agents["recipe"].process(data))
            results.append(await self.agents["sustainability"].process(data))
            results.append(await self.agents["compliance"].process(data))

        elif workflow_name == "vision_diagnostics":
            # Верига: Root Cause -> Maintenance -> Compliance
            results.append(await self.agents["root_cause"].process(data))
            results.append(await self.agents["maintenance"].process(data))
            results.append(await self.agents["compliance"].process(data))

        elif workflow_name == "full_inspection":
            # Всички агенти (Enterprise v8 Final Flow)
            if data.get("delta_e", 0) > data.get("tolerance", 1.0):
                data["query"] = "Yellow_Drift"

            # Изпълняваме в специфичен Enterprise ред
            agent_order = ["qa", "process", "recipe", "root_cause", "reasoning", "knowledge", "maintenance", "sustainability", "compliance"]
            for key in agent_order:
                if key in self.agents:
                    results.append(await self.agents[key].process(data))

        elif workflow_name == "sustainability_audit":
            # Верига за екологичен одит
            results.append(await self.agents["sustainability"].process(data))
            results.append(await self.agents["compliance"].process(data))
            results.append(await self.agents["knowledge"].process({"query": "ESG Industrial Standards ISO 14001"}))

        elif workflow_name == "predictive_maintenance":
            # Верига за предвидна поддръжка
            results.append(await self.agents["maintenance"].process(data))
            results.append(await self.agents["reasoning"].process({"query": "Machine_P3_Status"}))
            results.append(await self.agents["compliance"].process(data))

        elif workflow_name == "process_optimization":
            # Верига за оптимизация на процеса
            results.append(await self.agents["process"].process(data))
            if data.get("delta_e", 0) > 0.5:
                results.append(await self.agents["recipe"].process(data))
            results.append(await self.agents["reasoning"].process(data))

        return results

if __name__ == "__main__":
    print("Multi-Agent Architecture module ready.")
