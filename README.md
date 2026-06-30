
# Procurement Data Pipeline – Supply Chain

## 📌 Description
Pipeline batch distribué automatisant le processus d'approvisionnement pour une épicerie en ligne gérant **8 magasins**. Le système calcule les besoins nets, applique les règles fournisseurs (MOQ, pack size, lead time) et génère automatiquement les commandes fournisseurs avec une traçabilité et une auditabilité complètes des données.

---

## 🎯 Objectifs
- Automatiser les commandes fournisseurs à partir des ventes des 8 magasins
- Assurer l'auditabilité complète des données (traçabilité des commandes)
- Gérer les règles fournisseurs complexes (MOQ, pack size, lead time)
- Détecter les exceptions et anomalies (ruptures, délais)
- Séparer clairement les couches OLTP (PostgreSQL) et analytique (HDFS/Trino)

---

## 🏗️ Architecture Technique

| Couche | Technologie | Rôle |
|--------|-------------|------|
| **Base de données opérationnelle** | PostgreSQL | Données maîtres (produits, fournisseurs, stocks, règles) |
| **Data Lake** | HDFS + Hive Metastore | Stockage distribué des données (raw, processed, output, logs) |
| **Moteur SQL distribué** | Trino | Interrogation des données sur HDFS (format Parquet) |
| **Traitement batch** | Python (scripts) | Calcul des besoins, application des règles, génération des commandes |
| **Conteneurisation** | Docker | Déploiement et isolation des services |

---

## 🔄 Pipeline de Données

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PROCUREMENT DATA PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    1. INGESTION QUOTIDIENNE                          │   │
│  │     Récupération des données de vente depuis les 8 magasins POS      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    2. DATA LAKE (HDFS)                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐│   │
│  │  │  raw/        │  │  processed/  │  │  output/     │  │  logs/   ││   │
│  │  │  (brutes)    │  │  (nettoyées) │  │  (résultats) │  │  (audit) ││   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘│   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    3. CALCUL DU NET DEMAND                           │   │
│  │     Besoin = Ventes - Stock disponible - Commandes en cours          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    4. APPLICATION RÈGLES FOURNISSEURS                │   │
│  │     MOQ (Quantité Minimum de Commande)                               │   │
│  │     Pack Size (Conditionnement)                                      │   │
│  │     Lead Time (Délai de livraison)                                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    5. GÉNÉRATION DES COMMANDES                       │   │
│  │     Création automatique des bons de commande fournisseurs           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    6. DATA QUALITY & EXCEPTIONS                      │   │
│  │     Détection des anomalies (ruptures, délais, erreurs de calcul)    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Installation et Déploiement

### Prérequis
- Docker & Docker Compose
- Python 3.8+
- PostgreSQL
- HDFS (via Docker)

### Lancer le projet
```bash
# 1. Cloner le repository
git clone https://github.com/samiraelyaagoubi2022/procurements-pipeline.git

# 2. Lancer les services avec Docker Compose
docker-compose up -d

# 3. Exécuter le pipeline
python scripts/run_pipeline.py
```

---

## 📊 Résultats
- **8 magasins** simulés
- **Ingestion quotidienne** automatisée
- **Commandes fournisseurs** générées automatiquement
- **Traçabilité complète** des données (logs d'audit)
- **Détection des exceptions** (ruptures, délais)

---

## 🛠️ Stack Technique
| Composant | Version |
|-----------|---------|
| PostgreSQL | 13+ |
| HDFS | 3.3+ |
| Hive | 3.1+ |
| Trino | 400+ |
| Python | 3.8+ |
| Docker | 20.10+ |

---

## 👥 Auteur
**Samira EL YAAGOUBI**  
