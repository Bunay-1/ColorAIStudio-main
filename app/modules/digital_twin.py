"""
Digital Twin Module — ICAP (Industrial Color AI Platform)
========================================================
Симулация на производствени процеси и прогнозиране на качеството.
Използва физични модели и исторически данни за "What-if" анализи.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("DigitalTwin")

class ProcessSimulator:
    def __init__(self):
        # Базови параметри на машината (Дигитален Двойник)
        self.machine_profile = {
            "pressure_optimal": 4.5, # bar
            "temp_optimal": 22.0,    # Celsius
            "humidity_optimal": 45.0, # %
            "wear_rate": 0.0001      # Износване на час
        }

    def simulate_color_shift(self,
                             base_lab: List[float],
                             env_params: Dict[str, float],
                             machine_params: Dict[str, float]) -> Dict[str, Any]:
        """
        Симулира как промените в средата и машината ще повлияят на крайния цвят.
        Връща прогнозиран Delta E и нови Lab координати.
        """
        L, a, b = base_lab

        # Физична симулация: Влажността влияе на наситеността (b), температурата на светлостта (L)
        temp_diff = env_params.get("temperature", 22.0) - self.machine_profile["temp_optimal"]
        hum_diff = env_params.get("humidity", 45.0) - self.machine_profile["humidity_optimal"]
        pres_diff = machine_params.get("pressure", 4.5) - self.machine_profile["pressure_optimal"]

        # Емпирични коефициенти (Digital Twin Logic)
        delta_L = temp_diff * 0.05 - pres_diff * 0.1
        delta_b = hum_diff * 0.08
        delta_a = temp_diff * 0.02

        predicted_lab = [L + delta_L, a + delta_a, b + delta_b]

        # Изчисляване на прогнозен Delta E (проста евклидова дистанция за симулацията)
        predicted_de = np.sqrt(delta_L**2 + delta_a**2 + delta_b**2)

        return {
            "predicted_lab": predicted_lab,
            "predicted_delta_e": float(predicted_de),
            "risk_level": "HIGH" if predicted_de > 1.0 else "LOW",
            "simulation_timestamp": datetime.now().isoformat(),
            "recommendation": self._generate_sim_recommendation(predicted_de, env_params)
        }

    def _generate_sim_recommendation(self, de: float, env: Dict[str, float]) -> str:
        if de <= 0.5:
            return "Процесът е стабилен. Не се изискват корекции."

        recs = []
        if env.get("humidity", 45) > 60:
            recs.append("Намалете скоростта на подаване поради висока влажност.")
        if de > 1.0:
            recs.append("ВНИМАНИЕ: Прогнозираното отклонение е критично. Проверете охладителната система.")

        return " ".join(recs) if recs else "Препоръчва се фино регулиране на налягането."

class DigitalTwinService:
    """Интерфейс за оркестрация на симулациите."""
    def __init__(self, color_engine=None):
        self.simulator = ProcessSimulator()
        self.color_engine = color_engine

    async def run_what_if_analysis(self,
                                 current_state: Dict[str, Any],
                                 target_scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Изпълнява множество симулации за различни сценарии."""
        results = []
        base_lab = current_state.get("base_lab", [50.0, 0.0, 0.0])

        for scenario in target_scenarios:
            sim_res = self.simulator.simulate_color_shift(
                base_lab,
                scenario.get("env", {}),
                scenario.get("machine", {})
            )
            sim_res["scenario_name"] = scenario.get("name", "Unknown")
            results.append(sim_res)

        return results
