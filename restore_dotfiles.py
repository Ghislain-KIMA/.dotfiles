#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path


def run(cmd, shell=False, check=True):
    """Exécute une commande système."""
    print(f"\n--> Exécution : {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    subprocess.run(cmd, shell=shell, check=check)


def install_stow():
    """Installe GNU Stow s'il n'est pas déjà présent."""
    print("=== Installation de Stow ===")
    run(["sudo", "apt", "update"])
    run(["sudo", "apt", "install", "-y", "stow"])


def stow_packages(dotfiles_dir, packages):
    """Lance `stow <package>` pour chaque package donné, depuis dotfiles_dir."""
    print("=== Application des liens symboliques (Stow) ===")
    os.chdir(dotfiles_dir)
    for package in packages:
        run(["stow", package], check=True)


def restore_vscode_extensions(dotfiles_dir):
    """Réinstalle les extensions VS Code depuis dotfiles/vscode/extensions.txt"""
    extensions_file = dotfiles_dir / "vscode" / "extensions.txt"
    if not extensions_file.exists():
        print("Fichier extensions.txt introuvable, étape ignorée.")
        return

    print("=== Réinstallation des extensions VS Code ===")
    extensions = extensions_file.read_text().splitlines()
    for ext in extensions:
        ext = ext.strip()
        if ext:
            run(["code", "--install-extension", ext], check=False)


def main():
    # Ce script est censé se trouver à la racine de ~/dotfiles/
    dotfiles_dir = Path(__file__).resolve().parent

    install_stow()
    stow_packages(dotfiles_dir, ["git", "vscode", "nano", "conda"])
    restore_vscode_extensions(dotfiles_dir)

    print("\n==================================================")
    print(" Configuration restaurée avec succès !")
    print("==================================================")


if __name__ == "__main__":
    main()
