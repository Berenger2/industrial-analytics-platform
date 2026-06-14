# Contribuer

Merci de contribuer à Industrial Analytics Platform.

## Développement local

1. Créer `.env` à partir de `.env.example`.
2. Utiliser des secrets locaux uniques.
3. Démarrer les services avec `docker compose up --build`.
4. Vérifier `docker compose config --quiet` avant de proposer une modification.
5. Construire le frontend avec `npm ci && npm run build` depuis `frontend/`.

## Pull requests

- limiter chaque pull request à un objectif clair ;
- documenter les changements de configuration ;
- ajouter ou adapter les tests lorsque le comportement évolue ;
- ne jamais committer de secret, de fichier `.env` ou de données sensibles ;
- vérifier que l'intégration continue réussit.

Pour une vulnérabilité, suivre la procédure de [SECURITY.md](SECURITY.md) au
lieu d'ouvrir une issue publique.
