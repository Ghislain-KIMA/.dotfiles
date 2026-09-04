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
    {"name": "tree", "binary": "tree", "package": "tree"},
    {"name": "tealdeer", "binary": "tldr", "package": "tealdeer"},
    {"name": "fzf", "binary": "fzf", "package": "fzf"},
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


def install_rclone():
    """Installe rclone : toujours la dernière version stable, SHA-256 vérifié.

    Le paquet "rclone" des dépôts Ubuntu standards traîne souvent très en
    retard sur les releases officielles -> on télécharge directement depuis
    downloads.rclone.org (lien "current", toujours à jour), et on vérifie
    l'intégrité via le fichier SHA256SUMS publié pour la version exacte
    obtenue (méthode officiellement documentée par rclone.org).
    """
    print("\n=== Installation de rclone ===\n")

    if not shutil.which("unzip"):
        subprocess.run(["sudo", "apt", "install", "-y", "unzip"], check=True)

    try:
        zip_path = Path("/tmp/rclone-current-linux-amd64.zip")
        subprocess.run(
            ["wget", "https://downloads.rclone.org/rclone-current-linux-amd64.zip",
             "-O", str(zip_path)],
            check=True,
        )

        extract_dir = Path("/tmp/rclone_extract")
        shutil.rmtree(extract_dir, ignore_errors=True)
        subprocess.run(["unzip", "-q", "-o", str(zip_path), "-d", str(extract_dir)], check=True)

        # Le zip contient un dossier "rclone-vX.Y.Z-linux-amd64/" -> on en
        # extrait la version exacte pour aller chercher le bon SHA256SUMS.
        release_dir = next(extract_dir.glob("rclone-v*-linux-amd64"))
        version = release_dir.name.removeprefix("rclone-").removesuffix("-linux-amd64")

        if shutil.which("rclone"):
            current = subprocess.run(
                ["rclone", "version"], capture_output=True, text=True
            ).stdout.splitlines()[0]
            if version in current:
                print(f"===> rclone est déjà à jour ({version}).")
                zip_path.unlink()
                shutil.rmtree(extract_dir, ignore_errors=True)
                return
            print(f"===> Mise à jour disponible : {current.strip()} -> {version}")

        print("==> Vérification du SHA-256...")
        sums_url = f"https://downloads.rclone.org/{version}/SHA256SUMS"
        sums_result = subprocess.run(
            ["wget", "-qO-", sums_url], capture_output=True, text=True, check=True
        )
        expected_line = next(
            line for line in sums_result.stdout.splitlines()
            if "rclone-current-linux-amd64.zip" in line or f"rclone-{version}-linux-amd64.zip" in line
        )
        expected_sha256 = expected_line.split()[0]

        computed = compute_sha256(zip_path)
        if computed != expected_sha256:
            zip_path.unlink()
            shutil.rmtree(extract_dir, ignore_errors=True)
            print(
                f"\n[X] SHA-256 invalide pour rclone !\n"
                f"Attendu : {expected_sha256}\n"
                f"Obtenu  : {computed}\n"
                f"Fichiers supprimés par sécurité."
            )
            sys.exit(1)
        print("===> SHA-256 vérifié avec succès.")

        subprocess.run(
            ["sudo", "cp", str(release_dir / "rclone"), "/usr/bin/rclone"], check=True
        )
        subprocess.run(["sudo", "chown", "root:root", "/usr/bin/rclone"], check=True)
        subprocess.run(["sudo", "chmod", "755", "/usr/bin/rclone"], check=True)

        manpage = release_dir / "rclone.1"
        if manpage.exists():
            subprocess.run(["sudo", "mkdir", "-p", "/usr/local/share/man/man1"], check=True)
            subprocess.run(
                ["sudo", "cp", str(manpage), "/usr/local/share/man/man1/rclone.1"], check=True
            )
            subprocess.run(["sudo", "mandb"], check=False)

        zip_path.unlink()
        shutil.rmtree(extract_dir, ignore_errors=True)
        print(f"\n==> rclone {version} installé avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de rclone : {error}")
        sys.exit(1)


def install_obs():
    """Installe OBS Studio via le PPA officiel (ppa:obsproject/obs-studio).

    C'est la méthode officiellement recommandée par obsproject.com/download
    pour Ubuntu 24.04+ (avec Flathub comme seule autre option officielle).
    Donne toujours la dernière version stable, mise à jour automatiquement
    par la suite via system_update() (paquet apt normal une fois le PPA ajouté).
    """
    print("\n=== Installation d'OBS Studio ===\n")

    if shutil.which("obs"):
        upgrade_package_if_needed("obs-studio")
        return

    try:
        if not shutil.which("add-apt-repository"):
            subprocess.run(["sudo", "apt", "install", "-y", "software-properties-common"], check=True)

        subprocess.run(
            ["sudo", "add-apt-repository", "--yes", "--no-update", "multiverse"], check=True
        )
        subprocess.run(
            ["sudo", "add-apt-repository", "--yes", "ppa:obsproject/obs-studio"], check=True
        )

        apt_update()
        subprocess.run(["sudo", "apt", "install", "-y", "obs-studio"], check=True)
        print("\n==> OBS Studio installé avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation d'OBS Studio : {error}")
        sys.exit(1)
