# debian_accounts

Premier rôle de référence de la collection `gazzah.community` : gestion déclarative
et idempotente des comptes locaux Debian, sans modifier directement les fichiers
`/etc/passwd`, `/etc/group` ou `/etc/shadow`.

## Compatibilité et installation

Cibles : Debian 12 (bookworm) et Debian 13 (trixie), avec Python 3 et des privilèges
root (`become: true`). Contrôleur : ansible-core 2.19 ou ultérieur.
La collection `ansible.posix` est nécessaire, sans dépendance à un autre rôle :

```sh
ansible-galaxy collection install ansible.posix
```

Dans une collection installée, utiliser `gazzah.community.debian_accounts`.
Pour utiliser le rôle directement depuis ce dépôt, ajouter son répertoire `roles`
à `ANSIBLE_ROLES_PATH` et utiliser `debian_accounts`.

## Variables

Les seules variables globales sont définies dans `defaults/main.yml` :

```yaml
debian_accounts_groups: []
debian_accounts_users: []
```

Une liste vide ne supprime aucun compte ou groupe existant. Seuls les objets
explicitement déclarés sont gérés. Les valeurs propres à l'infrastructure restent
dans l'inventaire ; `vars/main.yml` ne contient aucune valeur imposée.

Chaque groupe explicite accepte `name` (obligatoire), `gid` (facultatif) et
`state` (`present` par défaut, ou `absent`).

### Propriétés d'un utilisateur

| Propriété | Type | Comportement si omise |
| --- | --- | --- |
| `name` | chaîne, obligatoire | Nom du compte |
| `state` | `present` / `absent` | `present` |
| `uid` | entier | Choix du système à la création, inchangé sinon |
| `group` | chaîne | Groupe principal choisi par le système à la création |
| `gid` | entier | Pas de création automatique du groupe principal |
| `groups` | liste de noms | Groupes secondaires existants conservés |
| `append` | booléen | `false` : remplace les groupes secondaires si `groups` est défini |
| `shell` | chemin | Valeur du système à la création, inchangée sinon |
| `comment` | chaîne | Comportement du module `user` |
| `create_home` | booléen | Valeur du module : `true` |
| `home` | chemin | Valeur du système à la création, inchangée sinon |
| `password` | chaîne | Mot de passe existant inchangé ; fournir uniquement un hash Linux |
| `update_password` | `always` / `on_create` | Valeur du module : `always` |
| `password_lock` | booléen | État du verrouillage du mot de passe inchangé |
| `expires` | nombre | Expiration inchangée ; timestamp Unix en secondes, `-1` pour la retirer |
| `remove` | booléen | Valeur du module : `false` ; utilisé avec `state: absent` |
| `ssh_authorized_keys` | liste de clés publiques | Fichier `authorized_keys` inchangé |
| `ssh_keys_exclusive` | booléen | `false` : conserve les autres clés |

Les paramètres facultatifs sont omis via `default(omit)` (ou l'équivalent
conditionnel pour `groups`). Aucune politique globale de shell ou de mot de passe
n'est imposée. Utiliser des booléens YAML `true` / `false`.

### Groupes principaux et secondaires

Ordre d'application : groupes explicites, groupes principaux automatiques,
utilisateurs, puis clés SSH. Le groupe principal est créé automatiquement seulement
si l'utilisateur est présent et définit à la fois `group` et `gid`.
Sans `gid`, le groupe nommé doit déjà exister ou être déclaré explicitement.

Un groupe déclaré dans `debian_accounts_groups` a priorité : il n'est pas recréé
par la boucle automatique et son GID explicite fait autorité. Plusieurs utilisateurs
peuvent partager le même groupe automatique ; ils doivent déclarer le même GID.
Les appels répétés avec ce même GID sont idempotents. Déclarer chaque nom de compte
et chaque groupe explicite une seule fois. Les configurations contradictoires
(GID différents pour un même groupe, groupe absent utilisé par un compte présent)
ne sont pas prises en charge.

