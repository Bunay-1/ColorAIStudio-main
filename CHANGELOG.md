# CHANGELOG — ICAP Platform

Всички значими промени по проекта се записват в този файл. Форматът е базиран на [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.2.5] — 2026-06-30

### Добавено
- **Documentation:** Актуализирана технологична таблица в README.md с Redis, GraphQL, OpenTelemetry и др.
- **Repository:** Пълно почистване на локални бинарни файлове и бази данни.

### Променено
- **Versioning:** Актуализация на версията на платформата до 0.2.5 в целия технологичен стек.

## [0.2.4] — 2026-06-30

### Добавено
- **Security:** Интегрирани `SecurityHeadersMiddleware` и `CSRFMiddleware` в основното FastAPI приложение.
- **Security:** Подобрена защита срещу common web vulnerabilities (XSS, CSRF, Clickjacking).

### Променено
- **Versioning:** Актуализация на версията на платформата до 0.2.4 в целия технологичен стек.

## [0.2.3] — 2026-06-30

### Добавено
- **Security:** Създаден официален LICENSE файл за Proprietary софтуер.
- **Documentation:** Актуализирано README с по-реалистичен тон и CI статус бадж.
- **Repository:** Подобрена хигиена на репозиториото и проверка на Git активите.

### Променено
- **Versioning:** Актуализация на версията на платформата до 0.2.3 в целия технологичен стек.
- **Documentation:** Преглед и актуализация на вътрешните линкове в документацията.

## [0.2.2] — 2026-06-30

### Добавено
- **Services:** Нови услуги `services/vision_service.py`, `services/rag_service.py`, `services/color_service.py`, `services/training_service.py` и `services/iot_business_service.py`.
- **Architecture:** Пълно разделяне на бизнес логиката от API контролерите за по-висока стабилност на legacy прокси слоя.
- **Testing:** Разширени интеграционни тестове за legacy прокси функционалността.

### Променено
- **API:** Всички рутери вече използват единствено услуги за изпълнение на бизнес логиката.
- **Versioning:** Актуализация до версия 0.2.2.

## [0.2.1] — 2026-06-30

### Добавено
- **Services:** Рефакториране на бизнес логиката за клиенти и модели в нови модули `services/client_service.py` и `services/model_service.py`.
- **Testing:** Нови Unit тестове за `ConnectionManager` в `tests/test_core.py`.
- **API:** Пълна имплементация на Kubernetes здравни сонди в `app/api/health.py`.
- **CI/CD:** Единен и оптимизиран пайплайн в `.github/workflows/ci-cd.yml`.

### Променено
- **Architecture:** Преминаване към сервизно-ориентиран подход за по-лесно тестване и поддръжка.
- **Versioning:** Актуализация до версия 0.2.1.

## [0.2.0] — 2026-06-30

### Добавено
- **API v1 Migration:** Завършена миграция на всички legacy ендпойнти към официалната v1 структура (`routers/knowledge_graph.py`, `routers/reports.py`, и др.).
- **Legacy Layer:** `app/api/legacy.py` вече е чист прокси слой за по-добра поддръжка.
- **GraphQL:** Подобрена GraphQL интеграция и поправка на потенциални runtime грешки при четене на Lab данни.
- **Testing:** Разширено тестово покритие в `tests/test_v1_migration.py`.

### Променено
- **Versioning:** Актуализация до версия 0.2.0 (Major Migration Update).

## [0.1.1] — 2026-06-30

### Добавено
- **API v1 Migration:** Миграция на ендпойнтите за клиенти и модели към `routers/clients.py` и `routers/models.py`.
- **Testing:** Нова тестова група `tests/test_v1_migration.py` за верификация на мигрираните ендпойнти.

### Променено
- **Versioning:** Актуализация на версията на 0.1.1 в целия технологичен стек.

## [0.1.0] — 2026-06-30

