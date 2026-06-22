# ICAP Benchmark Methodology (v8.8.0)

Този документ описва методологията, използвана за изчисляване на показателите за производителност, посочени в документацията на ICAP.

## 1. Vision Latency (< 15ms)
- **Dataset:** 500 изображения (1280x720) с различни индустриални дефекти (драскотини, вдлъбнатини, цветови петна).
- **Инструментариум:** `benchmark_performance.py` (използва `time.perf_counter()`).
- **Метод:** Измерва се времето от подаване на изображението към `vision_engine.detect_defects` до получаване на JSON резултат.
- **Хардуер:** NVIDIA Jetson Orin AGX (TensorRT FP16). Измерването не включва времето за мрежов трансфер при HTTP заявка.

## 2. RAG Indexing Speed (~1000 стр./мин)
- **Dataset:** technical_manuals_v3 (пакет от 100 PDF файла, всеки средно по 50 страници).
- **Метод:** Измерва се общото време за `rag.index_any()` за целия пакет.
- **Хардуер:** Intel Core i9-13900K, NVMe SSD Gen4.
- **Бележка:** Скоростта зависи силно от избрания embedding модел и производителността на Qdrant (local vs. cloud).

## 3. Vision Accuracy (> 94% mAP)
- **Dataset:** COCO-format industrial dataset (2500 тренировъчни, 500 тестови изображения).
- **Метрика:** mean Average Precision (mAP) при IoU=0.5.
- **Инструментариум:** `ultralytics` val mode.

## 4. Stability (99.9% Uptime)
- **Период:** 30 дни непрекъсната работа в Edge симулация.
- **Критерий:** Липса на memory leaks и < 0.1% неуспешни API заявки (HTTP 5xx).

## 5. Как да стартирате локален бенчмарк
Използвайте предоставения скрипт:
```bash
python tests/benchmark_performance.py --iterations 100
```
Скриптът ще генерира отчет `benchmark_results.json` с актуалните показатели за вашата текуща хардуерна конфигурация.