Les groupes secondaires doivent déjà exister ou être déclarés dans la liste des
groupes. Avec `append: false` et une liste `groups` définie, tout groupe secondaire
non listé est retiré. **Oublier `sudo` peut supprimer l'accès administrateur.**
`groups: []` retire tous les groupes secondaires ; omettre `groups` les conserve.
Avec `append: true`, les groupes listés sont ajoutés sans retirer les autres.

### Mots de passe, verrouillage et expiration

`password` doit être un hash compatible avec `crypt(3)` et `/etc/shadow` sur la
cible, jamais un mot de passe en clair. Le rôle ne calcule pas les hashes et ne
vérifie pas leur validité cryptographique. Les boucles sur les utilisateurs utilisent
`no_log: true` afin de ne pas afficher les hashes, y compris en mode diff.

Stocker les hashes avec Ansible Vault, par exemple dans
`group_vars/all/vault.yml` créé avec `ansible-vault create group_vars/all/vault.yml` :

```yaml
# Exemple de forme uniquement : remplacer par un hash complet valide.
vault_debian_accounts_aymen_password_hash: '$y$...'
```

Puis référencer cette variable dans l'inventaire :

```yaml
password: "{{ vault_debian_accounts_aymen_password_hash }}"
update_password: on_create
```

Exécuter le playbook avec `--ask-vault-pass` ou un mécanisme Vault adapté.
`on_create` conserve le mot de passe des comptes existants ; `always` applique les
changements du hash déclaré. Réutiliser un hash stable pour préserver l'idempotence.

`password_lock: true` verrouille **le mot de passe**, pas tous les accès au compte :
une clé SSH peut encore fonctionner. `false` déverrouille un mot de passe existant
verrouillé. Pour expirer le compte, déclarer un timestamp passé dans `expires` ;
l'effet sur les connexions dépend aussi de la configuration PAM/SSH.

### Clés SSH

Toutes les clés d'un utilisateur sont transmises ensemble à
`ansible.posix.authorized_key`, séparées par des retours à la ligne. Il n'y a pas de
boucle par clé. `ssh_keys_exclusive: true` supprime les clés non déclarées et peut
couper l'accès SSH : inclure toutes les clés nécessaires, notamment celles de
l'automatisation. Par défaut, les autres clés sont conservées.

Une liste vide avec `ssh_keys_exclusive: true` vide les clés autorisées ; avec
`false`, elle ne retire aucune clé. Une propriété `ssh_authorized_keys` absente ne
touche pas au fichier, même si l'exclusivité est activée. Les comptes absents sont
toujours ignorés. Le module gère le répertoire `.ssh` et ses permissions ; prévoir
un home utilisable, notamment lorsque `create_home: false`.

## Exemple minimal

```yaml
- name: Configure Debian accounts
  hosts: all
  become: true
  roles:
    - role: gazzah.community.debian_accounts
      debian_accounts_users:
        - name: deploy
          shell: /bin/bash
```

Équivalent pour un rôle local avec `ANSIBLE_ROLES_PATH` configuré :

```yaml
- name: Configure Debian accounts
  hosts: all
  become: true
  roles:
    - role: debian_accounts
```

## Exemple complet d'inventaire

Les clés ci-dessous sont des placeholders à remplacer par de vraies clés publiques.
Les identifiants numériques doivent être adaptés aux machines cibles.

```yaml
debian_accounts_groups:
  - name: admins
    gid: 1500
    state: present
  - name: developers
    gid: 1501
    state: present
  - name: docker
    state: present

debian_accounts_users:
  - name: aymen
    uid: 1001
    group: aymen
    gid: 1001
    groups:
      - sudo
      - docker
      - developers
    append: false
    shell: /bin/bash
    comment: Aymen Gazzah
    create_home: true
    home: /home/aymen
    password: "{{ vault_debian_accounts_aymen_password_hash }}"
    update_password: on_create
    password_lock: false
    expires: -1
    ssh_authorized_keys:
      - "ssh-ed25519 AAAA..."
      - "ssh-ed25519 BBBB..."
    ssh_keys_exclusive: true
    state: present
  - name: olduser
    state: absent
    remove: true
```

