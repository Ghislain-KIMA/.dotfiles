# .dotfiles

Dépôt personnel regroupant l'installation automatisée de logiciels et la restauration de mes configurations habituelles (Git, VS Code, nano, conda...) sur Ubuntu, après une réinstallation du système.

## Contenu

```
.dotfiles/
├── my_ubuntu.py          # Installe les logiciels (APT, .deb, archives vérifiées, dépôts officiels...)
├── restore_dotfiles.py   # Installe Stow, relie les configs, réinstalle les extensions VS Code
├── git/
│   └── .gitconfig
├── nano/
│   └── .nanorc
├── conda/
│   └── .condarc
└── vscode/
    ├── .config/Code/User/settings.json
    └── extensions.txt    # Liste des extensions VS Code à réinstaller
```

## Utilisation sur une machine fraîche

Une seule commande, à lancer sur un Ubuntu tout juste installé (sans rien d'autre configuré au préalable) :

```bash
curl -O https://raw.githubusercontent.com/TON_USER/.dotfiles/main/my_ubuntu.py
python3 my_ubuntu.py
```

Ce script va, dans l'ordre :

1. Installer les paquets système essentiels via APT (Git, PostgreSQL, VirtualBox, Docker, etc.)
2. Installer Chrome, Edge, VS Code, Android Studio, Flutter, Miniconda, Node.js (via NVM)
3. Configurer le `PATH` dans `~/.bashrc`
4. Créer les raccourcis Web Apps Chrome (Gmail, GitHub, YouTube, etc.)
5. Cloner ce dépôt dans `~/.dotfiles/` et restaurer les configurations :
   - Installer [GNU Stow](https://www.gnu.org/software/stow/)
   - Créer les liens symboliques (`~/.gitconfig`, `~/.nanorc`, `~/.condarc`, `~/.config/Code/User/settings.json`, ...)
   - Réinstaller toutes les extensions VS Code listées dans `vscode/extensions.txt`

## Logiciels installés et méthode

Chaque logiciel est installé via la source officielle la plus fiable disponible, en privilégiant systématiquement APT/`.deb` (paquets signés et vérifiés automatiquement à chaque mise à jour) ; à défaut, une archive officielle avec vérification manuelle du SHA-256.

| Logiciel | Méthode | Emplacement |
|---|---|---|
| Paquets système (build-essential, git, PostgreSQL, VirtualBox, Inkscape...) | APT (dépôts Ubuntu) | système |
| Google Chrome | `.deb` officiel | système |
| Microsoft Edge | dépôt APT Microsoft + clé GPG | système |
| Docker (CE, CLI, Buildx, Compose) | dépôt APT officiel + clé GPG | système |
| Claude Desktop | dépôt APT officiel Anthropic + **empreinte GPG vérifiée** | système |
| VS Code | dépôt APT Microsoft + clé GPG | système |
| Android Studio | archive `.tar.gz` officielle + **SHA-256 vérifié** | `~/installed/android-studio/` |
| Flutter SDK | `git clone` (dépôt officiel) | `~/installed/flutter/` |
| Miniconda | installeur `.sh` officiel + **SHA-256 vérifié** | `~/installed/miniconda3/` |
| Node.js / NVM | script d'installation officiel | `~/installed/nvm/` |

### Vérification SHA-256 (Android Studio, Miniconda)

Ces deux logiciels n'ont pas de dépôt APT officiel : leur intégrité est donc vérifiée manuellement après téléchargement.

- La **version et le SHA-256 attendu sont épinglés en dur** dans `my_ubuntu.py` (pas de "latest" mouvant, pour garder une somme stable et vérifiable).
- **Si le SHA-256 calculé ne correspond pas** à la valeur attendue :
  1. Le fichier téléchargé est immédiatement supprimé.
  2. Le script s'arrête (`RuntimeError`), aucune étape suivante ne s'exécute.
  3. Le message affiche la somme attendue et la somme obtenue pour diagnostiquer (fichier corrompu, version changée côté serveur, etc.).
- **Limite à connaître** : ces versions sont épinglées manuellement et deviendront obsolètes avec le temps. Il faut périodiquement revérifier et mettre à jour la version + le SHA-256 dans le script, depuis :
  - Android Studio : https://developer.android.com/studio
  - Miniconda : https://repo.anaconda.com/miniconda/

## Fonctionnement de Stow

Chaque sous-dossier à la racine (`git/`, `vscode/`, `nano/`, `conda/`) est un "package" Stow : son arborescence interne reproduit exactement celle attendue dans `$HOME`. La commande `stow <package>`, lancée depuis `~/.dotfiles/`, crée les liens symboliques correspondants — par exemple `~/.gitconfig` devient un lien vers `~/.dotfiles/git/.gitconfig`.

Modifier un fichier de config normalement (via son application, ou un éditeur) modifie donc directement le fichier versionné dans ce dépôt.

## Mettre à jour la liste des extensions VS Code

Après avoir installé une nouvelle extension utile, régénérer la liste avant de commit :

```bash
code --list-extensions > ~/.dotfiles/vscode/extensions.txt
cd ~/.dotfiles
git add vscode/extensions.txt
git commit -m "Mise à jour des extensions VS Code"
git push
```

## Sécurité — ce qui n'est volontairement PAS dans ce dépôt

- Clés SSH (`~/.ssh/`) et GPG (`~/.gnupg/`) — à régénérer/restaurer manuellement sur chaque nouvelle machine.
- Configuration rclone (`rclone.conf`) — contient des accès à des services cloud, à chiffrer avant toute migration future.
- Historique bash/psql/python, tokens d'authentification divers.

## Auteur

Ghislain — [BeoBenere](https://github.com/TON_USER)
