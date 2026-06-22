#!/usr/bin/env python3
"""
Enterprise Backup Script for ICAP v8.9.5 Enterprise
=================================================
Backup script for enterprise data including database, audit logs, tenant data, and configuration.
"""

import os
import sys
import shutil
import sqlite3
import json
import datetime
import tarfile
import gzip
from pathlib import Path
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnterpriseBackup:
    """Enterprise backup manager for ICAP."""
    
    def __init__(self, base_dir: str = None):
        """Initialize backup manager."""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.backup_dir = self.base_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Paths to backup
        self.db_path = self.base_dir / "icap.db"
        self.env_path = self.base_dir / ".env"
        self.audit_logs_path = self.base_dir / "AuditTrail"
        self.rag_path = self.base_dir / "RAG"
        self.config_path = self.base_dir / "config"
        
    def create_backup_name(self) -> str:
        """Generate backup filename with timestamp."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"icap_enterprise_backup_{timestamp}"
    
    def backup_database(self, backup_path: Path) -> bool:
        """Backup SQLite database."""
        try:
            if not self.db_path.exists():
                logger.warning(f"Database file not found: {self.db_path}")
                return True  # Not an error, just missing
            
            logger.info("Backing up database...")
            
            # Use SQLite backup API for consistent backup
            backup_db_path = backup_path / "icap.db"
            source = sqlite3.connect(str(self.db_path))
            backup = sqlite3.connect(str(backup_db_path))
            
            with backup:
                source.backup(backup)
            
            backup.close()
            source.close()
            
            logger.info("Database backup completed")
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def backup_audit_logs(self, backup_path: Path) -> bool:
        """Backup audit logs."""
        try:
            if not self.audit_logs_path.exists():
                logger.info("No audit logs directory found, skipping")
                return True
            
            logger.info("Backing up audit logs...")
            audit_backup_path = backup_path / "AuditTrail"
            shutil.copytree(self.audit_logs_path, audit_backup_path)
            
            logger.info("Audit logs backup completed")
            return True
            
        except Exception as e:
            logger.error(f"Audit logs backup failed: {e}")
            return False
    
    def backup_rag_index(self, backup_path: Path) -> bool:
        """Backup RAG index."""
        try:
            if not self.rag_path.exists():
                logger.info("No RAG directory found, skipping")
                return True
            
            logger.info("Backing up RAG index...")
            rag_backup_path = backup_path / "RAG"
            shutil.copytree(self.rag_path, rag_backup_path)
            
            logger.info("RAG index backup completed")
            return True
            
        except Exception as e:
            logger.error(f"RAG index backup failed: {e}")
            return False
    
    def backup_configuration(self, backup_path: Path) -> bool:
        """Backup configuration files."""
        try:
            logger.info("Backing up configuration...")
            
            # Backup .env file
            if self.env_path.exists():
                shutil.copy2(self.env_path, backup_path / ".env")
            
            # Backup config directory if exists
            if self.config_path.exists():
                config_backup_path = backup_path / "config"
                shutil.copytree(self.config_path, config_backup_path)
            
            # Backup nginx configuration
            nginx_path = self.base_dir / "nginx"
            if nginx_path.exists():
                nginx_backup_path = backup_path / "nginx"
                shutil.copytree(nginx_path, nginx_backup_path)
            
            # Backup k8s configuration
            k8s_path = self.base_dir / "k8s"
            if k8s_path.exists():
                k8s_backup_path = backup_path / "k8s"
                shutil.copytree(k8s_path, k8s_backup_path)
            
            logger.info("Configuration backup completed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            return False
    
    def backup_encrypted_data(self, backup_path: Path) -> bool:
        """Backup encrypted data keys and metadata."""
        try:
            logger.info("Backing up encryption metadata...")
            
            # Create encryption metadata file
            metadata = {
                "backup_timestamp": datetime.datetime.now().isoformat(),
                "note": "Encryption keys should be backed up separately for security"
            }
            
            metadata_path = backup_path / "encryption_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info("Encryption metadata backup completed")
            return True
            
        except Exception as e:
            logger.error(f"Encryption metadata backup failed: {e}")
            return False
    
    def create_backup_manifest(self, backup_path: Path) -> bool:
        """Create backup manifest with metadata."""
        try:
            logger.info("Creating backup manifest...")
            
            manifest = {
                "backup_name": backup_path.name,
                "timestamp": datetime.datetime.now().isoformat(),
                "version": "8.9.5 Enterprise",
                "components": {
                    "database": (backup_path / "icap.db").exists(),
                    "audit_logs": (backup_path / "AuditTrail").exists(),
                    "rag_index": (backup_path / "RAG").exists(),
                    "configuration": (backup_path / ".env").exists(),
                    "nginx": (backup_path / "nginx").exists(),
                    "k8s": (backup_path / "k8s").exists()
                },
                "file_sizes": {}
            }
            
            # Add file sizes
            for item in backup_path.rglob("*"):
                if item.is_file():
                    manifest["file_sizes"][str(item.relative_to(backup_path))] = item.stat().st_size
            
            manifest_path = backup_path / "backup_manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info("Backup manifest created")
            return True
            
        except Exception as e:
            logger.error(f"Backup manifest creation failed: {e}")
            return False
    
    def compress_backup(self, backup_path: Path) -> bool:
        """Compress backup directory."""
        try:
            logger.info("Compressing backup...")
            
            archive_path = backup_path.parent / f"{backup_path.name}.tar.gz"
            
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(backup_path, arcname=backup_path.name)
            
            # Remove uncompressed directory
            shutil.rmtree(backup_path)
            
            logger.info(f"Backup compressed: {archive_path}")
            logger.info(f"Archive size: {archive_path.stat().st_size / (1024*1024):.2f} MB")
            return True
            
        except Exception as e:
            logger.error(f"Backup compression failed: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 7) -> bool:
        """Remove old backups, keeping only the most recent ones."""
        try:
            logger.info(f"Cleaning up old backups (keeping {keep_count} most recent)...")
            
            # Get all backup archives
            backups = sorted(
                self.backup_dir.glob("icap_enterprise_backup_*.tar.gz"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Remove old backups
            for old_backup in backups[keep_count:]:
                logger.info(f"Removing old backup: {old_backup.name}")
                old_backup.unlink()
            
            logger.info("Backup cleanup completed")
            return True
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return False
    
    def perform_backup(self, compress: bool = True, keep_count: int = 7) -> bool:
        """Perform full enterprise backup."""
        logger.info("=" * 60)
        logger.info("Starting Enterprise Backup")
        logger.info("=" * 60)
        
        backup_name = self.create_backup_name()
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        results = []
        
        # Backup components
        results.append(("Database", self.backup_database(backup_path)))
        results.append(("Audit Logs", self.backup_audit_logs(backup_path)))
        results.append(("RAG Index", self.backup_rag_index(backup_path)))
        results.append(("Configuration", self.backup_configuration(backup_path)))
        results.append(("Encryption Metadata", self.backup_encrypted_data(backup_path)))
        results.append(("Manifest", self.create_backup_manifest(backup_path)))
        
        # Compress if requested
        if compress:
            results.append(("Compression", self.compress_backup(backup_path)))
        
        # Cleanup old backups
        results.append(("Cleanup", self.cleanup_old_backups(keep_count)))
        
        # Summary
        logger.info("=" * 60)
        logger.info("Backup Summary")
        logger.info("=" * 60)
        
        for component, success in results:
            status = "✓ SUCCESS" if success else "✗ FAILED"
            logger.info(f"{component:25s}: {status}")
        
        all_success = all(success for _, success in results)
        
        if all_success:
            logger.info("Backup completed successfully")
        else:
            logger.error("Backup completed with errors")
        
        return all_success

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ICAP Enterprise Backup Script")
    parser.add_argument("--no-compress", action="store_true", help="Skip compression")
    parser.add_argument("--keep", type=int, default=7, help="Number of backups to keep")
    parser.add_argument("--dir", type=str, help="Base directory (default: parent of scripts)")
    
    args = parser.parse_args()
    
    backup_manager = EnterpriseBackup(args.dir)
    success = backup_manager.perform_backup(
        compress=not args.no_compress,
        keep_count=args.keep
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
