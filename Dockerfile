# ICAP Platform Dockerfile — v8.11.3 Enterprise
# Multi-stage build for optimized image size and security
# Оптимизиран за индустриално приложение с GPU поддръжка

# Stage 1: Builder
FROM nvidia/cuda:12.1.0-base-ubuntu22.04 AS builder

# Дефиниране на променливи на средата
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUTF8=1
ENV TRANSFORMERS_OFFLINE=1
ENV HF_DATASETS_OFFLINE=1

# Инсталираме системни зависимости за Vision, AI и Мрежова работа
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Настройваме работна директория
WORKDIR /app

# Копираме requirements.txt и инсталираме Python пакети
COPY requirements.txt .
RUN pip3 install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
LABEL org.opencontainers.image.version="8.11.3"

# Дефиниране на променливи на средата
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUTF8=1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Инсталираме само runtime зависимости
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Копираме инсталираните пакети от builder stage
COPY --from=builder /root/.local /root/.local

# Настройваме работна директория
WORKDIR /app

# Създаваме структура за данни
RUN mkdir -p /app/RAG /app/vector_db /app/AuditTrail /app/Docs

# Копираме само необходимите файлове
COPY requirements.txt .
COPY irm_api.py .
COPY color_engine.py .
COPY ai_color_analysis.py .
COPY vision_engine.py .
COPY agents_system.py .
COPY rag_system.py .
COPY knowledge_graph.py .
COPY database.py .
COPY alerting_system.py .
COPY iot_connector.py .
COPY opc_ua_connector.py .
COPY voice_assistant.py .
COPY synthetic_gen.py .
COPY prepare_data.py .
COPY evaluate_model.py .
COPY finetune_unsloth.py .
COPY app/ ./app/
COPY routers/ ./routers/
COPY services/ ./services/
COPY utils/ ./utils/
COPY model_registry.json .

# Създаваме non-root user за security
RUN useradd -m -u 1000 icapuser && \
    chown -R icapuser:icapuser /app /root/.local

# Switch to non-root user
USER icapuser

# Експонираме порт за FastAPI
EXPOSE 8000

# Стартираме API сървъра
# За продукция в индустриална мрежа се препоръчва използването на --env-file при стартиране
CMD ["python3", "irm_api.py"]

# Healthcheck за Docker Desktop и Orchestrators
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
