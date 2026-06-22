#!/usr/bin/env python3
"""
Enterprise Restore Script for ICAP v8.9.5 Enterprise
==================================================
Restore script for enterprise data including database, audit logs, tenant data, and configuration.
"""

import os
import sys
import shutil
import sqlite3
import json
import datetime
import tarfile
from pathlib import Path
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('restore.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnterpriseRestore:
    """Enterprise restore manager for ICAP."""
    
    def __init__(self, base_dir: str = None):
        """Initialize restore manager."""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.backup_dir = self.base_dir / "backups"
        
        # Paths to restore
        self.db_path = self.base_dir / "icap.db"
        self.env_path = self.base_dir / ".env"
        self.audit_logs_path = self.base_dir / "AuditTrail"
        self.rag_path = self.base_dir / "RAG"
        self.config_path = self.base_dir / "config"
        
    def list_backups(self) -> List[Path]:
        """List available backups."""
        backups = sorted(
            self.backup_dir.glob("icap_enterprise_backup_*.tar.gz"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        return backups
    
    def select_backup(self, backup_name: str = None) -> Path:
        """Select backup to restore."""
        backups = self.list_backups()
        
        if not backups:
            logger.error("No backups found")
            return None
        
        if backup_name:
            backup_path = self.backup_dir / backup_name
            if backup_path.exists():
                return backup_path
            else:
                logger.error(f"Backup not found: {backup_name}")
                return None
        
        # Interactive selection
        print("\nAvailable backups:")
        for i, backup in enumerate(backups, 1):
            size_mb = backup.stat().st_size / (1024 * 1024)
            mtime = datetime.datetime.fromtimestamp(backup.stat().st_mtime)
            print(f"{i}. {backup.name} ({size_mb:.2f} MB, {mtime})")
        
        selection = input("\nSelect backup number (or 'q' to quit): ")
        if selection.lower() == 'q':
            return None
        
        try:
            index = int(selection) - 1
            if 0 <= index < len(backups):
                return backups[index]
        except ValueError:
            pass
        
        logger.error("Invalid selection")
        return None
    
    def extract_backup(self, backup_path: Path) -> Path:
        """Extract backup archive."""
        try:
            logger.info(f"Extracting backup: {backup_path.name}")
            
            extract_path = self.backup_dir / backup_path.stem
            extract_path.mkdir(exist_ok=True)
            
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(extract_path)
            
            logger.info("Backup extracted successfully")
            return extract_path
            
        except Exception as e:
            logger.error(f"Backup extraction failed: {e}")
            return None
    
    def read_manifest(self, extract_path: Path) -> Dict:
        """Read backup manifest."""
        try:
            manifest_path = extract_path / "backup_manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to read manifest: {e}")
            return {}
    
    def restore_database(self, extract_path: Path, force: bool = False) -> bool:
        """Restore database from backup."""
        try:
            backup_db_path = extract_path / "icap.db"
            
            if not backup_db_path.exists():
                logger.warning("Database backup not found, skipping")
                return True
            
            logger.info("Restoring database...")
            
            # Check if database exists
            if self.db_path.exists() and not force:
                response = input(f"Database file exists at {self.db_path}. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Database restore skipped")
                    return True
            
            # Create backup of existing database
            if self.db_path.exists():
                backup_existing = self.db_path.with_suffix(f".db.backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copy2(self.db_path, backup_existing)
                logger.info(f"Existing database backed up to: {backup_existing}")
            
            # Restore database
            shutil.copy2(backup_db_path, self.db_path)
            
            logger.info("Database restore completed")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def restore_audit_logs(self, extract_path: Path, force: bool = False) -> bool:
        """Restore audit logs from backup."""
        try:
            backup_audit_path = extract_path / "AuditTrail"
            
            if not backup_audit_path.exists():
                logger.info("Audit logs backup not found, skipping")
                return True
            
            logger.info("Restoring audit logs...")
            
            # Check if audit logs directory exists
            if self.audit_logs_path.exists() and not force:
                response = input(f"Audit logs directory exists at {self.audit_logs_path}. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Audit logs restore skipped")
                    return True
            
            # Create backup of existing audit logs
            if self.audit_logs_path.exists():
                backup_existing = self.audit_logs_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copytree(self.audit_logs_path, backup_existing)
                logger.info(f"Existing audit logs backed up to: {backup_existing}")
            
            # Restore audit logs
            if self.audit_logs_path.exists():
                shutil.rmtree(self.audit_logs_path)
            shutil.copytree(backup_audit_path, self.audit_logs_path)
            
            logger.info("Audit logs restore completed")
            return True
            
        except Exception as e:
            logger.error(f"Audit logs restore failed: {e}")
            return False
    
    def restore_rag_index(self, extract_path: Path, force: bool = False) -> bool:
        """Restore RAG index from backup."""
        try:
            backup_rag_path = extract_path / "RAG"
            
            if not backup_rag_path.exists():
                logger.info("RAG index backup not found, skipping")
                return True
            
            logger.info("Restoring RAG index...")
            
            # Check if RAG directory exists
            if self.rag_path.exists() and not force:
                response = input(f"RAG directory exists at {self.rag_path}. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    logger.info("RAG index restore skipped")
                    return True
            
            # Create backup of existing RAG index
            if self.rag_path.exists():
                backup_existing = self.rag_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                shutil.copytree(self.rag_path, backup_existing)
                logger.info(f"Existing RAG index backed up to: {backup_existing}")
            
            # Restore RAG index
            if self.rag_path.exists():
                shutil.rmtree(self.rag_path)
            shutil.copytree(backup_rag_path, self.rag_path)
            
            logger.info("RAG index restore completed")
            return True
            
        except Exception as e:
            logger.error(f"RAG index restore failed: {e}")
            return False
    
    def restore_configuration(self, extract_path: Path, force: bool = False) -> bool:
        """Restore configuration files from backup."""
        try:
            logger.info("Restoring configuration...")
            
            # Restore .env file
            backup_env_path = extract_path / ".env"
            if backup_env_path.exists():
                if self.env_path.exists() and not force:
                    response = input(f".env file exists at {self.env_path}. Overwrite? (y/N): ")
                    if response.lower() != 'y':
                        logger.info(".env restore skipped")
                    else:
                        backup_existing = self.env_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copy2(self.env_path, backup_existing)
                        shutil.copy2(backup_env_path, self.env_path)
                        logger.info(".env restored")
                else:
                    if self.env_path.exists():
                        backup_existing = self.env_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copy2(self.env_path, backup_existing)
                    shutil.copy2(backup_env_path, self.env_path)
                    logger.info(".env restored")
            
            # Restore config directory
            backup_config_path = extract_path / "config"
            if backup_config_path.exists():
                if self.config_path.exists() and not force:
                    response = input(f"Config directory exists at {self.config_path}. Overwrite? (y/N): ")
                    if response.lower() != 'y':
                        logger.info("Config restore skipped")
                    else:
                        if self.config_path.exists():
                            backup_existing = self.config_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                            shutil.copytree(self.config_path, backup_existing)
                        shutil.copytree(backup_config_path, self.config_path)
                        logger.info("Config restored")
                else:
                    if self.config_path.exists():
                        backup_existing = self.config_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copytree(self.config_path, backup_existing)
                    shutil.copytree(backup_config_path, self.config_path)
                    logger.info("Config restored")
            
            # Restore nginx configuration
            backup_nginx_path = extract_path / "nginx"
            if backup_nginx_path.exists():
                nginx_path = self.base_dir / "nginx"
                if nginx_path.exists() and not force:
                    response = input(f"Nginx directory exists at {nginx_path}. Overwrite? (y/N): ")
                    if response.lower() != 'y':
                        logger.info("Nginx restore skipped")
                    else:
                        if nginx_path.exists():
                            backup_existing = nginx_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                            shutil.copytree(nginx_path, backup_existing)
                        shutil.copytree(backup_nginx_path, nginx_path)
                        logger.info("Nginx restored")
                else:
                    if nginx_path.exists():
                        backup_existing = nginx_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copytree(nginx_path, backup_existing)
                    shutil.copytree(backup_nginx_path, nginx_path)
                    logger.info("Nginx restored")
            
            # Restore k8s configuration
            backup_k8s_path = extract_path / "k8s"
            if backup_k8s_path.exists():
                k8s_path = self.base_dir / "k8s"
                if k8s_path.exists() and not force:
                    response = input(f"K8s directory exists at {k8s_path}. Overwrite? (y/N): ")
                    if response.lower() != 'y':
                        logger.info("K8s restore skipped")
                    else:
                        if k8s_path.exists():
                            backup_existing = k8s_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                            shutil.copytree(k8s_path, backup_existing)
                        shutil.copytree(backup_k8s_path, k8s_path)
                        logger.info("K8s restored")
                else:
                    if k8s_path.exists():
                        backup_existing = k8s_path.with_suffix(f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copytree(k8s_path, backup_existing)
                    shutil.copytree(backup_k8s_path, k8s_path)
                    logger.info("K8s restored")
            
            logger.info("Configuration restore completed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration restore failed: {e}")
            return False
    
    def verify_restore(self, extract_path: Path) -> bool:
        """Verify restore by checking critical files."""
        try:
            logger.info("Verifying restore...")
            
            issues = []
            
            # Check database
            if self.db_path.exists():
                try:
                    conn = sqlite3.connect(str(self.db_path))
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM measurements")
                    cursor.fetchone()
                    conn.close()
                    logger.info("Database verification passed")
                except Exception as e:
                    issues.append(f"Database verification failed: {e}")
            else:
                issues.append("Database file not found")
            
            # Check configuration
            if self.env_path.exists():
                logger.info("Configuration verification passed")
            else:
                issues.append("Configuration file not found")
            
            if issues:
                logger.warning("Restore verification issues:")
                for issue in issues:
                    logger.warning(f"  - {issue}")
                return False
            else:
                logger.info("Restore verification passed")
                return True
            
        except Exception as e:
            logger.error(f"Restore verification failed: {e}")
            return False
    
    def cleanup_extract(self, extract_path: Path) -> bool:
        """Clean up extracted backup directory."""
        try:
            logger.info("Cleaning up extracted backup...")
            shutil.rmtree(extract_path)
            logger.info("Cleanup completed")
            return True
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return False
    
    def perform_restore(self, backup_name: str = None, force: bool = False, 
                       components: List[str] = None) -> bool:
        """Perform full enterprise restore."""
        logger.info("=" * 60)
        logger.info("Starting Enterprise Restore")
        logger.info("=" * 60)
        
        # Select backup
        backup_path = self.select_backup(backup_name)
        if not backup_path:
            logger.error("No backup selected")
            return False
        
        # Extract backup
        extract_path = self.extract_backup(backup_path)
        if not extract_path:
            logger.error("Backup extraction failed")
            return False
        
        # Read manifest
        manifest = self.read_manifest(extract_path)
        if manifest:
            logger.info(f"Backup version: {manifest.get('version', 'Unknown')}")
            logger.info(f"Backup timestamp: {manifest.get('timestamp', 'Unknown')}")
        
        # Default to all components if not specified
        if components is None:
            components = ["database", "audit_logs", "rag_index", "configuration"]
        
        results = []
        
        # Restore components
        if "database" in components:
            results.append(("Database", self.restore_database(extract_path, force)))
        
        if "audit_logs" in components:
            results.append(("Audit Logs", self.restore_audit_logs(extract_path, force)))
        
        if "rag_index" in components:
            results.append(("RAG Index", self.restore_rag_index(extract_path, force)))
        
        if "configuration" in components:
            results.append(("Configuration", self.restore_configuration(extract_path, force)))
        
        # Verify restore
        results.append(("Verification", self.verify_restore(extract_path)))
        
        # Cleanup
        results.append(("Cleanup", self.cleanup_extract(extract_path)))
        
        # Summary
        logger.info("=" * 60)
        logger.info("Restore Summary")
        logger.info("=" * 60)
        
        for component, success in results:
            status = "✓ SUCCESS" if success else "✗ FAILED"
            logger.info(f"{component:25s}: {status}")
        
        all_success = all(success for _, success in results)
        
        if all_success:
            logger.info("Restore completed successfully")
            logger.info("Please restart the ICAP service")
        else:
            logger.error("Restore completed with errors")
        
        return all_success

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ICAP Enterprise Restore Script")
    parser.add_argument("--backup", type=str, help="Backup name to restore")
    parser.add_argument("--force", action="store_true", help="Force overwrite without prompts")
    parser.add_argument("--components", type=str, nargs='+', 
                       choices=["database", "audit_logs", "rag_index", "configuration"],
                       help="Components to restore (default: all)")
    parser.add_argument("--dir", type=str, help="Base directory (default: parent of scripts)")
    
    args = parser.parse_args()
    
    restore_manager = EnterpriseRestore(args.dir)
    success = restore_manager.perform_restore(
        backup_name=args.backup,
        force=args.force,
        components=args.components
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
