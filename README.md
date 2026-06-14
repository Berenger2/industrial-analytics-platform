# Industrial Analytics Platform

Socle conteneurisé pour une plateforme d'analyse de données industrielles.
Le projet associe PostgreSQL, Cube, un importeur Python et une interface React.

> Le dépôt est actuellement destiné au développement local et à la
> démonstration. Il ne constitue pas encore une configuration de production.

## Services

| Service | Rôle | URL locale |
| --- | --- | --- |
| `postgres` | Stockage PostgreSQL persistant | `localhost:5432` |
| `cube` | Couche sémantique et API analytique Cube | <http://localhost:4000> |
| `frontend` | Interface React servie par Vite | <http://localhost:5173> |
| `importer` | Import idempotent des fichiers CSV et XML | tâche ponctuelle |

## Prérequis

- Docker Engine ou Docker Desktop ;
- Docker Compose v2.

## Installation

Créer la configuration locale :

```bash
cp .env.example .env
```

Remplacer au minimum `POSTGRES_PASSWORD` et `CUBEJS_API_SECRET` dans `.env`.
Pour générer des valeurs robustes :

```bash
openssl rand -hex 24
openssl rand -hex 32
```

Démarrer la plateforme :

```bash
docker compose up --build
```

Ouvrir ensuite <http://localhost:5173>.

Les ports sont liés à `127.0.0.1` afin de ne pas exposer les services sur le
réseau local. Ils peuvent être personnalisés dans `.env`.

Le service `importer` traite tous les fichiers CSV et XML de `data/samples`.
Grâce à la contrainte d'unicité, relancer la stack ne duplique pas les mesures.
Les lignes invalides et erreurs techniques sont tracées dans `import_logs`.

## Configuration

| Variable | Description | Exemple |
| --- | --- | --- |
| `POSTGRES_DB` | Nom de la base PostgreSQL | `industrial_analytics` |
| `POSTGRES_USER` | Utilisateur PostgreSQL | `industrial` |
| `POSTGRES_PASSWORD` | Mot de passe local, obligatoire | valeur aléatoire |
| `POSTGRES_PORT` | Port PostgreSQL sur la machine | `5432` |
| `CUBE_PORT` | Port de l'API Cube | `4000` |
| `CUBEJS_API_SECRET` | Secret de signature Cube, obligatoire | valeur aléatoire |
| `CUBEJS_DEV_MODE` | Active le mode développement Cube | `true` |
| `FRONTEND_PORT` | Port de l'interface Vite | `5173` |
| `VITE_CUBE_API_URL` | URL publique de l'API Cube | `http://localhost:4000/cubejs-api/v1` |
| `LOG_LEVEL` | Niveau de journalisation de l'importeur | `INFO` |

La configuration détaillée et les contrats CSV/XML sont documentés dans
[importer/README.md](importer/README.md).

Seules les variables préfixées par `VITE_` sont exposées au navigateur. Elles
ne doivent jamais contenir de secret.

## Arborescence

```text
.
├── compose.yaml
├── cube/
│   ├── Dockerfile
│   ├── cube.js
│   └── model/
├── data/
│   └── samples/
├── frontend/
├── importer/
├── infra/
│   └── postgres/
│       └── init/
└── .github/
    └── workflows/
        └── ci.yml
```

Les scripts de `infra/postgres/init` sont exécutés uniquement lors de la
création initiale du volume PostgreSQL.

Le schéma analytique principal se trouve dans
`infra/postgres/init/003_industrial_kpi_model.sql`. Il fournit les dimensions
sites et produits, les faits de production et de qualité, ainsi que la
traçabilité des imports. Les données fictives multi-sites sont séparées dans
`infra/postgres/init/004_demo_data.sql` et sont chargées de manière idempotente.

## Commandes utiles

Arrêter les services :

```bash
docker compose down
```

Arrêter les services et supprimer les données locales :

```bash
docker compose down --volumes
```

Relancer uniquement l'import :

```bash
docker compose run --rm importer
```

Consulter les journaux :

```bash
docker compose logs -f
```

Valider la configuration Compose :

```bash
docker compose config --quiet
```

Construire le frontend hors de Docker :

```bash
cd frontend
npm ci
npm run build
```

## Contribution

Consulter [CONTRIBUTING.md](CONTRIBUTING.md) avant de proposer une
modification. Les vulnérabilités doivent être signalées selon
[SECURITY.md](SECURITY.md), jamais dans une issue publique.

## Sécurité et production

Le fichier `.env` est volontairement exclu de Git. Le fichier `.env.example`
documente uniquement les variables attendues et ne doit contenir aucun secret.

Avant une mise en production :

- désactiver `CUBEJS_DEV_MODE` ;
- ne pas exposer PostgreSQL publiquement ;
- ajouter une terminaison TLS et une stratégie d'authentification ;
- définir les sauvegardes, la supervision et la politique de migration SQL.
