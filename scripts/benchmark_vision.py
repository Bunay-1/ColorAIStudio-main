"""
Vision Performance Benchmark — ICAP Platform
===========================================
Скрипт за верификация на латентността на Vision AI.
Измерва времето за детекция при различни режими (Standard vs TensorRT).
"""

import time
import os
import numpy as np
from app.modules.vision_engine import VisionEngine

def run_benchmark(iterations=100):
    print(f"🚀 Стартиране на Vision AI Benchmark ({iterations} итерации)...")

    # Инициализиране на двигателя
    engine = VisionEngine(lightweight=True)

    if not engine.enabled:
        print("❌ Vision Engine не е зареден. Проверете наличието на моделни тегла.")
        return

    # Създаване на празно тестово изображение
    test_img = "benchmark_temp.jpg"
    import cv2
    cv2.imwrite(test_img, np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8))

    latencies = []

    # Warm-up
    print("🔥 Warm-up (5 итерации)...")
    for _ in range(5):
        engine.detect_defects(test_img)

    # Actual benchmark
    print("⏱️ Измерване...")
    for i in range(iterations):
        start = time.time()
        engine.detect_defects(test_img)
        end = time.time()
        latencies.append((end - start) * 1000) # ms

    avg_latency = np.mean(latencies)
    p95_latency = np.percentile(latencies, 95)
    fps = 1000 / avg_latency

    print("\n--- Резултати от бенчмарка ---")
    print(f"Средна латентност: {avg_latency:.2f} ms")
    print(f"95-ти персентил:  {p95_latency:.2f} ms")
    print(f"Кадри в секунда (FPS): {fps:.1f}")
    print(f"NVIDIA GPU: {'Активирано' if engine.model.device.type == 'cuda' else 'Не е открито (CPU)'}")
    print("----------------------------\n")

    if avg_latency < 15:
        print("✅ Целта от <15ms е ПОСТИГНАТА!")
    else:
        print("⚠️ Латентността е над целевата. Обмислете използването на TensorRT експорт.")

    # Cleanup
    if os.path.exists(test_img):
        os.remove(test_img)

if __name__ == "__main__":
    run_benchmark()
