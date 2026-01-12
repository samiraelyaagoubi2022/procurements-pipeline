#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
orchestrator.py
===============

Orchestrateur principal du pipeline de procurement
Région: Casablanca, Maroc
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Ajouter le répertoire courant au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from utils.logger import setup_logger, StepLogger

# Configuration du logger
logger = setup_logger('orchestrator', log_level='INFO')


class PipelineOrchestrator:
    """Orchestrateur du pipeline de procurement"""

    def __init__(self, execution_date, num_orders=500, verbose=False):
        self.execution_date = execution_date
        self.num_orders = num_orders
        self.verbose = verbose
        self.scripts_dir = Path(__file__).parent.resolve()

        logger.info("=" * 80)
        logger.info("🇲🇦  PIPELINE DE PROCUREMENT - RÉGION DE CASABLANCA")
        logger.info("=" * 80)
        logger.info(f"📅 Date d'exécution: {self.execution_date}")
        logger.info(f"📦 Nombre de commandes: {self.num_orders}")
        logger.info(f"📁 Répertoire scripts: {self.scripts_dir}")
        logger.info("=" * 80)
        logger.info("")

    def run_script(self, script_name, *args):
        """Exécute un script Python avec capture des logs"""
        script_path = self.scripts_dir / script_name

        if not script_path.exists():
            logger.error(f"❌ Script introuvable: {script_path}")
            return False

        # Utiliser l'exécutable Python actuel
        cmd = [sys.executable, str(script_path), '--date', self.execution_date]

        if args:
            cmd.extend(args)

        if self.verbose and '--verbose' not in cmd:
            cmd.append('--verbose')

        logger.info(f"🚀 Exécution: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if result.stdout:
                for line in result.stdout.splitlines():
                    if line.strip():
                        logger.info(f"   {line}")

            logger.info(f"✅ Script terminé: {script_name}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erreur lors de l'exécution de {script_name}")
            logger.error(f"   Code de retour: {e.returncode}")

            if e.stdout:
                logger.error("   STDOUT:")
                for line in e.stdout.splitlines():
                    if line.strip():
                        logger.error(f"   {line}")

            if e.stderr:
                logger.error("   STDERR:")
                for line in e.stderr.splitlines():
                    if line.strip():
                        logger.error(f"   {line}")

            return False

    # -------------------- Étapes du pipeline --------------------
    def run_step_01_generate_data(self):
        with StepLogger("ÉTAPE 1/6 - Génération des données") as step:
            step.info(f"Génération de {self.num_orders} commandes et snapshots de stock...")
            success = self.run_script('01_generate_data.py', '--num-orders', str(self.num_orders))
            if success:
                step.success("Données générées avec succès")
            else:
                step.error("Échec de la génération des données")
            return success

    def run_step_02_aggregate_orders(self):
        with StepLogger("ÉTAPE 2/6 - Agrégation des commandes") as step:
            step.info("Agrégation des commandes par SKU avec Presto...")
            success = self.run_script('03_aggregate_orders.py')
            if success:
                step.success("Commandes agrégées")
            else:
                step.error("Échec de l'agrégation")
            return success

    def run_step_03_ingest_to_hdfs(self):
        with StepLogger("ÉTAPE 3/6 - Ingestion vers HDFS") as step:
            step.info("Copie des fichiers vers HDFS...")
            success = self.run_script('02_ingest_to_hdfs.py')
            if success:
                step.success("Fichiers ingérés dans HDFS")
            else:
                step.error("Échec de l'ingestion")
            return success

    def run_step_04_calculate_demand(self):
        with StepLogger("ÉTAPE 4/6 - Calcul de la demande nette") as step:
            step.info("Calcul de la demande avec stock de sécurité...")
            success = self.run_script('04_calculate_demand.py')
            if success:
                step.success("Demande calculée")
            else:
                step.error("Échec du calcul")
            return success

    def run_step_05_generate_orders(self):
        with StepLogger("ÉTAPE 5/6 - Génération des commandes fournisseurs") as step:
            step.info("Création des fichiers de commandes par fournisseur...")
            success = self.run_script('05_generate_orders.py')
            if success:
                step.success("Commandes fournisseurs générées")
            else:
                step.error("Échec de la génération")
            return success

    def run_step_06_check_exceptions(self):
        with StepLogger("ÉTAPE 6/6 - Vérification des exceptions") as step:
            step.info("Analyse des anomalies et exceptions...")
            success = self.run_script('06_check_exceptions.py')
            if success:
                step.success("Exceptions vérifiées")
            else:
                step.error("Échec de la vérification")
            return success

    # -------------------- Pipeline complet --------------------
    def run_pipeline(self):
        start_time = datetime.now()
        logger.info("\n🚀 DÉMARRAGE DU PIPELINE COMPLET\n")

        # ORDRE CORRIGÉ: Agrégation AVANT ingestion HDFS
        steps = [
            ("01", self.run_step_01_generate_data),
            ("02", self.run_step_02_aggregate_orders),      # Déplacé avant HDFS
            ("03", self.run_step_03_ingest_to_hdfs),        # Déplacé après agrégation
            ("04", self.run_step_04_calculate_demand),
            ("05", self.run_step_05_generate_orders),
            ("06", self.run_step_06_check_exceptions)
        ]

        for step_num, step_func in steps:
            step_start = datetime.now()
            success = step_func()
            step_end = datetime.now()
            duration = (step_end - step_start).total_seconds()
            logger.info(f"⏱️ Durée étape {step_num}: {duration:.2f}s\n")

            if not success:
                logger.error("\n" + "=" * 80)
                logger.error(f"❌ PIPELINE INTERROMPU À L'ÉTAPE {step_num}")
                logger.error("=" * 80)
                return False

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        logger.info("=" * 80)
        logger.info("✅ PIPELINE TERMINÉ AVEC SUCCÈS")
        logger.info("=" * 80)
        logger.info(f"⏱️  Durée totale: {total_duration:.2f} secondes")
        logger.info(f"📅 Date d'exécution: {self.execution_date}")
        logger.info(f"📦 Commandes traitées: {self.num_orders}")
        logger.info(f"🕐 Heure de fin: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80 + "\n")
        return True


# -------------------- CLI --------------------
def main():
    parser = argparse.ArgumentParser(
        description='Orchestrateur du pipeline de procurement - Casablanca',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  # Pipeline complet avec 500 commandes (défaut)
  python orchestrator.py --date 2026-03-18
  
  # Pipeline avec 10,000 commandes pour tester le partitionnement HDFS
  python orchestrator.py --date 2026-03-18 --num-orders 10000
  
  # Exécuter seulement l'étape de génération avec 50,000 commandes
  python orchestrator.py --date 2026-03-18 --num-orders 50000 --step 01
  
  # Pipeline complet en mode verbeux
  python orchestrator.py --date 2026-03-18 --num-orders 5000 --verbose
        """
    )
    parser.add_argument(
        '--date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Date d\'exécution (format: YYYY-MM-DD, défaut: aujourd\'hui)'
    )
    parser.add_argument(
        '--num-orders',
        type=int,
        default=500,
        help='Nombre de commandes à générer (défaut: 500, recommandé: 10000+ pour voir le partitionnement)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Active le mode verbeux avec logs détaillés'
    )
    parser.add_argument(
        '--step',
        type=str,
        choices=['01', '02', '03', '04', '05', '06', 'all'],
        default='all',
        help='Étape à exécuter (01=génération, 02=agrégation, 03=HDFS, 04=demande, 05=commandes, 06=exceptions, all=toutes)'
    )

    args = parser.parse_args()

    # Validation de la date
    try:
        datetime.strptime(args.date, '%Y-%m-%d')
    except ValueError:
        logger.error(f"❌ Format de date invalide: {args.date}")
        logger.error("   Format attendu: YYYY-MM-DD (exemple: 2026-03-18)")
        sys.exit(1)

    # Validation du nombre de commandes
    if args.num_orders < 1:
        logger.error(f"❌ Le nombre de commandes doit être >= 1 (reçu: {args.num_orders})")
        sys.exit(1)

    if args.num_orders > 100000:
        logger.warning(f"⚠️  Nombre de commandes élevé ({args.num_orders})")
        logger.warning("   Le traitement peut prendre plusieurs minutes...")

    orchestrator = PipelineOrchestrator(args.date, args.num_orders, args.verbose)

    if args.step == 'all':
        success = orchestrator.run_pipeline()
    else:
        step_map = {num: func for num, func in [
            ('01', orchestrator.run_step_01_generate_data),
            ('02', orchestrator.run_step_02_aggregate_orders),
            ('03', orchestrator.run_step_03_ingest_to_hdfs),
            ('04', orchestrator.run_step_04_calculate_demand),
            ('05', orchestrator.run_step_05_generate_orders),
            ('06', orchestrator.run_step_06_check_exceptions)
        ]}
        success = step_map[args.step]()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()