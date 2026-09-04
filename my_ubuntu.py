#!/usr/bin/env python3
"""Point d'entrée du dépôt .dotfiles.

Ce fichier reste volontairement MINIMAL et autonome (aucun import du
package `installer`) : sur une machine fraîche, il est récupéré seul via
wget, à un moment où ~/.dotfiles/ n'existe pas encore et où `git` n'est
pas forcément installé. Une fois le dépôt cloné, il délègue tout le reste
au package `installer/`.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Dupliqué volontairement depuis installer/config.py (GITHUB_USERNAME,
# DOTFILES_REPO_URL) : ce fichier doit fonctionner AVANT que le dépôt
# (et donc installer/config.py) n'existe sur la machine.
DOTFILES_REPO_URL = "https://github.com/Ghislain-KIMA/.dotfiles.git"


def get_dotfiles_dir():
    """Chemin du dépôt .dotfiles, personnalisable via la variable DOTFILES_DIR.

    Par défaut : ~/.dotfiles (comportement inchangé si rien n'est précisé).
    """
    return Path(os.environ.get("DOTFILES_DIR", str(Path.home() / ".dotfiles"))).expanduser()


def install_git():
    """Installe git s'il n'est pas déjà présent (nécessaire pour cloner .dotfiles)."""
    print("\n=== Installation de Git ===\n")

    if shutil.which("git"):
        print("===> Git est déjà installé.")
        return

    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "git"], check=True)
        print("\n==> Git installé avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de Git : {error}")
        sys.exit(1)


def clone_dotfiles():
    """Clone le dépôt .dotfiles dans DOTFILES_DIR s'il n'existe pas déjà."""
    print("\n=== Clonage du dépôt .dotfiles ===\n")

    dotfiles_dir = get_dotfiles_dir()
    if dotfiles_dir.exists():
        print(f"===> {dotfiles_dir} existe déjà, clonage ignoré.")
        return

    # git clone ne crée pas les dossiers parents manquants (contrairement à
    # mkdir -p) -> nécessaire si DOTFILES_DIR pointe vers un chemin imbriqué
    # qui n'existe pas encore (ex: ~/datas/backup/remote/projects/.dotfiles).
    dotfiles_dir.parent.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(
            ["git", "clone", DOTFILES_REPO_URL, str(dotfiles_dir)],
            check=True,
        )
        print(f"\n==> Dépôt cloné avec succès dans {dotfiles_dir} !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors du clonage : {error}")
        sys.exit(1)


def main():
    dotfiles_dir = get_dotfiles_dir()

    # Bootstrap uniquement si nécessaire : première exécution sur une
    # machine fraîche (git absent OU dépôt pas encore cloné). Une fois
    # ces deux conditions remplies, on ne rappelle plus jamais ces
    # fonctions -> plus de message "Installation de Git" à chaque lancement.
    if not shutil.which("git") or not dotfiles_dir.exists():
        install_git()
        clone_dotfiles()

    # Le package `installer/` n'existe que depuis que clone_dotfiles() a
    # cloné le dépôt -> on l'importe seulement maintenant, jamais en haut
    # du fichier (sinon le tout premier lancement, avant clonage, planterait).
    sys.path.insert(0, str(dotfiles_dir))
    from installer.steps import STEPS, run_all

    if len(sys.argv) > 1:
        step_name = sys.argv[1]
        if step_name not in STEPS:
            print(f"[X] Étape inconnue : {step_name}")
            print(f"Étapes disponibles : {', '.join(STEPS.keys())}")
            sys.exit(1)
        STEPS[step_name]()
    else:
        run_all()


if __name__ == "__main__":
    main()
