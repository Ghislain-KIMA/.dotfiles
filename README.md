# .dotfiles

Dépôt personnel pour automatiser l'installation des logiciels après une
réinstallation d'Ubuntu, et conserver quelques configurations perso.

## Structure du dépôt

```
.dotfiles/
├── my_ubuntu.py              # Point d'entrée : bootstrap (git + clone) + CLI
└── installer/
    ├── __init__.py
    ├── config.py               # Chemins et versions centralisés (voir plus bas)
    ├── core.py                 # apt_update, upgrade_package_if_needed, compute_sha256, system_update
    ├── browsers.py              # Chrome, Edge
    ├── dev_tools.py             # VS Code, Docker, VirtualBox, Node.js (NVM), Miniconda
    ├── misc.py                  # ripgrep, Inkscape, PostgreSQL, tree, tealdeer, fzf, rclone, Draw.io, OBS Studio, Claude Desktop
    ├── vscode_extensions.py     # Réinstallation des extensions VS Code
    ├── post_config.py           # Ajustements après installation (services à désactiver...)
    └── steps.py                 # Rassemble tout dans STEPS + run_all()
```

## Utilisation sur une machine fraîche

Une seule commande, sans rien installer au préalable (`wget` est disponible
par défaut sur Ubuntu) :

```bash
wget -O my_ubuntu.py https://raw.githubusercontent.com/Ghislain-KIMA/.dotfiles/main/my_ubuntu.py
python3 my_ubuntu.py
```

`my_ubuntu.py` reste volontairement minimal et autonome (aucun import du
package `installer` en haut du fichier) : au tout premier lancement,
`~/.dotfiles/` n'existe pas encore et `git` n'est pas forcément installé.
Le script :

1. Installe git et clone ce dépôt — **seulement si nécessaire** (git absent
   ou dépôt pas encore cloné). Sur les lancements suivants, cette étape est
   silencieusement sautée.
