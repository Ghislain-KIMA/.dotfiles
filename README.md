# .dotfiles

Dépôt personnel pour automatiser l'installation des logiciels après une
réinstallation d'Ubuntu, et conserver quelques configurations perso.

## Système actif : `my_ubuntu.py`

C'est le script principal, à la racine du dépôt. Il installe les logiciels
au fur et à mesure des besoins réels, avec une exécution complète ou
étape par étape.

### Utilisation sur une machine fraîche

Une seule commande, sans rien installer au préalable (`wget` est disponible
par défaut sur Ubuntu) :

```bash
wget -O my_ubuntu.py https://raw.githubusercontent.com/Ghislain-KIMA/.dotfiles/main/my_ubuntu.py
python3 my_ubuntu.py
```

Le script s'occupe ensuite de tout, dans l'ordre :

1. **git** — installe git (nécessaire pour la suite)
2. **clone** — clone ce dépôt dans `~/.dotfiles/` (si pas déjà fait)
3. **update** — `apt update && apt upgrade`
4. **chrome** — Google Chrome (`.deb` téléchargé directement)
5. **vscode** — VS Code (dépôt APT officiel Microsoft + clé GPG)
6. **edge** — Microsoft Edge (dépôt APT officiel Microsoft + clé GPG)
7. **tools** — petits utilitaires en ligne de commande (`ripgrep`, ...)
8. **extensions** — extensions VS Code, depuis `vscode/extensions.txt`
9. **claude** — Claude Desktop (dépôt APT officiel Anthropic + empreinte GPG vérifiée)

### Lancer une seule étape

Utile pour retenter une étape précise sans tout relancer (ex : une extension
qui a échoué à cause d'un timeout réseau) :

```bash
python3 my_ubuntu.py extensions
python3 my_ubuntu.py chrome
python3 my_ubuntu.py edge
# etc. — voir le dict STEPS dans le script pour la liste complète
```

### Relancer le script plusieurs fois

Sans danger. Chaque étape vérifie d'abord si le logiciel est déjà présent
(`shutil.which`) avant d'agir, et les paquets déjà installés/à jour sont
simplement ignorés avec un message, sans erreur ni duplication.

### Utilisation en module Python

Le script peut aussi être importé pour appeler une fonction précise depuis
un shell interactif :

```bash
cd ~/.dotfiles
python3
>>> import my_ubuntu
>>> my_ubuntu.install_vscode_extensions()
```

### Méthode d'installation par logiciel

| Logiciel | Méthode | Vérification d'intégrité |
|---|---|---|
| Google Chrome | `.deb` téléchargé directement | Aucune (s'auto-enregistre en dépôt APT après coup) |
| VS Code | Dépôt APT officiel | Clé GPG du dépôt, vérifiée à chaque mise à jour |
| Microsoft Edge | Dépôt APT officiel | Clé GPG du dépôt, vérifiée à chaque mise à jour |
| Claude Desktop | Dépôt APT officiel | Empreinte GPG vérifiée explicitement avant usage |
| ripgrep, etc. | `apt install` (dépôts Ubuntu) | Gérée nativement par apt |

Le dépôt APT + clé GPG est préféré chaque fois que possible : contrairement
à un `.deb` téléchargé une fois, la signature est revérifiée à **chaque**
mise à jour future, pas seulement au premier téléchargement.

### Mettre à jour la liste des extensions VS Code

```bash
code --list-extensions > ~/.dotfiles/vscode/extensions.txt
cd ~/.dotfiles
git add vscode/extensions.txt
git commit -m "Mise à jour des extensions VS Code"
git push
```

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
Git par erreur. Corrigeable avec `stow --no-folding`, mais la complexité
n'en valait plus la peine pour l'usage recherché.

Ces fichiers restent dans le dépôt pour référence, mais ne sont **pas**
utilisés par `my_ubuntu.py`. Possibilité d'y revenir un jour si le besoin
se représente.

## Sécurité — ce qui n'est volontairement pas dans ce dépôt

- Clés SSH (`~/.ssh/`) et GPG (`~/.gnupg/`)
- Configuration rclone (`rclone.conf`)
- Historique bash/psql/python, tokens d'authentification

## Auteur

Ghislain — [BeoBenere](https://github.com/Ghislain-KIMA)
