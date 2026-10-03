# ansible-roles-community

Collection Ansible `gazzah.community` — dépôt public.
Le socle ne contient pas encore de rôle : ils seront ajoutés selon les premières automatisations.

## Organisation

- `roles/<nom>/` : tâches, defaults, handlers, templates et documentation du rôle.
- `plugins/` : plugins réutilisables si nécessaire.
- `tests/` : vérifications fonctionnelles à ajouter avec les rôles.
- `galaxy.yml` : version et dépendances de la collection.

Un rôle est appelé avec son nom complet : `gazzah.community.nom_du_role`.
Les paramètres spécifiques aux machines sont fournis par les inventaires du dépôt privé `ansible-code`.
Aucun mot de passe, domaine interne ou adresse de serveur ne doit être ajouté à la collection publique.

## Vérifier et construire

```sh
python -m pip install -r requirements-dev.txt
yamllint .
mkdir -p build
ansible-galaxy collection build --output-path build
```

Après ajout et validation des rôles, créer un tag correspondant à `galaxy.yml`.
Le dépôt consommateur référence un tag précis, jamais une branche flottante en exploitation.
La licence de redistribution reste à choisir avant une publication sur Ansible Galaxy.
