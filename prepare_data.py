"""
Подготовка на данни за fine-tuning на Industrial Reasoning Model
================================================================
Конвертира JSON, JSONL, TMX, CSV, XLSX, DOCX и PDF файлове в instruction формат.
"""

import os
import json
import argparse
import re
import time
import zipfile
import shutil
import itertools
from pathlib import Path
from tqdm import tqdm

# ── pip зависимости ───────────────────────────────────────────────────────────
try:
    import pandas as pd
    from datasets import Dataset
    from lxml import etree
    from pypdf import PdfReader
    from docx import Document
except ImportError:
    raise SystemExit(
        "Инсталирай зависимостите:\n"
        "  pip install datasets pandas lxml tqdm pypdf python-docx openpyxl"
    )

# ═════════════════════════════════════════════════════════════════════════════
# ЧЕТЕНЕ НА РАЗЛИЧНИ ФОРМАТИ
# ═════════════════════════════════════════════════════════════════════════════

def load_jsonl(path: Path) -> list[dict]:
    records = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line: continue
            try:
                obj = json.loads(line)
                records.append(obj)
            except json.JSONDecodeError:
                continue
    return records

def load_json(path: Path) -> list[dict]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    except:
        return []

def json_to_instructions(records: list[dict]) -> list[dict]:
    result = []
    for rec in records:
        if "instruction" in rec and "output" in rec:
            result.append({
                "instruction": str(rec.get("instruction", "")).strip(),
                "input":       str(rec.get("input", "")).strip(),
                "output":      str(rec.get("output", "")).strip(),
            })
        elif "text" in rec:
            result.append({
                "instruction": "Анализирай следните данни за цветове:",
                "input":       str(rec["text"]).strip(),
                "output":      "",
            })
        else:
            flat = " | ".join(f"{k}: {v}" for k, v in rec.items() if isinstance(v, (str, int, float)))
            if flat:
                result.append({
                    "instruction": "Обясни следните данни:",
                    "input":       flat,
                    "output":      "",
                })
    return result

def load_csv_xlsx(path: Path) -> list[dict]:
    try:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)

        records = []
        cols = [c.lower() for c in df.columns]
        
        for _, row in df.iterrows():
            instruction, inp, output = "", "", ""
            
            # Конвертиране на всички колони в низове за избягване на атрибутни грешки
            row_data = {str(k).lower(): str(v) for k, v in row.items()}

            if "instruction" in cols: instruction = row[df.columns[cols.index("instruction")]]
            elif "question" in cols: instruction = row[df.columns[cols.index("question")]]
            
            if "input" in cols: inp = row[df.columns[cols.index("input")]]
            elif "context" in cols: inp = row[df.columns[cols.index("context")]]
            
            if "output" in cols: output = row[df.columns[cols.index("output")]]
            elif "answer" in cols: output = row[df.columns[cols.index("answer")]]
            
            if not instruction and not output:
                # Ако няма стандартни колони, правим целия ред на input
                inp = " | ".join([f"{col}: {val}" for col, val in row.items()])
                instruction = "Анализирай данните за цветове:"

            records.append({"instruction": str(instruction), "input": str(inp), "output": str(output)})
        return records
    except Exception as e:
        print(f"  [ГРЕШКА] {path.name}: {e}")
        return []

def load_docx(path: Path) -> list[dict]:
    try:
        doc = Document(path)
        records = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if len(text) > 50:
                records.append({
                    "instruction": "Анализирай текста за цветове:",
                    "input": text,
                    "output": ""
                })
        return records
    except Exception as e:
        print(f"  [ГРЕШКА] DOCX {path.name}: {e}")
        return []

def load_pdf(path: Path) -> list[dict]:
    try:
        reader = PdfReader(path)
        records = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
                for p in paragraphs:
                    records.append({
                        "instruction": "Анализирай техническия текст:",
                        "input": p,
                        "output": ""
                    })
        return records
    except Exception as e:
        print(f"  [ГРЕШКА] PDF {path.name}: {e}")
        return []

def load_md(path: Path) -> list[dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        # Разделяне по заглавия или големи блокове
        sections = re.split(r'\n#+\s+', text)
        records = []
        for sec in sections:
            if len(sec.strip()) > 50:
                records.append({
                    "instruction": "Анализирай документацията:",
                    "input": sec.strip(),
                    "output": ""
                })
        return records
    except: return []

def load_html(path: Path) -> list[dict]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        parser = etree.HTMLParser()
        tree = etree.fromstring(content, parser)
        if tree is not None:
            for s in tree.xpath("//script | //style"):
                s.getparent().remove(s)
            text = etree.tostring(tree, encoding='unicode', method='text')
            paragraphs = [p.strip() for p in text.splitlines() if len(p.strip()) > 60]
            return [{"instruction": "Анализирай уеб съдържанието:", "input": p, "output": ""} for p in paragraphs]
    except: return []

def load_xml(path: Path) -> list[dict]:
    try:
        tree = etree.parse(str(path))
        text = etree.tostring(tree, encoding='unicode', method='text')
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 50]
        return [{"instruction": "Анализирай техническите данни от XML:", "input": l, "output": ""} for l in lines]
    except: return []