2. Importe ensuite le package `installer/` (qui vient d'être cloné) et
   exécute toutes les étapes définies dans `STEPS`.

### Personnaliser l'emplacement du dépôt

Par défaut, tout se passe dans `~/.dotfiles/`. Personnalisable via la
variable d'environnement `DOTFILES_DIR` :

```bash
DOTFILES_DIR=~/datas/backup/remote/projects/.dotfiles python3 my_ubuntu.py
```

Les dossiers parents manquants sont créés automatiquement si besoin.

### Étapes disponibles

| Étape | Module | Description |
|---|---|---|
| `update` | `core` | `apt update && apt upgrade` |
| `chrome` | `browsers` | Google Chrome (`.deb` téléchargé directement) |
| `vscode` | `dev_tools` | VS Code (dépôt APT officiel Microsoft + clé GPG) |
| `edge` | `browsers` | Microsoft Edge (dépôt APT officiel + clé GPG) |
| `docker` | `dev_tools` | Docker CE (dépôt officiel + clé GPG) |
| `virtualbox` | `dev_tools` | VirtualBox + Extension Pack (dépôt Ubuntu standard, licence en mode interactif) |
| `nodejs` | `dev_tools` | Node.js via NVM (sans sudo, dans `~/.nvm`) |
| `miniconda` | `dev_tools` | Miniconda (version épinglée + SHA-256 vérifié) |
| `tools` | `misc` | ripgrep, Inkscape, PostgreSQL (+contrib), tree, tealdeer, fzf (dépôts Ubuntu) |
| `rclone` | `misc` | rclone (téléchargement direct, toujours la dernière version + SHA-256 vérifié) |
| `obs` | `misc` | OBS Studio (PPA officiel `ppa:obsproject/obs-studio`) |
| `drawio` | `misc` | Draw.io Desktop (dernière version via API GitHub + SHA-256) |
| `extensions` | `vscode_extensions` | Extensions VS Code depuis `vscode/extensions.txt` |
| `claude` | `misc` | Claude Desktop (dépôt officiel Anthropic + empreinte GPG vérifiée) |
| `post-config` | `post_config` | Désactive les services non désirés (PostgreSQL, Docker) |

### Lancer une seule étape

```bash
python3 my_ubuntu.py drawio
python3 my_ubuntu.py extensions
# etc.
```

### Relancer le script plusieurs fois

Sans danger. Chaque étape vérifie d'abord si le logiciel est déjà présent
avant d'agir. Le bootstrap (git + clone) ne s'exécute lui aussi qu'une
seule fois, silencieusement ignoré ensuite.

### `installer/config.py` : un seul endroit pour tout modifier

Ce fichier centralise :
- Les **chemins** (`DOTFILES_DIR`, `NVM_DIR`, `CONDA_DIR`)
- Les **versions épinglées** (`NVM_VERSION`, `NODE_VERSION`,
  `MINICONDA_FILENAME`, `MINICONDA_SHA256`)
- L'**URL du dépôt** (`DOTFILES_REPO_URL`)

Pour changer une version ou un chemin, un seul fichier à ouvrir — pas besoin
de fouiller dans chaque module.

**Exception** : `my_ubuntu.py` garde volontairement une copie de l'URL du
dépôt en double — il doit rester fonctionnel *avant* que ce fichier de
config n'existe sur la machine (avant le premier clonage).

### Ajouter un nouveau logiciel

1. Écrire la fonction `install_xxx()` dans le module qui correspond le
   mieux (`browsers.py`, `dev_tools.py`, `misc.py`, ou en créer un nouveau
   si aucun ne convient). Chemins et versions vont dans `config.py`.
2. L'ajouter au dictionnaire `STEPS` dans `installer/steps.py`.

### Méthode d'installation par logiciel

Le dépôt APT officiel + clé GPG est préféré chaque fois qu'il existe :
contrairement à un `.deb` téléchargé une fois, la signature est revérifiée
à **chaque** mise à jour future, pas seulement au premier téléchargement.
À défaut, un SHA-256 vérifié à l'installation.

| Logiciel | Méthode | Vérification |
|---|---|---|
| Google Chrome | `.deb` direct | Aucune (s'auto-enregistre en dépôt APT après coup) |
| VS Code, Edge, Docker, Claude Desktop | Dépôt APT officiel | Clé/empreinte GPG |
| OBS Studio | PPA officiel (Launchpad) | Clé gérée automatiquement par `add-apt-repository` |
| VirtualBox, ripgrep, Inkscape, PostgreSQL, tree, tealdeer, fzf | Dépôts Ubuntu standards | Gérée nativement par apt |
| Draw.io, Miniconda, rclone | Téléchargement direct | SHA-256 vérifié manuellement |
| Node.js | NVM (script officiel) | Aucune (pas de dépôt tiers, sans sudo) |

### Mettre à jour la liste des extensions VS Code

```bash
code --list-extensions > ~/.dotfiles/vscode/extensions.txt
cd ~/.dotfiles
git add vscode/extensions.txt
git commit -m "Mise à jour des extensions VS Code"
git push
```

### rclone

Le programme `rclone` est installé automatiquement (étape `rclone`, toujours
la dernière version stable), mais sa **configuration** (remotes, accès
cloud) reste volontairement manuelle : `rclone config` nécessite une
autorisation interactive (navigateur), et le fichier `rclone.conf` résultant
contient des identifiants sensibles à ne jamais committer en clair. Une
sauvegarde/restauration chiffrée (via `gpg`) pourra être ajoutée plus tard,
une fois une vraie configuration existante.

### Variables d'environnement

Une seule volontairement : `DOTFILES_DIR`. Elle seule a besoin d'être
connue *avant* que le dépôt (et `config.py`) n'existe sur la machine. Tout
le reste se règle directement dans `installer/config.py`.

---

## Fichiers legacy (non utilisés actuellement)

Le dépôt contient encore des restes d'une première approche basée sur
[GNU Stow](https://www.gnu.org/software/stow/) (liens symboliques) :

- `git/`, `nano/`, `conda/` — packages Stow (config Git, nano, conda)
- `vscode/.config/Code/User/settings.json` — settings VS Code, géré via Stow
- `restore_dotfiles.py` — script de restauration via Stow

Cette approche a été **abandonnée** : Stow "replie" un dossier entier en un
seul lien symbolique quand le dossier cible n'existe pas encore côté
machine (ex: `~/.config/Code/User/` absent sur une install fraîche), ce qui
a fait atterrir tout le cache/historique VS Code directement dans ce dépôt
Git par erreur. Ces fichiers restent pour référence, mais ne sont **pas**
utilisés par `my_ubuntu.py`.

## Sécurité — ce qui n'est volontairement pas dans ce dépôt

- Clés SSH (`~/.ssh/`) et GPG (`~/.gnupg/`)
- Configuration rclone (`rclone.conf`)
- Historique bash/psql/python, tokens d'authentification

## Auteur

Ghislain ([@Ghislain-KIMA](https://github.com/Ghislain-KIMA)) — setup personnel, pour mon propre workflow de développement.
