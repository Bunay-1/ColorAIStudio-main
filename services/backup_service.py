"""
ICAP Enterprise Backup Service (v8.5.0)
======================================
Управлява архивирането на критични данни: Audit Trail, База Знания и Конфигурации.
"""

import os
import shutil
import time
import zipfile
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BackupService")

class BackupService:
    def __init__(self, backup_dir="Backups"):
        self.backup_dir = backup_dir
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

    def create_full_backup(self):
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"icap_backup_{timestamp}.zip")

        targets = ["AuditTrail", "RAG", "qdrant_db", "clients.json", "model_registry.json"]

        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for target in targets:
                    if os.path.isdir(target):
                        for root, dirs, files in os.walk(target):
                            for file in files:
                                zipf.write(os.path.join(root, file),
                                           os.path.relpath(os.path.join(root, file), os.path.join(target, '..')))
                    elif os.path.exists(target):
                        zipf.write(target)

            logger.info(f"✅ Пълен архив е създаден успешно: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Грешка при създаване на архив: {e}")
            return None

if __name__ == "__main__":
    svc = BackupService()
    svc.create_full_backup()