LANG_NAMES = {
    "en": "английски", "bg": "български", "fr": "френски", "ru": "руски",
    "de": "немски", "it": "италиански", "es": "испански", "zh": "китайски",
}

def load_tmx(path: Path) -> list[dict]:
    try:
        tree = etree.parse(str(path))
        records = []
        for tu in tree.iter("tu"):
            segments = {}
            for tuv in tu.iter("tuv"):
                lang = tuv.get("{http://www.w3.org/XML/1998/namespace}lang") or tuv.get("lang")
                seg = tuv.find("seg")
                if lang and seg is not None and seg.text:
                    segments[lang.lower()[:2]] = seg.text.strip()

            langs = list(segments.keys())
            if len(langs) >= 2:
                for src, tgt in itertools.permutations(langs, 2):
                    records.append({
                        "instruction": f"Преведи от {LANG_NAMES.get(src, src)} на {LANG_NAMES.get(tgt, tgt)}:",
                        "input": segments[src],
                        "output": segments[tgt]
                    })
        return records
    except:
        return []

def clean_record(rec: dict) -> dict | None:
    def clean_text(t: str) -> str:
        t = re.sub(r"<[^>]+>", " ", str(t))
        t = re.sub(r"\s+", " ", t).strip()
        return t

    instruction = clean_text(rec.get("instruction", ""))
    inp         = clean_text(rec.get("input", ""))
    output      = clean_text(rec.get("output", ""))

    if not output and not inp: return None
    if instruction == output and len(instruction) > 0: return None

    return {"instruction": instruction, "input": inp, "output": output}

def deduplicate(records: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for rec in records:
        key = (rec["instruction"], rec["input"], rec["output"])
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    return unique

ALPACA_TEMPLATE = (
    "Below is an instruction that describes a task, paired with an input "
    "that provides further context. Write a response that appropriately completes the request.\n\n"
    "### Instruction:\n{instruction}\n\n"
    "### Input:\n{input}\n\n"
    "### Response:\n{output}"
)

def format_for_unsloth(rec: dict) -> dict:
    text = ALPACA_TEMPLATE.format(
        instruction=rec["instruction"],
        input=rec["input"],
        output=rec["output"],
    )
    return {**rec, "text": text}

def main():
    parser = argparse.ArgumentParser(description="Подготовка на данни за IRM fine-tuning")
    parser.add_argument("--data_dir", type=str, default="./Full_spectrum", help="Директория с всички данни")
    parser.add_argument("--output",   type=str, default="./dataset", help="Изходен dataset")
    parser.add_argument("--val_split", type=float, default=0.05, help="Validation split")
    args = parser.parse_args()

    all_records = []
    data_path = Path(args.data_dir)

    if not data_path.exists():
        print(f"❌ Директорията {args.data_dir} не съществува.")
        return

    # 1. СЪБИРАНЕ И РАЗАРХИВИРАНЕ
    files_to_process = list(data_path.rglob("*"))
    print(f"📂 Намерени {len(files_to_process)} първоначални обекта")

    final_list = []
    pending = [f for f in files_to_process if f.is_file()]

    while pending:
        fp = pending.pop(0)
        ext = fp.suffix.lower()

        if ext == ".zip":
            zip_extract = fp.parent / f"tmp_train_zip_{int(time.time())}_{os.getpid()}"
            try:
                with zipfile.ZipFile(fp, 'r') as z:
                    z.extractall(zip_extract)
                new_files = [f for f in zip_extract.rglob("*") if f.is_file()]
                pending.extend(new_files)
            except Exception as e:
                print(f"  [ГРЕШКА] При разархивиране на {fp.name}: {e}")
            continue

        final_list.append(fp)

    print(f"📊 Общо файлове за анализ след разархивиране: {len(final_list)}")

    for fp in tqdm(final_list):
        if not fp.is_file(): continue
        ext = fp.suffix.lower()

        if ext == ".jsonl":
            all_records.extend(json_to_instructions(load_jsonl(fp)))
        elif ext == ".json":
            all_records.extend(json_to_instructions(load_json(fp)))
        elif ext in [".csv", ".xlsx", ".xls"]:
            all_records.extend(load_csv_xlsx(fp))
        elif ext == ".docx":
            all_records.extend(load_docx(fp))
        elif ext == ".pdf":
            all_records.extend(load_pdf(fp))
        elif ext == ".md":
            all_records.extend(load_md(fp))
        elif ext == ".html":
            all_records.extend(load_html(fp))
        elif ext == ".xml":
            all_records.extend(load_xml(fp))
        elif ext == ".tmx":
            all_records.extend(load_tmx(fp))

    print(f"📊 Общо събрани: {len(all_records):,} записа")

    cleaned = [clean_record(r) for r in all_records]
    cleaned = [r for r in cleaned if r is not None]
    cleaned = deduplicate(cleaned)

    print(f"✅ След почистване: {len(cleaned):,} записа")

    if not cleaned:
        print("❌ Няма данни за запис.")
        return

    formatted = [format_for_unsloth(r) for r in cleaned]
    dataset = Dataset.from_list(formatted)
    split = dataset.train_test_split(test_size=args.val_split, seed=42)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    split.save_to_disk(str(out_dir))

    print(f"🎉 Dataset записан в: {out_dir}")

if __name__ == "__main__":
    main()
