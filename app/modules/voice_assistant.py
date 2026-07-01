import os
import time
import logging

# Конфигуриране на логване
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VoiceAssistant")

class VoiceAssistant:
    def __init__(self, model_name=None, lightweight=None):
        self.model = None
        self.enabled = False
        edge_mode = os.environ.get("ICAP_EDGE_MODE", "1") == "1"
        self.lightweight = lightweight if lightweight is not None else edge_mode

        if model_name is None:
            model_name = "tiny" if self.lightweight else "base"

        if edge_mode:
            logger.info(f"EDGE MODE: Voice Assistant (Whisper {model_name}) ще бъде зареден лениво при първа нужда.")
            return

        try:
            import whisper
            import torch
            logger.info(f"Опит за зареждане на Whisper модел ({model_name})...")
            self.model = whisper.load_model(model_name)
            self.enabled = True
            logger.info("Whisper моделът е зареден успешно.")
        except Exception as e:
            logger.error(f"Грешка при зареждане на Voice Assistant (Whisper/Torch): {e}")
            logger.warning("Гласовите функции ще бъдат деактивирани.")

    def transcribe(self, audio_path):
        """Превръща реч в текст (Whisper)."""
        if self.model is None:
            try:
                import whisper
                m_name = "tiny" if self.lightweight else "base"
                logger.info(f"Lazy Loading Whisper ({m_name})...")
                self.model = whisper.load_model(m_name)
                self.enabled = True
            except:
                return "[Гласовото разпознаване е деактивирано]"

        if not self.enabled or self.model is None:
            return "[Гласовото разпознаване е деактивирано поради системна несъвместимост]"

        if not os.path.exists(audio_path):
            return "Файлът не съществува"

        try:
            result = self.model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            logger.error(f"Грешка при транскрипция: {e}")
            return f"[Грешка при обработка на аудио: {e}]"

    def speak(self, text, lang="bg", output_path="response.mp3"):
        """Превръща текст в реч (gTTS)."""
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang=lang)
            tts.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"Грешка при генериране на реч (gTTS): {e}")
            return None

if __name__ == "__main__":
    va = VoiceAssistant()
    print(f"Voice Assistant status: {'Enabled' if va.enabled else 'Disabled'}")