### Добавено
- **Architecture:** Пълно рефакториране на `irm_api.py` — изнасяне на логиката в `app/main.py` и `app/core/lifecycle.py`.
- **Performance:** Добавена 30-секундна пауза в `background_indexer` при успешно изпълнение за оптимизация на ресурсите.
- **Security:** Имплементирана автентикация за всички legacy ендпойнти в `app/api/legacy.py`.
- **Security:** Блокиране на wildcard CORS в production среда.
- **Security:** Маркиране и деактивиране на демо ендпойнти (`hsi_analyze`, `switch_model`) в production.
- **Git:** Конфигуриране на `.gitattributes` за поддръжка на Git LFS за ML модели (`.pt`, `.pth`, `.onnx`).
- **Git:** Добавяне на `icap.db` в `.gitignore`.
- **IoT:** Изнасяне на твърдо кодирани прагове в `.env` (напр. `OPC_UA_TEMP_THRESHOLD`).

### Променено
- **Versioning:** Ресет на версията до 0.1.0 по препоръка за нов проект. Актуализация в целия технологичен стек.

## [8.11.5] — 2026-06-29

### Добавено
- **GraphQL:** Рефакториране на GraphQL рутера с поддръжка на контекст мениджъри и реални Delta E изчисления.
- **Testing:** Нова тестова група за GraphQL (`tests/test_graphql.py`).

### Променено
- **Versioning:** Актуализация на версията на 8.11.5 в целия технологичен стек.

## [8.11.4] — 2026-06-29

### Добавено
- **Security:** Глобален exception handler за предотвратяване изтичането на stack traces.
- **Security:** Автоматизирано сканиране за сигурност с Bandit и Semgrep в CI/CD.
- **Security:** Документация за сигурност (`SECURITY.md`) и насоки за допринасяне (`CONTRIBUTING.md`).
- **DevOps:** Kubernetes Secrets интеграция за чувствителни данни.
- **Documentation:** Двуезична поддръжка (BG + EN) за основните документи.
- **Testing:** Badge за test coverage в README.

### Променено
- **Architecture:** Рефакториране на `irm_api.py` чрез изнасяне на legacy ендпойнтите в `app/api/legacy.py`.
- **Architecture:** Имплементиране на Dependency Injection за клиенти.
- **Versioning:** Актуализация на версията на 8.11.4 в целия технологичен стек.
- **Dependencies:** Фиксиране на версиите на всички зависимости в `requirements.txt`.

### Коригирано
- **Repository:** Изчистване на `__pycache__` и компилирани файлове от Git индекса.

## [8.11.3] — 2026-06-27

### Добавено
- **CI/CD:** Пълна поправка на CI/CD Pipeline — оптимизация на инсталацията на зависимости и конфигурацията на тестовете.
- **Testing:** Корекция на `pytest.ini` за предотвратяване на конфликти при отчитане на покритието.

### Променено
- **Versioning:** Актуализация на версията на 8.11.3 в целия технологичен стек.

## [8.11.2] — 2026-06-27

### Добавено
- **Architecture:** Рефакториране на `irm_api.py` в модулна структура (`app/core`, `app/api`).
- **Architecture:** Миграция към `lifespan` контекст мениджър за FastAPI.
- **Architecture:** Exponential backoff механизъм за фоновия индексер.
- **API:** Въвеждане на `/v1` префикс за всички основни рутери.
- **API:** Pydantic модел валидация за `/clients` ендпойнта.
- **Security:** Защита срещу path traversal в `/download_report`.
- **Security:** Ограничаване на CORS хедърите за по-добра сигурност.
- **Security:** Добавяне на `Deprecation` хедъри към legacy ендпойнтите.
- **Code Quality:** Добавяне на липсващи type hints в основните модули.
- **Repository:** Конфигуриране на `.gitignore` за изключване на DB и моделни файлове.
- **CI/CD:** Добавяне на `setuptools` в CI стъпките за коригиране на `pkg_resources` грешката при изграждане на модели.

### Променено
- **Versioning:** Актуализация до v8.11.2 Enterprise.
- **README:** Актуализация на документацията за новата архитектура.

