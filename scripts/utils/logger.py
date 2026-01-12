#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
logger.py
=========
Système de logging pour le pipeline
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from functools import wraps
import time


class ColoredFormatter(logging.Formatter):
    """Formatter avec couleurs pour la console"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Vert
        'WARNING': '\033[33m',  # Jaune
        'ERROR': '\033[31m',    # Rouge
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname:8s}{self.COLORS['RESET']}"
            )
        return super().format(record)


def setup_logger(name='pipeline', log_dir='logs', log_level=logging.INFO):
    """
    Configure le système de logging
    
    Args:
        name: Nom du logger
        log_dir: Répertoire des logs
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logger configuré
    """
    # Créer le répertoire de logs
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Nom du fichier de log avec date
    log_file = log_path / f"pipeline_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # Créer le logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Éviter les handlers dupliqués
    if logger.handlers:
        return logger
    
    # Format des messages
    log_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Handler pour le fichier
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    
    # Handler pour la console avec couleurs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColoredFormatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    
    # Ajouter les handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_step(step_name):
    """
    Décorateur pour logger l'exécution d'une étape
    
    Usage:
        @log_step("Chargement des données")
        def load_data():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('pipeline')
            
            logger.info("=" * 60)
            logger.info(f"DÉBUT: {step_name}")
            logger.info("=" * 60)
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                
                elapsed = time.time() - start_time
                logger.info("-" * 60)
                logger.info(f"✅ SUCCESS: {step_name}")
                logger.info(f"⏱️  Durée: {elapsed:.2f}s")
                logger.info("=" * 60)
                logger.info("")
                
                return result
                
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error("-" * 60)
                logger.error(f"❌ ERREUR: {step_name}")
                logger.error(f"⏱️  Durée: {elapsed:.2f}s")
                logger.error(f"💥 Exception: {str(e)}")
                logger.error("=" * 60)
                logger.error("", exc_info=True)
                raise
        
        return wrapper
    return decorator


class StepLogger:
    """
    Context manager pour logger une étape avec progression
    
    Usage:
        with StepLogger("Traitement des données") as step:
            step.info("Chargement...")
            # ... traitement ...
            step.success("Traité 1000 lignes")
    """
    
    def __init__(self, step_name, logger_name='pipeline'):
        self.step_name = step_name
        self.logger = logging.getLogger(logger_name)
        self.start_time = None
    
    def __enter__(self):
        self.logger.info("=" * 60)
        self.logger.info(f"DÉBUT: {self.step_name}")
        self.logger.info("=" * 60)
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info("-" * 60)
            self.logger.info(f"✅ SUCCESS: {self.step_name}")
            self.logger.info(f"⏱️  Durée: {elapsed:.2f}s")
            self.logger.info("=" * 60)
            self.logger.info("")
        else:
            self.logger.error("-" * 60)
            self.logger.error(f"❌ ERREUR: {self.step_name}")
            self.logger.error(f"⏱️  Durée: {elapsed:.2f}s")
            self.logger.error(f"💥 Exception: {str(exc_val)}")
            self.logger.error("=" * 60)
            self.logger.error("", exc_info=True)
        
        return False  # Propage l'exception
    
    def info(self, message):
        """Log un message d'information"""
        self.logger.info(f"   {message}")
    
    def success(self, message):
        """Log un message de succès"""
        self.logger.info(f"   ✅ {message}")
    
    def warning(self, message):
        """Log un avertissement"""
        self.logger.warning(f"   ⚠️  {message}")
    
    def error(self, message):
        """Log une erreur"""
        self.logger.error(f"   ❌ {message}")
    
    def debug(self, message):
        """Log un message de debug"""
        self.logger.debug(f"   🔍 {message}")


# Exemple d'utilisation
if __name__ == '__main__':
    # Test du logger
    logger = setup_logger('test', log_level=logging.DEBUG)
    
    logger.debug("Ceci est un message de debug")
    logger.info("Ceci est un message d'information")
    logger.warning("Ceci est un avertissement")
    logger.error("Ceci est une erreur")
    
    print("\n--- Test du décorateur ---\n")
    
    @log_step("Test du décorateur")
    def test_function():
        time.sleep(1)
        logger.info("Traitement en cours...")
        return "OK"
    
    result = test_function()
    
    print("\n--- Test du context manager ---\n")
    
    with StepLogger("Test du context manager") as step:
        step.info("Étape 1")
        time.sleep(0.5)
        step.success("Étape 1 terminée")
        step.info("Étape 2")
        time.sleep(0.5)
        step.success("Étape 2 terminée")