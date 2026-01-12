#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
06_check_exceptions.py
======================
Vérification des exceptions et anomalies
"""

import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.utils.logger import setup_logger, log_step

logger = setup_logger('exceptions')


@log_step("Vérification des exceptions")
def check_exceptions(execution_date):
    """Vérifie les anomalies et génère un rapport"""
    
    logger.info(f"🔍 Vérification pour la date: {execution_date}")
    logger.info("")
    
    exceptions = []
    
    # 1. Charger la demande nette
    demand_file = Path(f'data/processed/net_demand_{execution_date}.csv')
    
    if not demand_file.exists():
        logger.warning(f"⚠️  Fichier introuvable: {demand_file}")
        logger.info("   Aucune exception à vérifier")
        return True
    
    demand_df = pd.read_csv(demand_file)
    
    logger.info(f"📂 {len(demand_df)} produits à commander")
    logger.info("")
    
    # 2. Vérifier les commandes volumineuses (> 1000 unités)
    logger.info("🔎 Vérification des commandes volumineuses...")
    large_orders = demand_df[demand_df['final_order_qty'] > 1000]
    
    if len(large_orders) > 0:
        logger.warning(f"   ⚠️  {len(large_orders)} commande(s) > 1000 unités")
        for _, row in large_orders.iterrows():
            exceptions.append({
                'type': 'LARGE_ORDER',
                'severity': 'WARNING',
                'sku': row['sku'],
                'product_name': row['product_name'],
                'quantity': int(row['final_order_qty']),
                'message': f"Commande volumineuse: {row['final_order_qty']:,.0f} unités"
            })
    else:
        logger.info("   ✓ Aucune commande volumineuse")
    
    logger.info("")
    
    # 3. Vérifier les valeurs élevées (> 50,000 MAD)
    logger.info("🔎 Vérification des valeurs élevées...")
    demand_df['order_value'] = demand_df['final_order_qty'] * demand_df['unit_price']
    high_value = demand_df[demand_df['order_value'] > 50000]
    
    if len(high_value) > 0:
        logger.warning(f"   ⚠️  {len(high_value)} commande(s) > 50,000 MAD")
        for _, row in high_value.iterrows():
            exceptions.append({
                'type': 'HIGH_VALUE',
                'severity': 'WARNING',
                'sku': row['sku'],
                'product_name': row['product_name'],
                'value': float(row['order_value']),
                'message': f"Valeur élevée: {row['order_value']:,.2f} MAD"
            })
    else:
        logger.info("   ✓ Aucune valeur excessive")
    
    logger.info("")
    
    # 4. Vérifier les ruptures critiques (stock < 0)
    logger.info("🔎 Vérification des ruptures critiques...")
    critical = demand_df[demand_df['current_stock'] < 0]
    
    if len(critical) > 0:
        logger.error(f"   ❌ {len(critical)} rupture(s) critique(s)")
        for _, row in critical.iterrows():
            exceptions.append({
                'type': 'STOCK_OUT',
                'severity': 'CRITICAL',
                'sku': row['sku'],
                'product_name': row['product_name'],
                'current_stock': int(row['current_stock']),
                'message': f"Rupture de stock: {row['current_stock']:,.0f} unités"
            })
    else:
        logger.info("   ✓ Aucune rupture critique")
    
    logger.info("")
    
    # 5. Vérifier les stocks très bas (< stock sécurité / 2)
    logger.info("🔎 Vérification des stocks bas...")
    low_stock = demand_df[
        (demand_df['current_stock'] > 0) & 
        (demand_df['current_stock'] < demand_df['safety_stock_qty'] / 2)
    ]
    
    if len(low_stock) > 0:
        logger.warning(f"   ⚠️  {len(low_stock)} stock(s) très bas")
        for _, row in low_stock.iterrows():
            exceptions.append({
                'type': 'LOW_STOCK',
                'severity': 'WARNING',
                'sku': row['sku'],
                'product_name': row['product_name'],
                'current_stock': int(row['current_stock']),
                'safety_stock': int(row['safety_stock_qty']),
                'message': f"Stock bas: {row['current_stock']:,.0f} unités (sécurité: {row['safety_stock_qty']:,.0f})"
            })
    else:
        logger.info("   ✓ Aucun stock critique")
    
    logger.info("")
    
    # 6. Sauvegarder le rapport
    if exceptions:
        logger.info("💾 Sauvegarde du rapport d'exceptions...")
        
        exceptions_dir = Path('logs/exceptions')
        exceptions_dir.mkdir(parents=True, exist_ok=True)
        
        exceptions_file = exceptions_dir / f'exceptions_{execution_date}.json'
        with open(exceptions_file, 'w', encoding='utf-8') as f:
            json.dump({
                'date': execution_date,
                'total_exceptions': len(exceptions),
                'exceptions': exceptions
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"   ✓ Rapport: {exceptions_file}")
        logger.info("")
    
    # 7. Résumé
    logger.info("📊 RÉSUMÉ DES EXCEPTIONS:")
    logger.info(f"   • Total: {len(exceptions)}")
    
    if exceptions:
        by_severity = {}
        for exc in exceptions:
            severity = exc['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        for severity, count in by_severity.items():
            logger.info(f"   • {severity}: {count}")
    else:
        logger.info("   ✓ Aucune exception détectée")
    
    logger.info("")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Vérification des exceptions')
    parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y-%m-%d'))
    args = parser.parse_args()
    
    try:
        check_exceptions(args.date)
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()