## [8.11.1] — 2026-06-27

### Коригирано
- **Dependencies:** Корекция на `requirements.txt` — замяна на `strawberry` със `strawberry-graphql` и фиксиране на версиите.
- **Documentation:** Актуализация на версията на 8.11.1 в документацията и Docker конфигурациите.

## [8.11.0] — 2026-06-27

### Добавено
- **Architecture:** Рефакториране на `irm_api.py` в модулна структура (`app/core`, `app/api`).
- **Architecture:** Миграция към `lifespan` контекст мениджър за FastAPI.
- **Architecture:** Exponential backoff механизъм за фоновия индексер.
- **API:** Въвеждане на `/v1` префикс за всички основни рутери.
- **API:** Pydantic модел валидация за `/clients` ендпойнта.
- **Security:** Защита срещу path traversal в `/download_report`.
- **Security:** Ограничаване на CORS хедърите за по-добра сигурност.
- **Security:** Добавяне на `Deprecation` хедъри към legacy ендпойнтите.
- **Code Quality:** Добавяне на липсващи type hints в основните модули.
- **Repository:** Конфигуриране на `.gitignore` за изключване на DB и моделни файлове.

### Променено
- **Versioning:** Актуализация до v8.11.0 Enterprise.
- **README:** Актуализация на документацията за новата архитектура.

## [8.10.0] — 2026-06-26

### Добавено
- **Performance:** Redis caching layer (utils/redis_cache.py) за Delta E изчисления и RAG резултати.
- **Performance:** Интегриране на Redis кеширане в color router (/color/analyze) с 10 мин TTL.
- **Performance:** Интегриране на Redis кеширане в RAG router (/rag/diagnose) с 5 мин TTL.
- **Infrastructure:** Redis контейнер в docker-compose.yml и docker-compose.prod.yml.
- **Testing:** Добавяне на pytest-cov, pytest-asyncio, pytest-timeout в requirements.txt.
- **Testing:** Активиране на 80% test coverage праг в pytest.ini.
- **CI/CD:** Добавяне на coverage reporting в GitHub Actions CI pipeline.
- **Database:** Alembic migration система за PostgreSQL (alembic/).
- **Database:** Първоначална миграция (001_initial_schema.py) за users, tenants, audit_logs, api_keys.
- **Security:** API key rotation manager (utils/api_key_manager.py) за secure API key lifecycle.
- **Security:** CSRF protection middleware (utils/csrf_middleware.py) за state-changing operations.
- **Security:** Security headers middleware (utils/security_headers.py) с CSP, HSTS, X-Frame-Options.
- **Documentation:** Пълен API reference documentation (Docs/API_REFERENCE.md).
- **Documentation:** Architecture documentation с диаграми (Docs/ARCHITECTURE.md).
- **Documentation:** Comprehensive troubleshooting guide (Docs/TROUBLESHOOTING.md).
- **Deployment:** Helm Charts за Kubernetes deployment (helm/icap/).
- **Monitoring:** Log aggregation с Loki и Promtail (monitoring/loki-config.yml, monitoring/promtail-config.yml).
- **Monitoring:** Grafana dashboard за data visualization (monitoring/grafana-dashboard.json).
- **API Versioning:** Пълна поддръжка на API v1 и v2 с backward compatibility (utils/api_versioning.py).
- **Dependencies:** Добавяне на redis, hiredis, alembic, sqlalchemy в requirements.txt.

### Променено
- **Versioning:** Актуализация до v8.10.0 Enterprise.
- **README:** Актуализация на версията и новите функции в v8.10.0.
- **Docker Compose:** Добавяне на Redis service и health checks.
- **Docker Compose Prod:** Пиннати версии на Qdrant (v1.10.1) и добавяне на Redis, Loki, Promtail.
- **Dockerfile:** Актуализация на версията до 8.10.0.
- **docker-compose.yml:** Актуализация на версията на образа до 8.10.0.
- **utils/version.py:** Актуализация на версията до 8.10.0 Enterprise.

