"""Divers : petits outils CLI, Draw.io, Claude Desktop."""
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

from installer.core import apt_update, upgrade_package_if_needed, compute_sha256

# Paquets "simples" : déjà présents dans les dépôts Ubuntu par défaut,
# installables directement via apt, sans clé GPG ni dépôt supplémentaire.
# "binary" est utilisé pour vérifier si déjà installé ; "package" est le
# nom exact du paquet apt (parfois différent, ex: fd-find -> binaire fdfind).
APT_PACKAGES = [
    {"name": "ripgrep", "binary": "rg", "package": "ripgrep"},
    {"name": "Inkscape", "binary": "inkscape", "package": "inkscape"},
    {
        "name": "PostgreSQL",
        "binary": "psql",
        "package": ["postgresql", "postgresql-contrib"],
    },
    {"name": "rclone", "binary": "rclone", "package": "rclone"},
]


def install_apt_packages(packages=APT_PACKAGES):
    """Installe en une fois tous les paquets APT simples pas encore présents.

    "package" peut être une chaîne (un seul paquet) ou une liste de chaînes
    (plusieurs paquets liés, ex: postgresql + postgresql-contrib), vérifiés
    ensemble via un seul "binary" représentatif (ex: psql pour PostgreSQL).
    """
    print("\n=== Installation des outils en ligne de commande ===\n")

    to_install = []
    for pkg in packages:
        if shutil.which(pkg["binary"]):
            print(f"===> {pkg['name']} est déjà installé.")
            continue

        package = pkg["package"]
        if isinstance(package, list):
            to_install.extend(package)
        else:
            to_install.append(package)

    if not to_install:
        return

    try:
        apt_update()
        subprocess.run(["sudo", "apt", "install", "-y", *to_install], check=True)
        print(f"\n==> Installés avec succès : {', '.join(to_install)}")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation : {error}")
        sys.exit(1)


def install_drawio():
    """Installe ou met à jour Draw.io Desktop via l'API GitHub.

    Pas de dépôt APT officiel pour Draw.io -> on récupère dynamiquement l'URL
    et le SHA-256 de la dernière release via l'API GitHub (champ "digest" de
    chaque asset), on compare à la version installée, et on ne télécharge
    que si une mise à jour est réellement nécessaire.
    """
    print("\n=== Installation de Draw.io Desktop ===\n")

    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/jgraph/drawio-desktop/releases/latest"
        )
        with urllib.request.urlopen(req) as response:
            release_data = json.loads(response.read().decode())

        latest_version = release_data["tag_name"].lstrip("v")

        if shutil.which("drawio"):
            # Le paquet dpkg s'appelle "draw.io" (avec un point), pas "drawio"
            # -> confirmé par le message d'apt lors de l'installation
            # ("sélection de « draw.io » au lieu de ...").
            result = subprocess.run(
                ["dpkg-query", "-W", "-f=${Version}", "draw.io"],
                capture_output=True,
                text=True,
            )
            installed_version = result.stdout.strip()
            # Comparaison approximative : le tag GitHub (ex: "28.0.6") est
            # généralement inclus dans la version dpkg (ex: "28.0.6-1").
            if latest_version in installed_version:
                print(f"===> Draw.io est déjà à jour ({installed_version}).")
                return
            print(
                f"===> Mise à jour disponible : "
                f"{installed_version} -> {latest_version}, installation..."
            )

        asset = next(
            a for a in release_data["assets"]
            if a["name"].endswith(".deb") and "amd64" in a["name"]
        )
        url = asset["browser_download_url"]
        expected_sha256 = asset["digest"].removeprefix("sha256:")

        deb_path = Path("/tmp") / asset["name"]
        print(f"\n==> Téléchargement de {asset['name']}...")
        subprocess.run(["wget", url, "-O", str(deb_path)], check=True)

        print("==> Vérification du SHA-256...")
        computed = compute_sha256(deb_path)
        if computed != expected_sha256:
            deb_path.unlink()
            print(
                f"\n[X] SHA-256 invalide pour Draw.io !\n"
                f"Attendu : {expected_sha256}\n"
                f"Obtenu  : {computed}\n"
                f"Fichier supprimé par sécurité."
            )
            sys.exit(1)
        print("===> SHA-256 vérifié avec succès.")

        subprocess.run(["sudo", "apt", "install", "-y", str(deb_path)], check=True)
        deb_path.unlink()
        print("\n==> Draw.io installé avec succès !")

    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de Draw.io : {error}")
        sys.exit(1)


def install_claude_desktop():
    """Installe Claude Desktop via le dépôt APT officiel Anthropic, avec vérification GPG."""
    print("\n=== Installation de Claude Desktop ===\n")

    if shutil.which("claude-desktop"):
        upgrade_package_if_needed("claude-desktop")
        return

    try:
        subprocess.run(
            ["wget", "-qO", "/tmp/claude-desktop-key.asc",
             "https://downloads.claude.ai/claude-desktop/key.asc"],
            check=True,
        )
        subprocess.run(
            ["sudo", "install", "-D", "-o", "root", "-g", "root", "-m", "644",
             "/tmp/claude-desktop-key.asc",
             "/usr/share/keyrings/claude-desktop-archive-keyring.asc"],
            check=True,
        )
        os.remove("/tmp/claude-desktop-key.asc")

        result = subprocess.run(
            ["gpg", "--show-keys", "/usr/share/keyrings/claude-desktop-archive-keyring.asc"],
            capture_output=True,
            text=True,
            check=True,
        )
        expected_fingerprint = "31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE"
        if expected_fingerprint not in result.stdout.replace(" ", ""):
            print(
                f"\n[X] Empreinte GPG invalide pour Claude Desktop !\n"
                f"Attendue : {expected_fingerprint}\n"
                f"Obtenue  : {result.stdout}\n"
                f"Installation annulée par sécurité."
            )
            sys.exit(1)
        print("===> Empreinte GPG vérifiée avec succès.")

        subprocess.run(
            "echo 'deb [signed-by=/usr/share/keyrings/claude-desktop-archive-keyring.asc] "
            "https://downloads.claude.ai/claude-desktop/apt/stable stable main' | "
            "sudo tee /etc/apt/sources.list.d/claude-desktop.list > /dev/null",
            shell=True,
            check=True,
        )

        apt_update()
        subprocess.run(["sudo", "apt", "install", "-y", "claude-desktop"], check=True)
        print("\n==> Claude Desktop installé avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de Claude Desktop : {error}")
        sys.exit(1)
