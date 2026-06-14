# Service d'import

Le service lit tous les fichiers CSV et XML configurés dans un répertoire,
nettoie et valide leurs lignes, puis alimente
`analytics.production_metrics`.

Chaque fichier produit une entrée dans `analytics.import_logs` :

- `completed` lorsque toutes les lignes sont valides ;
- `partial` lorsque les lignes valides sont importées mais que certaines sont
  rejetées ;
- `failed` lorsque le fichier est illisible, mal formé ou qu'une erreur
  technique interrompt son traitement.

Les insertions sont idempotentes grâce à la contrainte unique sur
`machine_id`, `metric_name` et `recorded_at`.

## Formats acceptés

Les deux formats utilisent les mêmes champs obligatoires :

| Champ | Règle |
| --- | --- |
| `machine_id` | texte non vide, normalisé en majuscules |
| `site` | texte non vide, espaces normalisés |
| `metric_name` | texte non vide, normalisé en minuscules |
| `metric_value` | nombre fini, point ou virgule décimale |
| `unit` | texte non vide, normalisé en minuscules |
| `recorded_at` | date ISO 8601 incluant un fuseau horaire |

### CSV

La première ligne doit contenir les noms de colonnes :

```csv
machine_id,site,metric_name,metric_value,unit,recorded_at
PRESS-001,Lyon,temperature,68.4,celsius,2026-01-15T08:00:00Z
```

### XML

Chaque mesure doit être placée dans un élément dont le nom est configuré avec
`IMPORT_XML_RECORD_TAG` :

```xml
<production_metrics>
  <record>
    <machine_id>PRESS-001</machine_id>
    <site>Lyon</site>
    <metric_name>temperature</metric_name>
    <metric_value>68.4</metric_value>
    <unit>celsius</unit>
    <recorded_at>2026-01-15T08:00:00Z</recorded_at>
  </record>
</production_metrics>
```

## Configuration

| Variable | Obligatoire | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `DATABASE_URL` | oui | aucune | URL PostgreSQL |
| `IMPORT_INPUT_DIR` | oui | aucune | Répertoire contenant les fichiers |
| `IMPORT_SOURCE_SYSTEM` | oui | aucune | Source inscrite dans `import_logs` |
| `IMPORT_CSV_PATTERN` | non | `*.csv` | Motif des fichiers CSV |
| `IMPORT_CSV_DELIMITER` | non | `,` | Séparateur CSV, sur un caractère |
| `IMPORT_XML_PATTERN` | non | `*.xml` | Motif des fichiers XML |
| `IMPORT_XML_RECORD_TAG` | non | `record` | Nom d'un élément XML représentant une ligne |
| `IMPORT_BATCH_SIZE` | non | `500` | Nombre de lignes insérées par lot |
| `IMPORT_MAX_ERROR_DETAILS` | non | `20` | Nombre maximal d'erreurs conservées par fichier |
| `DATABASE_CONNECT_TIMEOUT_SECONDS` | non | `10` | Délai maximal de connexion |
| `DATABASE_APPLICATION_NAME` | non | `industrial-analytics-importer` | Nom visible dans PostgreSQL |
| `LOG_LEVEL` | non | `INFO` | Niveau des logs JSON |

Les secrets ne doivent pas être ajoutés dans l'image Docker ni dans les
fichiers sources. Ils sont fournis au processus par l'environnement.

## Exécution

Depuis la racine du dépôt :

```bash
docker compose run --rm importer
```

Le processus retourne `0` si tous les fichiers sont terminés avec succès ou
partiellement. Il retourne `1` lorsqu'au moins un fichier échoue, et `2` pour
une configuration invalide.

## Tests

```bash
cd importer
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Les logs sont écrits sur la sortie standard au format JSON afin d'être
collectés directement par Docker ou une plateforme d'observabilité.
