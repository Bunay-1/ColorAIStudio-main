# Industrial Color AI Platform (ICAP) v0.2.8 Enterprise

![ICAP Banner](https://img.shields.io/badge/Industrial_AI-v0.2.8-blue?style=for-the-badge&logo=ai)
<!-- icap-v0.2.8 -->
![ISO 9001 Compliance Support](https://img.shields.io/badge/ISO_9001-Compliance_Support-green?style=for-the-badge)
![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)
[![CI Status](https://github.com/your-username/icap/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/your-username/icap/actions)
![Test Coverage](https://img.shields.io/badge/Coverage-85%25-brightgreen?style=for-the-badge&logo=pytest)

## 🚀 Общ Преглед
**Industrial Color AI Platform (ICAP)** е специализирано софтуерно решение за автоматизиран качествен контрол и колориметричен анализ в индустриални среди. Платформата съчетава компютърно зрение (Vision AI) и семантично търсене (RAG) за осигуряване на прецизност и проследимост съгласно стандарта ISO 9001.

### 🌟 Текущ фокус (v0.2.8):
- **GraphRAG**: Дълбоко семантично търсене с логически връзки.
- **Digital Twin**: Симулация на процеси и прогнозиране на качеството.
- **Vision Optimization**: TensorRT поддръжка за ултра-ниска латентност.
- **ESG Monitoring**: Автоматизиран CO2 отпечатък съгласно ISO 14040.

---

## 🏗 Архитектура
ICAP е проектирана като модулна микросървисна екосистема, оптимизирана за Edge и Cloud разгръщане. Детайлно описание можете да намерите в **[Architecture Documentation](Docs/ARCHITECTURE.md)**.

### Основни компоненти:
1. **API Gateway (FastAPI)**: Централна оркестрация.
2. **Vector Core (Qdrant)**: Семантична памет.
3. **Intelligence Layer (Ollama)**: Локални LLM разсъждения.
4. **Vision AI**: Анализ в реално време.

---

## ⚡ Производителност (Целеви показатели)
Посочените данни са базирани на вътрешни бенчмаркове в контролирана Edge среда (NVIDIA Jetson Orin). За детайлна методология и реални резултати, вижте **[Production Readiness](Docs/PRODUCTION_READY.md)**.

- **Vision Latency**: < 15ms (целева).
- **RAG Speed**: ~1000 страници/мин индексиране.
- **Accuracy**: > 94% mAP за детекция на специфични дефекти.
- **Uptime**: 99.9% проектирана наличност.

---

## 🛠 Технологичен Стек

| Категория | Технологии |
| :--- | :--- |
| **Език & Framework** | Python, FastAPI, Uvicorn |
| **AI & LLM** | Ollama, Qdrant, Ultralytics (YOLO), Transformers (ViT) |
| **Кеширане & API** | Redis, GraphQL (Strawberry), WebSockets |
| **Индустриална Свързаност** | MQTT, OPC-UA |
| **Наблюдаемост** | OpenTelemetry, Prometheus, Grafana |
| **Инфраструктура** | Docker, PostgreSQL, Alembic |

---

## 🧩 Модулна Документация
- 🎨 **[Color Engine](Docs/COLOR_ENGINE.md)**: Математическо ядро [Stable].
- 👁️ **[Vision AI](Docs/VISION_AI.md)**: Детекция на дефекти [Stable].
- 📚 **[RAG System](Docs/RAG_SYSTEM.md)**: База знания [Beta].
- 🤖 **[Multi-Agent Workspace](Docs/MULTI_AGENT.md)**: AI Агенти [Beta].
- 🔌 **[IoT Connectors](Docs/IOT_CONNECTORS.md)**: Свързаност [Stable].
- 🍃 **[Sustainability](Docs/SUSTAINABILITY.md)**: CO2 отпечатък [Beta].
- 🕸️ **[Knowledge Graph](Docs/KNOWLEDGE_GRAPH.md)**: Онтология [Beta].
- 🏢 **[Digital Twin](Docs/DIGITAL_TWIN.md)**: Симулационен модел [Beta].

---

## 🚀 Бързо начало (Getting Started)

### 1. Предварителни изисквания
- **Docker & Docker Compose** (препоръчително)
- **Ollama** (за локални AI функции)
- **NVIDIA GPU** (за оптимална производителност на Vision AI)

### 2. Стартиране в 3 стъпки
```bash
# 1. Клонирайте хранилището
git clone https://github.com/your-username/icap.git && cd icap

# 2. Подгответе конфигурацията
cp .env.example .env

# 3. Стартирайте платформата
docker-compose up -d
```
Платформата ще бъде достъпна на `http://localhost:8000`. Документацията на API е на `http://localhost:8000/docs`.

---

## 📥 Инсталация и Конфигурация

```bash
# Стартиране чрез Docker Compose (API + Qdrant + Redis)
docker-compose up -d
```
За подробни инструкции вижте **[Deployment Guide](Docs/DEPLOYMENT_GUIDE.md)**.

---

## 🛡 Сигурност и Лиценз
Този софтуер е **Proprietary** (Собственически). Всички права са запазени. Използването в търговска среда изисква валиден лицензен ключ. Вижте **[LICENSE](LICENSE)** и **[SECURITY.md](SECURITY.md)**.

---
**Бележка относно AI:** Платформата използва "AI" като общ термин. Диагностичните функции в момента се базират на хибридни експертни системи и евристични алгоритми, съчетани с машинно обучение за визуална инспекция.

*Изготвено от: ICAP Engineering Team | v0.2.8 | 2026*
