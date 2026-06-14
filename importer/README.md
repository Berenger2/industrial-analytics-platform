# Importer

Service Python chargé d'intégrer les référentiels et faits industriels dans
PostgreSQL.

Il traite les sources dans l'ordre de leurs dépendances :

1. `sites.csv` vers `analytics.dim_sites`
2. `products.csv` vers `analytics.dim_products`
3. `production_orders.csv` vers `analytics.fact_production_orders`
4. `quality_controls.xml` vers `analytics.fact_quality_controls`

Chaque fichier produit une entrée dans `analytics.import_logs`. Les statuts
sont `completed`, `partial` lorsqu'une partie des lignes est rejetée, et
`failed` lorsqu'une erreur technique annule la transaction du fichier.

## Idempotence

Les données sont insérées ou mises à jour à partir des clés métier :

| Dataset | Clé |
| --- | --- |
| Sites | `site_code` |
| Produits | `product_code` |
| Ordres de fabrication | `order_number` |
| Contrôles qualité | `control_reference` |

Relancer l'import avec les mêmes fichiers ne crée donc pas de doublons.

## Formats

Les exemples complets sont disponibles dans `data/samples`.

Les fichiers CSV utilisent leur première ligne comme en-tête. Les timestamps
doivent respecter ISO 8601 et inclure un fuseau horaire. Les champs texte sont
nettoyés et les codes métier normalisés en majuscules.

Le fichier XML contient un élément par contrôle :

```xml
<quality_controls>
  <quality_control>
    <control_reference>QC-LYO-2026-0505-01</control_reference>
    <order_number>PO-2026-0501-LYO</order_number>
    <controlled_at>2026-05-05T10:30:00+02:00</controlled_at>
    <sample_size>80</sample_size>
    <passed_quantity>79</passed_quantity>
    <failed_quantity>1</failed_quantity>
    <result>passed</result>
    <defect_category>Surface finish</defect_category>
    <inspector_name>Claire Bernard</inspector_name>
    <notes>Functional tests passed.</notes>
  </quality_control>
</quality_controls>
```

## Configuration

| Variable | Défaut | Description |
| --- | --- | --- |
| `DATABASE_URL` | aucune | URL de connexion PostgreSQL |
| `IMPORT_INPUT_DIR` | aucune | Répertoire des sources |
| `IMPORT_SOURCE_SYSTEM` | aucune | Origine inscrite dans `import_logs` |
| `IMPORT_SITES_FILE` | `sites.csv` | Fichier des sites |
| `IMPORT_PRODUCTS_FILE` | `products.csv` | Fichier des produits |
| `IMPORT_PRODUCTION_ORDERS_FILE` | `production_orders.csv` | Fichier des OF |
| `IMPORT_QUALITY_CONTROLS_FILE` | `quality_controls.xml` | Fichier qualité |
| `IMPORT_QUALITY_CONTROL_RECORD_TAG` | `quality_control` | Élément XML unitaire |
| `IMPORT_CSV_DELIMITER` | `,` | Séparateur CSV |
| `IMPORT_BATCH_SIZE` | `500` | Taille des lots |
| `IMPORT_MAX_ERROR_DETAILS` | `20` | Erreurs détaillées conservées |
| `DATABASE_CONNECT_TIMEOUT_SECONDS` | `10` | Délai de connexion |
| `DATABASE_APPLICATION_NAME` | `industrial-analytics-importer` | Nom PostgreSQL |
| `LOG_LEVEL` | `INFO` | Niveau des logs JSON |

Les secrets sont fournis exclusivement par l'environnement.

## Exécution

Depuis la racine du dépôt :

```bash
docker compose run --rm importer
```

Le code de sortie vaut `0` si aucun fichier n'échoue, `1` en cas d'échec
d'import ou de connexion, et `2` si la configuration est invalide.

## Tests

```bash
cd importer
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Les logs sont structurés en JSON sur la sortie standard.

## Migration du modèle legacy

Une nouvelle base ne crée plus `analytics.production_metrics`. Sur un volume
PostgreSQL déjà initialisé, les scripts d'initialisation ne sont pas rejoués
automatiquement. La migration idempotente doit être exécutée une fois :

```bash
docker compose exec postgres psql \
  -U "${POSTGRES_USER:-industrial}" \
  -d "${POSTGRES_DB:-industrial_analytics}" \
  -f /docker-entrypoint-initdb.d/005_remove_legacy_production_metrics.sql
```
