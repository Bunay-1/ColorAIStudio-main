"""
Синтетично генериране на индустриални данни за обучение
======================================================
Използва съществуващ модел (през Ollama), за да генерира нови двойки инструкция-отговор.
Това помага за "cold start", когато реалните данни са малко.
"""

import requests
import json
import argparse
import time
import random
from pathlib import Path
from rag_system import IRM_RAG

# Списък с индустриални теми (fallback ако RAG е празен)
TOPICS = [
    "Хидравлични системи и повреди",
    "SCADA системи и аларми",
    "Профилактика на електрически двигатели",
    "Вибрационен анализ на лагери"
]

def generate_from_rag(rag, model="llama3.1", count=5):
    """Генерира сценарии базирани на реални документи от RAG."""
    stats = rag.get_stats()
    if stats['total_chunks'] == 0:
        print("⚠️ RAG базата е празна. Използва се стандартно генериране по теми.")
        return None

    # Извличаме всички документи от базата
    all_docs = rag.collection.get(include=['documents', 'metadatas'])
    docs = all_docs['documents']
    metas = all_docs['metadatas']
    
    generated = []
    
    # Избираме случайни откъси
    sample_indices = random.sample(range(len(docs)), min(count, len(docs)))
    
    for idx in sample_indices:
        context = docs[idx]
        source = metas[idx]['source']
        
        print(f"📄 Генериране на казус въз основа на: {source}...")
        
        prompt = f"""
        Ти си експерт по индустриална поддръжка. 
        Въз основа на следния технически откъс от документация, генерирай 1 реалистичен казус на български език.
        
        ТЕХНИЧЕСКИ КОНТЕКСТ:
        ---
        {context}
        ---
        
        Казусът трябва да включва:
        1. instruction: Въпрос/Проблем от техник.
        2. input: Специфични параметри или данни от контекста.
        3. output: Техническо решение, базирано СТРИКТНО на предоставения контекст.

        Върни само чист JSON обект БЕЗ допълнителен текст, обяснения или Markdown форматиране.
        Формат: {{"instruction": "...", "input": "...", "output": "..."}}
        """
        
        try:
            url = "http://localhost:11434/api/generate"
            response = requests.post(url, json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                # Премахваме "format": "json" за тест, тъй като някои версии на Ollama дават 500 при грешен промпт
            }, timeout=120)
            
            if response.status_code == 200:
                res_text = response.json().get("response", "").strip()
                # Изчистваме евентуални Markdown блокове
                if "```json" in res_text:
                    res_text = res_text.split("```json")[1].split("```")[0].strip()
                elif "```" in res_text:
                    res_text = res_text.split("```")[1].split("```")[0].strip()
                
                case = json.loads(res_text)
                # Добавяме метаданни за проследимост
                case["source_doc"] = source
                generated.append(case)
            else:
                print(f"❌ Грешка от Ollama: {response.status_code}")
        except Exception as e:
            print(f"❌ Грешка при генериране: {e}")
            
    return generated

def generate_scenarios(topic, model="llama3.1", count=10):
    """Генерира сценарии за дадена тема."""
    prompt = f"""
    Ти си експерт по индустриална автоматизация и поддръжка.
    Генерирай {count} технически казуса за обучение на ИИ на български език.
    Всеки казус трябва да включва:
    1. Въпрос/Проблем от оператор (instruction)
    2. Допълнителен технически контекст (input) - параметри, кодове на грешки и т.н.
    3. Подробен технически анализ и решение (output)

    Формат: JSONL
    Пример за ред: {{"instruction": "...", "input": "...", "output": "..."}}
    Тема: {topic}
    """
    
    url = "http://localhost:11434/api/generate"
    try:
        response = requests.post(url, json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=120)
        
        if response.status_code == 200:
            # Опит за парсване на JSON отговора (моделите понякога връщат списък в полето 'response')
            data = response.json().get("response", "")
            return data
        else:
            print(f"❌ Грешка от Ollama: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Грешка при връзка с Ollama: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="llama3.1", help="Модел в Ollama за генериране")
    parser.add_argument("--count", type=int, default=10, help="Общ брой сценарии за генериране")
    parser.add_argument("--use_rag", type=bool, default=True, help="Използване на RAG документи")
    parser.add_argument("--output", type=str, default="./data/synthetic/generated.jsonl")
    args = parser.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_generated = []
    
    if args.use_rag:
        print("🔍 Инициализиране на RAG за синтетично генериране...")
        rag = IRM_RAG()
        rag_results = generate_from_rag(rag, args.model, args.count)
        if rag_results:
            all_generated.extend(rag_results)

    # Ако RAG е празен или не е използван, fallback към теми
    if not all_generated:
        print(f"🚀 Старт на стандартно синтетично генериране с модел {args.model}...")
        for topic in TOPICS:
            print(f"🔍 Генериране за тема: {topic}...")
            result = generate_scenarios(topic, args.model, max(1, args.count // len(TOPICS)))
            if result:
                try:
                    batch = json.loads(result)
                    if isinstance(batch, list):
                        all_generated.extend(batch)
                except:
                    for line in result.strip().split("\n"):
                        try:
                            all_generated.append(json.loads(line))
                        except: continue

    if all_generated:
        with open(out_path, "w", encoding="utf-8") as f:
            for rec in all_generated:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"✅ Успешно генерирани {len(all_generated)} записа в {out_path}")
    else:
        print("❌ Не бяха генерирани данни.")
        print("❌ Не бяха генерирани данни. Провери дали Ollama работи.")

if __name__ == "__main__":
    main()
