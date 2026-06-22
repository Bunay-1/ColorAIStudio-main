# ICAP MLOps Pipeline & Model Lifecycle

## 1. Model Registry & Versioning
Всички AI модели (YOLO, ViT, LLM) се описват централизирано в `model_registry.json`. Платформата поддържа:
- **Versioning:** Семантично версиониране за всеки модел.
- **Rollback:** Възможност за връщане към стабилна версия през таблото.
- **Metadata:** Проследяване на точност (Accuracy) и дата на обучение.

## 2. Dataset Management
Данните за обучение и тест се съхраняват в `test_dataset/`.
- **Structure:** Разделени на `train/` и `test/` сетове за Vision и Color данни.
- **Active Learning:** Скриптът `vision_engine.py` автоматично записва изображения с ниска увереност в `AuditTrail/ActiveLearning/` за човешки преглед и повторно обучение.

## 3. Retraining Pipeline
Процесът на фино напасване (Fine-tuning) е автоматизиран:
1.  **Drift Detection:** `ai_color_analysis.py` използва CUSUM за засичане на отклонения в измерванията.
2.  **Trigger:** При засичане на дрейф, се генерира препоръка за ретрейнинг.
3.  **Training:** Използва се `finetune_unsloth.py` за оптимизирано обучение върху GPU.
4.  **Evaluation:** Автоматична оценка чрез `evaluate_model.py` преди разгръщане.

## 4. Edge Deployment
- **TensorRT:** Компилиране на моделите за максимална производителност на Edge устройства.
- **Triton Integration:** Поддръжка за NVIDIA Triton Inference Server при нужда от облачно мащабиране.

---
*ICAP Machine Learning Operations | v8.9.1*
