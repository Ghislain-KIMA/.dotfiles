# .dotfiles

Dépôt personnel regroupant l'installation automatisée de logiciels et la restauration de mes configurations habituelles (Git, VS Code, ...) sur Ubuntu, après une réinstallation du système.

## Contenu

```
.dotfiles/
├── my_ubuntu.py          # Installe les logiciels (APT, .deb, archives, Snap...)
├── restore_dotfiles.py   # Installe Stow, relie les configs, réinstalle les extensions VS Code
├── git/
│   └── .gitconfig
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

1. Installer les paquets système essentiels via APT (Git, PostgreSQL, VirtualBox, etc.)
2. Installer Chrome, Edge, VS Code, Android Studio, Flutter, Miniconda, Node.js (via NVM)
3. Configurer le `PATH` dans `~/.bashrc`
4. Créer les raccourcis Web Apps Chrome (Gmail, GitHub, YouTube, etc.)
5. Cloner ce dépôt dans `~/.dotfiles/` et restaurer les configurations :
   - Installer [GNU Stow](https://www.gnu.org/software/stow/)
   - Créer les liens symboliques (`~/.gitconfig`, `~/.config/Code/User/settings.json`, ...)
   - Réinstaller toutes les extensions VS Code listées dans `vscode/extensions.txt`

## Fonctionnement de Stow

Chaque sous-dossier à la racine (`git/`, `vscode/`) est un "package" Stow : son arborescence interne reproduit exactement celle attendue dans `$HOME`. La commande `stow <package>`, lancée depuis `~/.dotfiles/`, crée les liens symboliques correspondants — par exemple `~/.gitconfig` devient un lien vers `~/.dotfiles/git/.gitconfig`.

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
- Configuration rclone (`rclone.conf`) — contient des accès à des services cloud, gérée séparément.
- Historique bash/psql/python, tokens d'authentification divers.

## Auteur

Ghislain — [BeoBenere](https://github.com/TON_USER)
