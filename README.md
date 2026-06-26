# Industrial Color AI Platform (ICAP) v8.11.2 Enterprise

![ICAP Banner](https://img.shields.io/badge/Industrial_AI-v8.11.2-blue?style=for-the-badge&logo=ai)
![ISO 9001 Compliance Support](https://img.shields.io/badge/ISO_9001-Compliance_Support-green?style=for-the-badge)
![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)

## 🚀 Общ Преглед
**Industrial Color AI Platform (ICAP)** е надеждно софтуерно решение за автоматизиран качествен контрол и колориметричен анализ. Проектирана за индустриална експлоатация, платформата осигурява прецизни измервания и проследимост на данните чрез интеграция на компютърно зрение и семантично търсене.

### 🌟 Ключови подобрения в v8.11.2 Enterprise [Stable]:
- **Architectural Refactoring**: Разделяне на ядрото и API логиката за по-добра поддръжка.
- **Enhanced Security**: Pydantic валидация, защита срещу Path Traversal и подобрени CORS политики.
- **Robust Background Indexer**: Exponential backoff за по-добра устойчивост при грешки.
- **API Versioning (v1)**: Въвеждане на официално API версиониране и пренасочване на legacy ендпойнти.
- **Lifespan Management**: Миграция към модерен FastAPI lifespan за управление на ресурсите.
- **Redis Caching Layer**: Високопроизводителен кеш за Delta E изчисления и RAG резултати (30-50% подобрение).
- **Test Coverage 80%+**: Автоматизирано измерване на test coverage с pytest-cov и CI integration.
- **PostgreSQL Migration**: Пълна поддръжка на PostgreSQL за production с Alembic migrations.
- **API Key Rotation**: Secure API key lifecycle management с автоматична ротация.
- **CSRF Protection**: Cross-Site Request Forgery защита за state-changing operations.
- **Security Headers**: Enhanced HTTP security headers (CSP, HSTS, X-Frame-Options).
- **SQL Audit Core**: Миграция на Audit Trail към SQLite за Edge мащабируемост. Поддържа PostgreSQL за Cloud инсталации.
- **Persistent Indexing State**: Пълна устойчивост на фоновия индексер при рестарт.
- **Lifespan State Management**: Dependency Injection архитектура за по-добра стабилност при натоварване.
- **Configurable Security**: Гъвкаво управление на CORS и подобрена диагностика на връзките.
- **Orchestrated Architecture [Production]**: Пълна поддръжка на Docker Compose за разгръщане на API, Qdrant, Ollama и Redis.
- **Enterprise Security [Production]**: Интегрирани насоки за мрежова сегментация и least-privilege достъп.
- **ISO 9001 Compliance Support [Production]**: Автоматизирано логване и проследимост за улесняване на одитните процеси.
- **Push Alerting System [Production]**: Интеграция със Slack, Email и SMS за критични отклонения.
- **Color AI Core [Production]**: Математическо ядро за Delta E и MI изчисления, валидирано по ISO/CIE.
- **Optimized RAG Indexing [Production]**: До 5 пъти по-бързо индексиране на техническа документация.
- **AI-Assisted Diagnostic Support [Research/Beta]**: Вероятностен анализ на причините за дефекти (Heuristic + KG интеграция).
- **Vision AI Precision [Stable]**: Високопрецизен анализ (YOLOv11/ViT) и Explainability слой (Grad-CAM).
- **Multi-Agent Orchestration [Beta]**: Автономни агенти с Human-in-the-loop Guardrails.
- **Sustainability LCA [Beta]**: Интеграция с IoT енергийни данни и бенчмаркинг по ISO 14040.
- **What-if Optimization [Research]**: Симулации за промяна на рецепти и производствени параметри.
- **Temporal Knowledge Graph [Research]**: Проследяване на промените във връзките във времето.
- **Strategic Multi-Agent Framework**: 9 специализирани агента, организирани в 3 стабилни работни потока.
- **Industrial RAG & Ontology**: Семантично търсене в техническа документация, интегрирано с индустриални стандарти.
- **Sustainability Analytics**: Изчисляване на CO2 отпечатък на база реална консумация.
- **Enterprise Dashboard**: Управление на флота от устройства и мониторинг на ресурсите в реално време.
- **Стабилност и Мащаб**: Подобрена WebSocket свързаност и Scalar Quantization за работа с големи бази данни.
- **Real-time Notifications**: WebSocket, Email, Slack и Webhook notifications за real-time alerts и updates.
- **Advanced Analytics**: Comprehensive analytics dashboard с metrics, reports и trend analysis.
- **Webhook Integration**: Event-driven архитектура с webhook subscriptions, delivery retries и signature verification.
- **Compliance Reporting**: Automated compliance reports за GDPR, SOC2, HIPAA, ISO27001, PCI_DSS.
- **Multi-Factor Authentication (MFA)**: TOTP-based authentication с QR codes, backup codes и verification.
- **Caching Layer**: Performance optimization с memory/disk caching, LRU eviction и statistics tracking.
- **Data Export/Import**: JSON/CSV export/import за users, tenants, measurements, audit logs.

---

## 🏗 Архитектура на Системата
ICAP е проектирана като модулна микросървисна екосистема:
1.  **API Gateway (FastAPI):** Централен хъб за заявки и оркестрация.
2.  **Vector Core (Qdrant):** Високопроизводителна база за семантично търсене.
3.  **Intelligence Layer (Ollama):** Локално изпълнение на LLM за технически разсъждения.
4.  **Vision Engine (YOLO/ViT):** Обработка на изображения в реално време.
5.  **IoT Mesh (MQTT/OPC-UA):** Двупосочна връзка с индустриалния хардуер.

---

## ⚡ Производителност и Надеждност
ICAP е оптимизирана за тежки индустриални среди:
- **Vision Latency:** < 15ms (YOLOv11 TensorRT).
- **RAG Speed:** ~1000 стр./мин индексиране.
- **Accuracy:** > 94% mAP за детекция на дефекти.
- **Stability:** 99.9% ъптайм в Edge режим.
- **Одит:** Пълна проследимост (Audit Trail) на всяко измерване.

*За детайлни бенчмаркове вижте **[Production Readiness](Docs/PRODUCTION_READY.md)**.*

---

## 🛠 Технологичен Стек

| Категория | Технологии |
| :--- | :--- |
| **Език и Рамка** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![Uvicorn](https://img.shields.io/badge/Uvicorn-202020?style=flat) |
| **Enterprise Security** | ![RBAC](https://img.shields.io/badge/RBAC-Foundation-blue?style=flat) ![Backup](https://img.shields.io/badge/Backup-Service-green?style=flat) |
| **AI и Анализ** | ![Scikit_learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikit-learn&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white) ![Numpy](https://img.shields.io/badge/Numpy-013243?style=flat&logo=numpy&logoColor=white) |
| **LLM и RAG** | ![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat&logo=ollama&logoColor=white) ![Qdrant](https://img.shields.io/badge/Qdrant-FF4B4B?style=flat&logo=qdrant&logoColor=white) ![GraphRAG](https://img.shields.io/badge/GraphRAG-NetworkX-orange?style=flat) ![FastEmbed](https://img.shields.io/badge/FastEmbed-SPLADE-blue?style=flat) |
| **Alerting & Push** | ![Slack](https://img.shields.io/badge/Slack-4A154B?style=flat&logo=slack&logoColor=white) ![Email](https://img.shields.io/badge/Email-D14836?style=flat&logo=gmail&logoColor=white) ![Twilio](https://img.shields.io/badge/Twilio-F22F46?style=flat&logo=twilio&logoColor=white) |
| **Документи** | ![LXML](https://img.shields.io/badge/LXML-Parsing-green?style=flat) ![TMX](https://img.shields.io/badge/TMX-Multi--lang-blue?style=flat) ![ZIP](https://img.shields.io/badge/ZIP-Processing-red?style=flat) |
| **Vision AI** | ![YOLOv11](https://img.shields.io/badge/YOLOv11-00FFFF?style=flat) ![ViT](https://img.shields.io/badge/Vision_Transformer-red?style=flat) ![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=flat&logo=opencv&logoColor=white) |
| **3D и Графики** | ![Three.js](https://img.shields.io/badge/Three.js-000000?style=flat&logo=three.js&logoColor=white) ![Chart.js](https://img.shields.io/badge/Chart.js-FF6384?style=flat&logo=chart.js&logoColor=white) |
| **Индустриална Свързаност** | ![MQTT](https://img.shields.io/badge/MQTT-3C5288?style=flat&logo=mqtt&logoColor=white) ![OPC-UA](https://img.shields.io/badge/OPC--UA-FFA500?style=flat) ![WebSockets](https://img.shields.io/badge/WebSockets-Real--time-yellow?style=flat) |
| **Sustainability** | ![Eco_Score](https://img.shields.io/badge/Sustainability-Industry_5.0-green?style=flat) ![LCA](https://img.shields.io/badge/LCA-Analysis-blue?style=flat) |
| **Инфраструктура** | ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white) ![MLOps](https://img.shields.io/badge/MLOps-Version_Control-red?style=flat) ![Quantization](https://img.shields.io/badge/Scalar_Quantization-INT8-green?style=flat) |

---

## 🧩 Модулна Документация
Платформата е изградена на модулен принцип. Изберете специфично ръководство за детайлна информация:

- 🎨 **[Color Engine](Docs/COLOR_ENGINE.md)**: Математическо ядро за Delta E и MI изчисления.
- 👁️ **[Vision AI](Docs/VISION_AI.md)**: Детекция на дефекти и анализ на повърхности.
- 📚 **[Semantic RAG System](Docs/RAG_SYSTEM.md)**: Интелигентно управление на базата знания.
- 🤖 **[Multi-Agent Workspace](Docs/MULTI_AGENT.md)**: Оркестрация на автономни AI агенти.
- 🕸️ **[Knowledge Graph](Docs/KNOWLEDGE_GRAPH.md)**: Интерактивна визуализация и логическо разсъждение.
- 🌈 **[HSI Diagnostics](Docs/HSI_DIAGNOSTICS.md)**: Хиперспектрален анализ на материали.
- 🏗️ **[3D Digital Twin](Docs/DIGITAL_TWIN.md)**: Визуализация на качеството върху 3D модели.
- 🔌 **[IoT Connectors](Docs/IOT_CONNECTORS.md)**: Интеграция с MQTT и OPC-UA.
- 🍃 **[Sustainability Engine](Docs/SUSTAINABILITY.md)**: Анализ на CO2 отпечатък и екологичен индекс.
- 📈 **[Training Guide](Docs/TRAINING_GUIDE.md)**: Fine-tuning на AI моделите.
- 🔄 **[MLOps Registry](Docs/MLOPS.md)**: Управление на жизнения цикъл на моделите.

---

## 📥 Инсталация и Конфигурация

### 1. Настройка на околната среда
Създайте `.env` файл в корена на проекта със следните параметри:
```env
MQTT_BROKER=192.168.1.50
OPC_UA_SERVER_URL=opc.tcp://192.168.1.100:4840/
API_URL=http://localhost:8000
ICAP_EDGE_MODE=1  # 1 за оптимизация на Jetson/Edge

# Ollama Конфигурация
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=irm-industrial  # Името на модела, не път към него
```

### 2. Стартиране чрез Docker (Препоръчително)
Най-лесният начин за стартиране на цялата екосистема (API + Qdrant + Redis) е чрез Docker Compose:

```bash
docker-compose up -d
```

Алтернативно, за самостоятелен контейнер:
```bash
docker build -t icap-v8.11.2 .
docker run -p 8000:8000 --env-file .env icap-v8.11.2
```

### 3. Ръчна инсталация
#### За Windows:
Стартирайте `run_icap.bat`. Скриптът автоматично създава изолирана виртуална среда (`.venv`), инсталира нужните зависимости и стартира API сървъра. Включва вградена диагностика при грешки.

#### За Linux/macOS:
```bash
# Клонирайте и инсталирайте зависимостите
pip install -r requirements.txt

# Стартирайте API сървъра
python irm_api.py
```
След стартиране, отворете `irm_dashboard.html` в браузър за достъп до графичния интерфейс.

---

## 🛡 ISO 9001 и Одит
ICAP включва вградена система за **Audit Trail**, която логва всяко измерване и AI действие в `AuditTrail/measurements_log.csv`. Това гарантира пълна проследяемост на качеството съгласно международните стандарти.

## 📄 Лиценз
Този софтуер е **Proprietary** (Собственически). Всички права са запазени. Използването в търговска среда изисква валиден лицензен ключ.

---
**Забележка относно AI терминологията:** Платформата използва "AI" като общ термин за интелигентни функции. Функциите за диагностика (RCA) в момента се базират на усъвършенствани евристични алгоритми и експертни системи за подпомагане на вземането на решения (DSS), докато Vision Engine (YOLO/ViT) използва дълбоко машинно обучение с валидирани метрики.

---
*Изготвено от: ICAP Engineering Team | v8.11.2 | 2026*
