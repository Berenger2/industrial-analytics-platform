# Industrial Analytics Platform

Plateforme de démonstration pour le suivi de KPI industriels multi-sites.

Le projet couvre une chaîne analytique complète : ingestion de fichiers,
stockage PostgreSQL, modélisation sémantique avec Cube et restitution dans un
dashboard React.

## Aperçu

Le dashboard permet de suivre :

- les ordres de fabrication ;
- les volumes planifiés et produits ;
- le taux et la quantité de rebut ;
- les ordres en retard ;
- les contrôles qualité et les non-conformités ;
- les résultats par site, produit et période.

Les données utilisées sont fictives et représentent plusieurs sites de
production européens.

## Architecture

```text
CSV / XML
    │
    ▼
Importer Python
    │
    ▼
PostgreSQL
    │
    ▼
Cube semantic layer
    │
    ▼
React dashboard
```

| Service | Technologie | Responsabilité |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite | Dashboard, filtres et visualisations |
| API analytique | Cube | Modèle sémantique, KPI et pré-agrégations |
| Import | Python | Lecture, validation et nettoyage des fichiers |
| Base de données | PostgreSQL | Dimensions, faits et journalisation |
| Orchestration | Docker Compose | Environnement local reproductible |

## Fonctionnalités

### Dashboard

- vue globale de la performance ;
- production mensuelle ;
- comparaison des sites ;
- suivi des ordres de fabrication ;
- analyse des contrôles qualité ;
- filtres par site et période ;
- gestion des états de chargement et d'erreur.

### Import de données

- prise en charge des formats CSV et XML ;
- validation des champs obligatoires ;
- normalisation des valeurs ;
- insertions idempotentes par lots ;
- logs JSON structurés ;
- traçabilité des erreurs dans `import_logs`.

### Modèle analytique

Le modèle PostgreSQL sépare les dimensions et les faits :

- `dim_sites`
- `dim_products`
- `fact_production_orders`
- `fact_quality_controls`
- `import_logs`

Cube expose les domaines `ProductionOrders`, `QualityControls`, `Sites` et
`Products`, avec des pré-agrégations mensuelles par site.

## Démarrage

### Prérequis

- Docker Desktop ou Docker Engine ;
- Docker Compose v2.

### Installation

```bash
git clone https://github.com/Berenger2/industrial-analytics-platform.git
cd industrial-analytics-platform
cp .env.example .env
```

Remplacer les deux valeurs sensibles dans `.env` :

```env
POSTGRES_PASSWORD=your-local-password
CUBEJS_API_SECRET=your-local-secret
```

Puis démarrer les services :

```bash
docker compose up --build
```

Le dashboard est disponible sur :

```text
http://localhost:5173
```

## Commandes utiles

```bash
# Arrêter les services
docker compose down

# Recréer entièrement la base locale
docker compose down --volumes
docker compose up --build

# Relancer l'import des fichiers d'exemple
docker compose run --rm importer

# Consulter les logs
docker compose logs -f
```

Les scripts SQL d'initialisation sont exécutés uniquement lors de la création
du volume PostgreSQL.

## Qualité

Le dépôt comprend :

- des tests unitaires pour l'importeur ;
- une vérification TypeScript ;
- un build frontend de production ;
- une validation Docker Compose ;
- une CI GitHub Actions sur `develop` et `main` ;
- une publication optionnelle des images sur GitHub Container Registry.

Les principales vérifications locales sont :

```bash
cd importer
python -m unittest discover -s tests -v

cd ../frontend
npm ci
npm run typecheck
npm run build
```

## Structure

```text
.
├── cube/                 # Modèles Cube
├── data/samples/         # Fichiers CSV et XML fictifs
├── frontend/             # Dashboard React TypeScript
├── importer/             # Service d'import Python
├── infra/postgres/init/  # Schéma et données de démonstration
├── compose.yaml
└── .github/workflows/    # CI et publication des images
```

## Périmètre

Ce projet est conçu pour la démonstration et le développement local. Une mise
en production demanderait notamment une authentification, TLS, une gestion
centralisée des secrets, des sauvegardes et une stratégie de migration.
