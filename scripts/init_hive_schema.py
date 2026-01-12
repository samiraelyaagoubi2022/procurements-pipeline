#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
init_hive_schema.py
===================
Initialise le schéma Hive avant l'exécution du pipeline
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils.presto_client import PrestoClient
from utils.logger import setup_logger

logger = setup_logger('init_hive')


def init_hive_schema():
    """Initialise le schéma Hive default"""
    
    logger.info("=" * 80)
    logger.info("🔧 INITIALISATION DU SCHÉMA HIVE")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        # Connexion à Trino
        logger.info("🔌 Connexion à Trino...")
        client = PrestoClient(
            host=os.getenv('TRINO_HOST', 'trino'),
            port=int(os.getenv('TRINO_PORT', 8080))
        )
        
        if not client.test_connection():
            logger.error("❌ Impossible de se connecter à Trino")
            return False
        
        logger.info("✅ Connecté à Trino")
        logger.info("")
        
        # Vérifier si le schéma existe
        logger.info("🔍 Vérification du schéma 'default'...")
        
        try:
            result = client.fetch_all("SHOW SCHEMAS FROM hive")
            schemas = [row[0] for row in result]
            logger.info(f"   Schémas existants : {', '.join(schemas)}")
            
            if 'default' in schemas:
                logger.info("   ✅ Schéma 'default' déjà présent")
            else:
                logger.info("   ℹ️  Schéma 'default' absent, création...")
                
                # Créer le schéma default
                client.execute("CREATE SCHEMA IF NOT EXISTS hive.default")
                logger.info("   ✅ Schéma 'default' créé")
        
        except Exception as e:
            logger.warning(f"   ⚠️  Erreur vérification schémas : {e}")
            logger.info("   Tentative de création directe...")
            
            try:
                client.execute("CREATE SCHEMA IF NOT EXISTS hive.default")
                logger.info("   ✅ Schéma 'default' créé")
            except Exception as e2:
                logger.error(f"   ❌ Impossible de créer le schéma : {e2}")
                return False
        
        logger.info("")
        
        # Vérifier que le schéma est accessible
        logger.info("🔍 Vérification de l'accès au schéma...")
        try:
            result = client.fetch_all("SHOW TABLES FROM hive.default")
            logger.info(f"   ✅ Schéma accessible ({len(result)} tables)")
        except Exception as e:
            logger.error(f"   ❌ Schéma inaccessible : {e}")
            return False
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ INITIALISATION TERMINÉE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("📌 Le pipeline peut maintenant s'exécuter")
        logger.info("")
        
        client.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation : {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Point d'entrée"""
    success = init_hive_schema()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()