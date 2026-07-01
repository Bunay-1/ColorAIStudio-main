"""
Система за оценка (Evaluation) на Industrial Reasoning Model
===========================================================
Проверява точността на модела срещу набор от технически въпроси.
"""

import requests
import json
import argparse
import pandas as pd
from tqdm import tqdm

# Базов набор от въпроси за тестване на индустриално мислене
TEST_BENCHMARK = [
    {
        "instruction": "Диагностицирай проблем с хидравлична машина.",
        "input": "Машината издава висок свистящ звук, налягането е нестабилно (флуктуира между 40 и 120 bar).",
        "expected": "Кавитация или засмукване на въздух в смукателната линия."
    },
    {
        "instruction": "Анализирай SCADA аларма.",
        "input": "Error Code: E-402 (Overcurrent) на инвертор на конвейерна лента.",
        "expected": "Механично засядане на лентата или претоварване на двигателя."
    },
    {
        "instruction": "Преведи технически термин.",
        "input": "Preventive maintenance",
        "expected": "Профилактична поддръжка"
    }
]

def ask_ollama(prompt, model, url):
    try:
        response = requests.post(f"{url}/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }, timeout=60)
        return response.json().get("response", "")
    except Exception as e:
        return f"Грешка: {e}"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="irm-industrial", help="Име на модела в Ollama")
    parser.add_argument("--url", type=str, default="http://localhost:11434", help="Ollama API URL")
    parser.add_argument("--output", type=str, default="evaluation_results.csv")
    args = parser.parse_args()

    results = []
    print(f"🧪 Тестване на модел: {args.model}...")

    for test in tqdm(TEST_BENCHMARK):
        prompt = f"### Instruction:\n{test['instruction']}\n\n### Input:\n{test['input']}\n\n### Response:\n"
        response = ask_ollama(prompt, args.model, args.url)
        
        results.append({
            "Instruction": test['instruction'],
            "Input": test['input'],
            "Expected": test['expected'],
            "Model Output": response
        })

    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False, encoding="utf-8-sig")
    print(f"✅ Оценката завърши. Резултатите са записани в: {args.output}")

if __name__ == "__main__":
    main()
