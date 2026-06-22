#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Деплой на Fine-Tuned Industrial Reasoning Model с Ollama
# ═══════════════════════════════════════════════════════════════════
# Изисква: Ollama инсталиран (https://ollama.com)
# Използване: bash deploy_ollama.sh ./my_irm_model

MODEL_DIR="${1:-./my_irm_model}"
MODEL_NAME="irm-industrial"
GGUF_FILE="$MODEL_DIR/gguf/model-q8_0.gguf"

echo "════════════════════════════════════════"
echo "  Деплой на Industrial Reasoning Model"
echo "════════════════════════════════════════"

# ── 1. Провери дали Ollama е инсталиран ──────────────────────────
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama не е намерен. Инсталирай го:"
    echo "   curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

# ── 2. Провери дали GGUF файлът съществува ───────────────────────
if [ ! -f "$GGUF_FILE" ]; then
    echo "❌ GGUF файлът не е намерен: $GGUF_FILE"
    echo "   Провери пътя или стартирай finetune_unsloth.py отново."
    exit 1
fi

echo "✅ GGUF файл намерен: $GGUF_FILE"

# ── 3. Създай Modelfile ──────────────────────────────────────────
MODELFILE="$MODEL_DIR/Modelfile"

# Използваме променлива за системния промпт за по-лесна промяна
SYSTEM_PROMPT="Ти си специализиран асистент за управление на производствени процеси. Анализираш параметри, диагностицираш откази и даваш технически препоръки за оптимизация на процеси."

cat > "$MODELFILE" << EOF
# Ollama Modelfile за Industrial Reasoning Model
FROM $GGUF_FILE

# Системен промпт
SYSTEM """$SYSTEM_PROMPT"""

# Параметри на генерацията
PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1
PARAMETER stop "<|eot_id|>"
PARAMETER stop "<|end_of_text|>"
EOF

echo "✅ Modelfile създаден: $MODELFILE"

# ── 4. Импортирай модела в Ollama ────────────────────────────────
echo ""
echo "🔄 Импортиране в Ollama (може да отнеме 1-2 минути)..."
ollama create "$MODEL_NAME" -f "$MODELFILE"

if [ $? -ne 0 ]; then
    echo "❌ Грешка при импортиране. Провери Ollama logs: journalctl -u ollama"
    exit 1
fi

echo ""
echo "✅ Моделът е импортиран успешно като: $MODEL_NAME"

# ── 5. Тестов въпрос ─────────────────────────────────────────────
echo ""
echo "🧪 Тестов въпрос към модела..."
echo "────────────────────────────────────────"

ollama run "$MODEL_NAME" \
    "Компресорът на линия 3 показва температура 98°C при нормална работна граница 85°C. Какви са вероятните причини и какво трябва да направя?"

echo "────────────────────────────────────────"

# ── 6. API информация ─────────────────────────────────────────────
echo ""
echo "🌐 REST API е достъпен на: http://localhost:11434"
echo ""
echo "Примерна заявка от Python:"
echo '──────────────────────────────────────────'
cat << 'PYEXAMPLE'
import requests, json

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "irm-industrial",
        "prompt": "Температурата на котела надвишава 95°C. Анализирай.",
        "stream": False
    }
)
print(response.json()["response"])
PYEXAMPLE
echo '──────────────────────────────────────────'
echo ""
echo "🎉 Industrial Reasoning Model е готов за производствена употреба!"
echo "   Стартирай интерактивно: ollama run $MODEL_NAME"
