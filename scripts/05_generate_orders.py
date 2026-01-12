#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
05_generate_orders.py
=====================
Génération des fichiers de commande par fournisseur - Version corrigée
"""

import sys
import os
import argparse
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from utils.logger import setup_logger, log_step
from utils.postgres_client import PostgresClient

logger = setup_logger('generate_orders')

@log_step("Génération des commandes fournisseurs")
def generate_orders(execution_date):
    """
    Génère les fichiers de commande par fournisseur
    """
    
    logger.info(f"📝 Génération pour la date: {execution_date}")
    logger.info("")
    
    # Chemins
    base_dir = Path.cwd()
    demand_file = base_dir / 'data' / 'processed' / f'net_demand_{execution_date}.csv'
    output_dir = base_dir / 'output' / 'supplier_orders' / execution_date
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Charger la demande nette
    logger.info("📂 Chargement de la demande nette...")
    demand_df = pd.read_csv(demand_file)
    logger.info(f"   ✓ {len(demand_df)} lignes chargées")
    logger.info("")
    
    # Connexion PostgreSQL pour récupérer les infos supplémentaires
    logger.info("📂 Chargement des fournisseurs...")
    try:
        pg = PostgresClient(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            database=os.getenv('POSTGRES_DB', 'procurement_db'),
            user=os.getenv('POSTGRES_USER', 'procurement_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'procurement_pass')
        )
        
        # Charger les fournisseurs
        suppliers_df = pg.fetch_dataframe(
            "SELECT supplier_id, supplier_name, contact_email, contact_phone, lead_time_days FROM suppliers WHERE is_active = TRUE"
        )
        logger.info(f"   ✓ {len(suppliers_df)} fournisseurs")
        logger.info("")
        
        # Charger les infos produits (pack_size, moq)
        products_df = pg.fetch_dataframe(
            "SELECT sku, pack_size, moq, unit_of_measure FROM products WHERE is_active = TRUE"
        )
        
        # Joindre avec la demande pour avoir pack_size et moq
        demand_df = demand_df.merge(
            products_df[['sku', 'pack_size', 'moq', 'unit_of_measure']], 
            on='sku', 
            how='left'
        )
        
        # Valeurs par défaut si manquantes
        demand_df['pack_size'] = demand_df['pack_size'].fillna(1).astype(int)
        demand_df['moq'] = demand_df['moq'].fillna(1).astype(int)
        demand_df['unit_of_measure'] = demand_df['unit_of_measure'].fillna('pièce')
        
    except Exception as e:
        logger.warning(f"   ⚠️ Erreur PostgreSQL: {e}")
        logger.info("   Utilisation de valeurs par défaut")
        
        # Créer un DataFrame de fournisseurs minimal
        suppliers_df = pd.DataFrame({
            'supplier_id': demand_df['supplier_id'].unique(),
            'supplier_name': ['Fournisseur ' + str(i) for i in range(len(demand_df['supplier_id'].unique()))],
            'contact_email': ['contact@supplier.ma'] * len(demand_df['supplier_id'].unique()),
            'contact_phone': ['+212522000000'] * len(demand_df['supplier_id'].unique()),
            'lead_time_days': [2] * len(demand_df['supplier_id'].unique())
        })
        
        # Ajouter les colonnes manquantes avec valeurs par défaut
        demand_df['pack_size'] = 1
        demand_df['moq'] = 1
        demand_df['unit_of_measure'] = 'pièce'
    
    # Générer un fichier par fournisseur
    logger.info("📄 Génération des fichiers par fournisseur...")
    logger.info("")
    
    total_orders = 0
    total_value = 0.0
    
    for supplier_id in demand_df['supplier_id'].unique():
        # Filtrer les produits de ce fournisseur
        supplier_demand = demand_df[demand_df['supplier_id'] == supplier_id].copy()
        
        if len(supplier_demand) == 0:
            continue
        
        # Trouver les infos du fournisseur
        supplier_info = suppliers_df[suppliers_df['supplier_id'] == supplier_id]
        
        if len(supplier_info) == 0:
            logger.warning(f"   ⚠️ Fournisseur {supplier_id} introuvable")
            continue
        
        supplier_name = supplier_info.iloc[0]['supplier_name']
        
        # Créer le fichier de commande
        order_items = []
        
        for _, row in supplier_demand.iterrows():
            order_items.append({
                'sku': row['sku'],
                'product_name': row['product_name'],
                'category': row['category'],
                'quantity_ordered': int(row['final_order_qty']),
                'pack_size': int(row['pack_size']),
                'moq': int(row['moq']),
                'unit_price': float(row['unit_price']),
                'line_total': float(row['order_value']),
                'unit_of_measure': row['unit_of_measure']
            })
        
        # Créer le DataFrame de commande
        order_df = pd.DataFrame(order_items)
        
        # Nom de fichier sécurisé
        safe_supplier_name = supplier_name.replace(' ', '_').replace('/', '_')
        output_file = output_dir / f'ORDER_{supplier_id}_{safe_supplier_name}_{execution_date}.csv'
        
        # Sauvegarder
        order_df.to_csv(output_file, index=False)
        
        order_total = order_df['line_total'].sum()
        total_orders += 1
        total_value += order_total
        
        logger.info(f"   ✓ {supplier_id} - {supplier_name}")
        logger.info(f"      • {len(order_df)} produits")
        logger.info(f"      • {order_total:,.2f} MAD")
        logger.info(f"      • {output_file.name}")
        logger.info("")
    
    # Résumé
    logger.info("📊 RÉSUMÉ:")
    logger.info(f"   • Commandes générées: {total_orders}")
    logger.info(f"   • Valeur totale: {total_value:,.2f} MAD")
    logger.info(f"   • Répertoire: {output_dir}")
    logger.info("")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Génération des commandes fournisseurs - Version corrigée'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=datetime.now().strftime('%Y-%m-%d'),
        help='Date d\'exécution (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    try:
        generate_orders(args.date)
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()