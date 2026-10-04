# ansible-roles-community

Collection Ansible `gazzah.community` — dépôt public.
Rôles fonctionnels réutilisables, sans politique ni données propres à une infrastructure.

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

## Rôles disponibles

- [debian_accounts](roles/debian_accounts/README.md) : comptes, groupes, clés et migrations explicites.
- [apt_repositories](roles/apt_repositories/README.md) : dépôts deb822 et options APT déclaratifs.
- [system_identity](roles/system_identity/README.md) : hostname et fuseau horaire.
- [services](roles/services/README.md) : état des services déclarés.

La version 0.5.0 retire le rôle composite `debian_baseline`. Chaque fonction est
appelée séparément avec ses variables d’inventaire. SSH et unattended-upgrades
sont confiés aux rôles communautaires choisis dans le dépôt consommateur.
Les scripts de présentation du lab restent dans ce dépôt privé.