### Коригирано
- **Docker Compose Prod:** Премахнато използване на latest tag за Qdrant.

## [8.9.7] — 2026-06-22

### Добавено
- Added CI-driven version validation and changelog enforcement.

### Променено
- Added readiness probe and improved release automation support.

## [8.9.6] — 2026-06-22

### Добавено
- **Observability:** Prometheus metrics instrumentation added for color analysis and RAG endpoints.
- **DevOps:** Updated Dockerfile label, `docker-compose.yml`, and `docker-compose.prod.yml` for release `8.9.6`.
- **Versioning:** Added centralized application version module `utils/version.py`.
- **Deployment:** Updated Kubernetes deployment manifest labels and image tag to `8.9.6`.

### Променено
- **Versioning:** Platform version updated to `8.9.6 Enterprise` across application metadata and health endpoint.
- **Documentation:** README, requirements metadata, and Postman collection updated for `8.9.6`.

## [8.9.5] — 2026-06-20
### Добавено
- **Authentication:** Enhanced JWT authentication system с access/refresh tokens и token blacklist за logout.
- **Authentication:** User management endpoints за CRUD операции над потребители.
- **Authentication:** Role-based permissions с 6 роли (ADMIN, SUPERVISOR, OPERATOR, QUALITY_CONTROL, MAINTENANCE, VIEWER).
- **Multi-tenancy:** Multi-tenancy support модул (utils/multi_tenant.py) с tenant isolation и context management.
- **Multi-tenancy:** Tenant management endpoints за създаване, управление и мониторинг на tenants.
- **Multi-tenancy:** Tenant middleware за автоматично извличане на tenant от headers.
- **Security:** Data encryption at rest модул (utils/encryption.py) с AES-256 encryption за sensitive data.
- **Security:** Encryption helpers за database values, configuration и environment variables.
- **Security:** SSL/TLS configuration (nginx/nginx.conf) с HTTP/2, HSTS и security headers.
- **Security:** SSL certificate generation script за development/testing.
- **Compliance:** Audit logging модул (utils/audit_logger.py) за проследяване на user actions.
- **Compliance:** Audit endpoints за query и summary на audit logs.
- **Scalability:** Advanced rate limiting модул (utils/rate_limiter.py) с per-user и per-tenant limits.
- **Scalability:** Role-based rate limiting с configurable multipliers.
- **Scalability:** Session management модул (utils/session_manager.py) с concurrency control.
- **Scalability:** Kubernetes deployment configuration (k8s/icap-deployment.yaml) с HPA за auto-scaling.
- **Scalability:** Horizontal Pod Autoscaler с CPU/memory-based scaling (3-10 replicas).
- **Integration:** Authentication integration в color, vision и RAG router endpoints.
- **Integration:** Audit logging integration в critical API endpoints.
- **Integration:** Advanced rate limiting integration в API endpoints.
- **Integration:** Multi-tenancy integration в database operations с tenant_id колонки и isolated queries.
- **Testing:** Unit tests за authentication module (tests/test_auth.py).
- **Testing:** Unit tests за multi-tenancy module (tests/test_multi_tenant.py).
- **Testing:** Unit tests за encryption module (tests/test_encryption.py).
- **Testing:** Unit tests за audit logger module (tests/test_audit_logger.py).
- **Testing:** Unit tests за rate limiter module (tests/test_rate_limiter.py).
- **Testing:** Unit tests за session manager module (tests/test_session_manager.py).
- **Testing:** Integration tests за authentication system (tests/test_integration_auth.py).
- **Performance:** Load testing script (scripts/load_test.py) за API performance testing.
- **Performance:** Performance optimizer module (utils/performance_optimizer.py) с monitoring и caching.
- **Performance:** System health monitoring и performance recommendations.
- **Performance:** In-memory cache manager с TTL support.
- **Performance:** Query optimization utilities за database performance.
- **Documentation:** Enterprise Security documentation (Docs/ENTERPRISE_SECURITY.md).
- **Documentation:** Multi-Tenancy Setup Guide (Docs/MULTI_TENANCY_SETUP.md).
- **Documentation:** Performance Tuning Guide (Docs/PERFORMANCE_TUNING.md).
- **Documentation:** Monitoring and Alerting Configuration (Docs/MONITORING_ALERTING.md).
- **Documentation:** Disaster Recovery Procedures (Docs/DISASTER_RECOVERY.md).
- **Documentation:** API Examples for Enterprise Features (Docs/API_EXAMPLES.md).
- **Documentation:** Enhanced OpenAPI/Swagger documentation за auth endpoints.
- **Documentation:** Enhanced OpenAPI/Swagger documentation за tenant endpoints.
- **Testing:** Postman collection за API testing (postman/ICAP_Enterprise_Collection.json).
- **Testing:** Integration tests за multi-tenancy (tests/test_integration_multi_tenant.py).
- **Testing:** Integration tests за rate limiting (tests/test_integration_rate_limiting.py).
- **Testing:** Integration tests за audit logging (tests/test_integration_audit_logging.py).
- **Testing:** End-to-end tests за enterprise workflows (tests/test_e2e_enterprise_workflows.py).
- **Documentation:** Migration Guide от v8.9.1 към v8.9.5 Enterprise (Docs/MIGRATION_GUIDE.md).
- **Documentation:** Quick Start Guide за Enterprise Features (Docs/QUICK_START_ENTERPRISE.md).
- **Documentation:** Security Audit Checklist (Docs/SECURITY_AUDIT_CHECKLIST.md).
- **Scripts:** Enterprise backup script (scripts/backup_enterprise.py).
- **Scripts:** Enterprise restore script (scripts/restore_enterprise.py).
- **Features:** API versioning support (utils/api_versioning.py) с version negotiation и response transformation.
- **Features:** API versioning middleware integration в main application.
- **Monitoring:** Performance benchmarking suite (scripts/benchmark_performance.py).
- **Monitoring:** Grafana dashboard configuration за ICAP Enterprise monitoring (k8s/grafana-dashboard.json).
- **Notifications:** Real-time notifications service (utils/notification_service.py) с WebSocket, Email, Slack и Webhook channels.
- **Notifications:** Notifications router (routers/notifications.py) с REST API endpoints за notification management.
- **Analytics:** Advanced analytics service (utils/analytics_service.py) с metrics, reports и trend analysis.
- **Analytics:** Analytics router (routers/analytics.py) с REST API endpoints за analytics operations.
- **Webhooks:** Webhook service (utils/webhook_service.py) с event subscriptions, delivery retries и signature verification.
- **Webhooks:** Webhook router (routers/webhooks.py) с REST API endpoints за webhook management.
- **Compliance:** Automated compliance reporting service (utils/compliance_service.py) за GDPR, SOC2, HIPAA, ISO27001, PCI_DSS.
- **Compliance:** Compliance router (routers/compliance.py) с REST API endpoints за compliance operations.
- **MFA:** Multi-factor authentication service (utils/mfa_service.py) с TOTP, QR codes и backup codes.
- **MFA:** MFA router (routers/mfa.py) с REST API endpoints за MFA operations.
- **Cache:** Caching layer service (utils/cache_service.py) с memory/disk caching, LRU eviction и statistics.
- **Cache:** Cache router (routers/cache.py) с REST API endpoints за cache management.
- **Export/Import:** Data export/import service (utils/export_import_service.py) с JSON/CSV formats.
- **Export/Import:** Export/import router (routers/export_import.py) с REST API endpoints за data operations.
- **Admin Dashboard:** React-based admin dashboard (admin_dashboard/) с TailwindCSS за enterprise management.
- **SDKs:** Python client SDK (sdk/python/icap_client.py) за ICAP API integration.
- **SDKs:** JavaScript client SDK (sdk/javascript/icap-client.js) за ICAP API integration.
- **CI/CD:** Enhanced GitHub Actions workflow с Docker scanning, deployment jobs и notifications.
- **Documentation:** README updated с нови enterprise features (notifications, analytics, webhooks, compliance, mfa, cache, export/import).

