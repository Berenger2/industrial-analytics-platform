# Politique de sécurité

## Signaler une vulnérabilité

Ne pas publier de vulnérabilité dans une issue GitHub publique.

Utiliser la fonctionnalité **Private vulnerability reporting** de l'onglet
Security du dépôt GitHub. Le rapport doit inclure les étapes de reproduction,
l'impact estimé et, si possible, une proposition de correction.

Les secrets exposés doivent être révoqués et remplacés immédiatement, y compris
lorsqu'ils ont ensuite été supprimés du dépôt.

## Périmètre

Le projet est actuellement un environnement de développement. Les versions
déployées en production doivent notamment ajouter TLS, authentification,
sauvegardes, supervision et gestion centralisée des secrets.