## Suppression et identifiants existants

Pour supprimer un compte et son home (ainsi que son spool mail selon `userdel`) :

```yaml
debian_accounts_users:
  - name: olduser
    state: absent
    remove: true
```

Sans `remove: true`, le home est conservé. Le rôle ne force pas la suppression d'un
compte occupé et ne supprime pas explicitement son groupe principal ; `userdel`
peut supprimer son groupe privé selon la configuration Debian.

Vérifier les UID/GID déjà utilisés avant application : aucune allocation ni migration
automatique n'est effectuée. Modifier l'UID d'un compte existant peut laisser des
fichiers hors de son home avec l'ancien propriétaire numérique. Modifier un GID
peut laisser des fichiers associés à l'ancien groupe. Prévoir une migration séparée
et contrôlée des fichiers et des processus. Modifier `home` ne déplace pas son
contenu (le rôle n'active pas `move_home`).

Les groupes explicites sont traités avant les utilisateurs, y compris pour les
suppressions. Retirer d'abord les utilisateurs ou changer leur groupe principal
dans une première exécution, puis supprimer le groupe dans une seconde.

## Structure et conventions

- `defaults/main.yml` : interface publique, variables préfixées `debian_accounts_`.
- `tasks/main.yml` : imports statiques de `groups.yml`, `users.yml`, `ssh_keys.yml`.
- `handlers/main.yml` et `vars/main.yml` : réservés, sans configuration imposée.
- `meta/main.yml` : auteur, compatibilité et métadonnées du rôle.
- `tests/inventory` et `tests/test.yml` : scénario minimal sans secret.

Les modules et imports utilisent leur FQCN. Tags disponibles : `debian_accounts`,
`debian_accounts_groups`, `debian_accounts_users`, `debian_accounts_ssh`.
Les tags partiels supposent que les prérequis existent déjà ; une exécution complète
reste nécessaire pour créer les groupes et les comptes avant les clés.

## Validation

Depuis la racine du dépôt :

```sh
ansible-playbook -i roles/debian_accounts/tests/inventory roles/debian_accounts/tests/test.yml --syntax-check
ansible-lint roles/debian_accounts
```

Depuis le répertoire du rôle :

```sh
ansible-playbook -i tests/inventory tests/test.yml --syntax-check
```

Le test importe le rôle par un chemin relatif au playbook, indépendamment du
répertoire courant et sans installation préalable de la collection locale.
Le scénario couvre les groupes explicites, un groupe principal partagé, les groupes
secondaires, les clés vides exclusives et un compte absent. Le contrôle de syntaxe
ne prouve pas la convergence ni la compatibilité réelle des deux versions Debian.

Pour un test fonctionnel, utiliser uniquement une machine Debian jetable et adapter
l'inventaire (fourni en connexion locale). Une exécution sans `--syntax-check`
**crée des comptes de test** et utilise les GID 29100/29101 : vérifier leur disponibilité.
Exécuter deux fois le playbook ; la seconde exécution doit annoncer `changed=0`.
Aucun nettoyage automatique ni Molecule n'est inclus à ce stade.

## Références et licence

Comportements des modules :
[user](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/user_module.html),
[group](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/group_module.html),
[authorized_key](https://docs.ansible.com/projects/ansible/latest/collections/ansible/posix/authorized_key_module.html).

Auteur : gazzah-lab. Licence du rôle : MIT-0, conservée depuis les en-têtes du
squelette existant. Cela ne choisit pas la licence de redistribution de la collection,
encore non définie dans `galaxy.yml`.