### Променено
- **Versioning:** Актуализация до v8.9.5 Enterprise.
- **README:** Актуализация на версия до v8.9.5 Enterprise.

## [8.9.4] — 2026-06-20
### Добавено
- **Documentation:** Enhanced OpenAPI/Swagger documentation с detailed descriptions, tags и examples.
- **Documentation:** Developer guide (Docs/DEVELOPER_GUIDE.md) с project structure, setup instructions и contribution guidelines.
- **Documentation:** Deployment guide (Docs/DEPLOYMENT_GUIDE.md) с Docker, Kubernetes и production configurations.
- **Documentation:** Backup strategy documentation (Docs/BACKUP_STRATEGY.md) с comprehensive backup/recovery procedures.
- **DevOps:** Production Docker Compose configuration (docker-compose.prod.yml) с monitoring stack (Prometheus, Grafana, Jaeger).
- **DevOps:** Enhanced health check endpoint с comprehensive service status и system resource monitoring.
- **DevOps:** GitHub Actions CI/CD pipeline вече включва security scanning, configuration validation и performance benchmarking.

### Променено
- **Versioning:** Актуализация до v8.9.4 Enterprise.

## [8.9.3] — 2026-06-20
### Добавено
- **Testing:** Integration tests за Color Engine, RAG System и IoT Connectors (test_integration_color.py, test_integration_rag.py, test_integration_iot.py).
- **Testing:** End-to-end tests за critical workflows (test_e2e_workflows.py) - color analysis, trend prediction, recipe formulation.
- **Testing:** Pytest configuration (pytest.ini) за automated test coverage reporting с 70% minimum threshold.
- **Performance:** Parallel embedding processing в RAG system с batch processing за по-бързо индексиране.
- **Performance:** Batch processing за vision operations в multi_view_fusion метода за по-добра производителност.
- **Performance:** Cache manager модул (utils/cache_manager.py) с LRU cache за скъпи изчисления.
- **Performance:** Caching за SPC calculations в ai_color_analysis.py за по-бърза статистика.
- **Database:** Database query optimizations с connection pooling, WAL mode и indexes за common queries.
- **Database:** Optimized helper functions за batch, machine и recent measurements queries.
- **Database:** Automated cleanup function за old data maintenance.
- **Observability:** Correlation ID middleware (utils/correlation_id.py) за проследяване на заявки през системата.
- **Observability:** Интеграция на correlation ID middleware в main API за request tracing.
- **Observability:** OpenTelemetry distributed tracing модул (utils/tracing.py) с Jaeger exporter.
- **Observability:** Интеграция на OpenTelemetry tracing в main API за distributed tracing.
- **Business Metrics:** Custom business metrics module (utils/business_metrics.py) за quality, performance и efficiency KPIs.
- **Alerting:** Подобрена alerting system с rate limiting, deduplication, escalation logic и statistics tracking.

