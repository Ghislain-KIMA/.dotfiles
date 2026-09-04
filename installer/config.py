"""Configuration centralisée : chemins et versions épinglées.

Un seul endroit pour retrouver/modifier tout ce qui est configurable dans
le projet. Chaque module importe d'ici plutôt que de coder ses propres
chemins ou versions en dur.

Note : my_ubuntu.py (le point d'entrée, à la racine) N'IMPORTE PAS ce
fichier -- il doit rester autonome, puisqu'il s'exécute avant même que ce
dépôt (et donc ce module) existe sur une machine fraîche. Il garde donc
ses deux constantes minimales (URL du dépôt, DOTFILES_DIR) en double,
volontairement.
"""
import os
from pathlib import Path

# --- Chemins ---------------------------------------------------------------

# Doit rester calculé de la même façon que dans my_ubuntu.py (même variable
# d'environnement, même valeur par défaut) pour pointer vers le même dossier.
DOTFILES_DIR = Path(
    os.environ.get("DOTFILES_DIR", str(Path.home() / ".dotfiles"))
).expanduser()

NVM_DIR = Path.home() / ".nvm"
CONDA_DIR = Path.home() / "miniconda3"

# --- Versions épinglées (pas de dépôt/API permettant une résolution dynamique) --

NVM_VERSION = "v0.40.7"
NODE_VERSION = "24"

# À mettre à jour manuellement depuis https://repo.anaconda.com/miniconda/
MINICONDA_FILENAME = "Miniconda3-py314_26.5.3-2-Linux-x86_64.sh"
MINICONDA_SHA256 = "80bc27f13c4de90f10e387aa45e864de4f0860692c1221aef5900009a2b55302"
MINICONDA_URL = f"https://repo.anaconda.com/miniconda/{MINICONDA_FILENAME}"

# --- Divers ------------------------------------------------------------------

GITHUB_USERNAME = "Ghislain-KIMA"
DOTFILES_REPO_URL = f"https://github.com/{GITHUB_USERNAME}/.dotfiles.git"