### Променено
- **Versioning:** Актуализация до v8.9.3 Enterprise.

## [8.9.2] — 2026-06-20
### Коригирано
- **Configuration Management:** Премахнати hard-coded стойности в IoT конекторите (iot_connector.py, opc_ua_connector.py) и заменени с environment variables.
- **Error Handling:** Подобрено error handling във vision_engine.py с по-добра устойчивост при Triton client initialization, YOLO model loading и ViT initialization.
- **Error Handling:** Добавен robust error handling в rag_system.py за Qdrant operations, embedding generation и query operations.
- **Resilience:** Добавена reconnection logic за MQTT connector с exponential backoff и max retry attempts.
- **Resilience:** Добавен circuit breaker pattern за защита на external services (Ollama, Qdrant) от cascade failures.
- **Security:** Премахнати реални API keys от .env.example и заменени с placeholder стойности.
- **Input Validation:** Добавена comprehensive input validation в color router с проверки за Lab координати, tolerance и batch size.
- **Input Validation:** Добавена input validation в vision router с проверки за файлови формати и размери.

### Добавено
- **Circuit Breaker:** Нов модул utils/circuit_breaker.py за защита на external services с OPEN/CLOSED/HALF_OPEN states.

### Променено
- **Versioning:** Актуализация до v8.9.2 Enterprise.

## [8.9.1] — 2026-06-20
### Добавено
- **AI Transparency:** Прецизиране на AI терминологията в документацията и кода (диференциация между Heuristics и ML).
- **Launcher Stability:** Цялостна преработка на `run_icap.bat` с подобрена диагностика и Python detection.
- **MLOps Registry:** Въвеждане на официална документация за жизнения цикъл на моделите (Docs/MLOPS.md).
- **Performance Evidence:** Публикуване на конкретни хардуерни и наборовни данни доказателства за бенчмарковете в Docs/PRODUCTION_READY.md.
- **RAG Live Visibility:** Възстановено и подобрено автоматично фоново индексиране с визуализация на чанковете в реално време.
- **RAG Stats Sync:** Добавена автоматична синхронизация между индексер състоянието и Qdrant базата, гарантираща актуални статистики.
- **Color Engine Stability:** Поправени критични грешки при изчисляване на Delta E и Metamerism Index за съвместимост с ASTM E308.
- **Trend Prediction Fix:** Елиминиран TypeError в прогнозирането на трендове при малък набор от данни.
- **Assistant Stability:** Поправен критичен бъг в RAG търсенето при работа в Edge/Lightweight режим (AttributeError fix).

### Променено
- **Versioning:** Актуализация до v8.9.1 Enterprise.
- **Database Strategy:** SQLite е дефиниран като решение за Edge мащабируемост, с опция за PostgreSQL при Cloud инсталации.
- **Status Alignment:** Актуализиране на статусите на функциите в README (Production vs Research).

### Коригирано
- **Batch Script:** Поправени критични грешки в `run_icap.bat`, водещи до крашове при стартиране.

## [8.8.0] — 2026-06-19
### Добавено
- **Infrastructure Hardening:** Пиннати версии на образи и ресурсни лимити в Docker Compose.
- **Remote Qdrant Support:** Динамично превключване между локален и отдалечен Qdrant сървър.
- **Docker Connectivity:** Поправена връзка към Ollama чрез `host.docker.internal`.
- **Security Hardening:** Премахната публична експозиция на векторната база данни.

### Променено
- **Versioning:** Актуализация до v8.8.0 Enterprise.

## [8.7.0] — 2026-06-18
### Добавено
- **Modular API Architecture:** Имплементиране на FastAPI Routers за разделяне на бизнес логиката.
- **JWT Authentication:** Нова система за сигурност с токени и роли (RBAC).
- **SQL Enterprise Core:** Унифициран SQL бекенд за измервания, клиенти и модели.

### Променено
- **Refactoring:** Монолитният `irm_api.py` е разбит на специализирани рутери.
- **Version bump:** Актуализация до v8.7.0 Enterprise.

## [8.5.0] — 2026-06-17
### Добавено
- **Benchmarking Engine:** Нова система за измерване на реалната производителност.
- **Enterprise RBAC:** Начална имплементация на Role-Based Access Control.

### Променено
- **Version bump:** Актуализация на версията на платформата на 8.5.0.

## [8.4.3] — 2026-06-16
### Добавено
- **Technical Precision:** Коригирани CO2 коефициенти съгласно Eurostat 2023.
- **Orchestration:** Пълна поддръжка на `docker-compose.yml` за API и Qdrant.

### Променено
- **Terminology:** "ISO 9001 Compliant" е заменено с "ISO 9001 Compliance Support".
- **Terminology:** Ребрандиране на "Root Cause Intelligence" в "AI-Assisted Diagnostic Support".

## [8.3.1] — 2024-11-20
- Начална Enterprise версия с RAG, Vision AI и Multi-Agent оркестрация.
