#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path


def apt_update():
    """Rafraîchit le cache des paquets (sudo apt update)."""
    subprocess.run(["sudo", "apt", "update"], check=True)


def upgrade_package_if_needed(package_name):
    """Vérifie et met à jour un paquet de manière 100 % fiable."""
    apt_update()

    # Simulation en anglais standard
    env = {**os.environ, "LC_ALL": "C"}
    check_cmd = ["apt-get", "-s", "install", "--only-upgrade", package_name]
    result = subprocess.run(check_cmd, capture_output=True, text=True, env=env)

    # Si "Inst <nom_du_paquet>" n'est PAS dans la sortie, le paquet est déjà à jour
    if f"Inst {package_name}" not in result.stdout:
        print(f"===> {package_name} est déjà la version la plus récente.")
        return False

    print(f"\n===> Une mise à jour de {package_name} est disponible, installation...")
    try:
        subprocess.run(
            ["sudo", "apt", "install", "--only-upgrade", "-y", package_name],
            check=True,
        )
        print(f"===> {package_name} mis à jour avec succès !")
        return True
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Erreur lors de la mise à jour de {package_name} : {error}")
        sys.exit(1)


def install_git():
    """Installe git s'il n'est pas déjà présent (nécessaire pour cloner .dotfiles)."""
    print("\n=== Installation de Git ===\n")

    if shutil.which("git"):
        print("===> Git est déjà installé.")
        return

    try:
        apt_update()
        subprocess.run(["sudo", "apt", "install", "-y", "git"], check=True)
        print("\n==> Git installé avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de Git : {error}")
        sys.exit(1)


def clone_dotfiles():
    """Clone le dépôt .dotfiles dans ~/.dotfiles s'il n'existe pas déjà."""
    print("\n=== Clonage du dépôt .dotfiles ===\n")

    dotfiles_dir = Path.home() / ".dotfiles"
    if dotfiles_dir.exists():
        print(f"===> {dotfiles_dir} existe déjà, clonage ignoré.")
        return

    try:
        subprocess.run(
            [
                "git", "clone",
                "https://github.com/Ghislain-KIMA/.dotfiles.git",
                str(dotfiles_dir),
            ],
            check=True,
        )
        print(f"\n==> Dépôt cloné avec succès dans {dotfiles_dir} !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors du clonage : {error}")
        sys.exit(1)


def system_update():
    print("\n=== Lancement de la mise à jour du système ===\n")

    try:
        apt_update()
        subprocess.run(["sudo", "apt", "upgrade", "-y"], check=True)
        print("\n==> Système mis à jour avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de la mise à jour du système : {error}")
        sys.exit(1)


# Paquets .deb "simples" : téléchargement direct, sans dépôt APT propre.
# Adapté uniquement aux logiciels qui n'ajoutent pas leur propre dépôt à l'installation.
DEB_PACKAGES = [
    {
        "name": "Google Chrome",
        "binary": "google-chrome",
        "url": "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
    },
]


def install_deb_packages(packages):
    """Parcourt une liste de paquets .deb et les installe s'ils ne sont pas présents."""
    for pkg in packages:
        name = pkg["name"]
        binary = pkg["binary"]
        url = pkg["url"]

        print(f"\n=== Installation de {name} ===\n")

        if shutil.which(binary):
            print(f"===> {name} est déjà installé.")
            continue

        deb_path = f"/tmp/{binary}.deb"

        try:
            print(f"\n==> Téléchargement de {name}...")
            subprocess.run(["wget", url, "-O", deb_path], check=True)

            print(f"\n==> Installation de {name}...")
            subprocess.run(["sudo", "apt", "install", "-y", deb_path], check=True)
            print(f"\n==> {name} installé avec succès !")

        except subprocess.CalledProcessError as error:
            print(f"\n[X] Une erreur est survenue lors de l'installation de {name} : {error}")
            sys.exit(1)
        finally:
            if os.path.exists(deb_path):
                os.remove(deb_path)


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


def install_apt_packages(packages):
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


def compute_sha256(file_path):
    """Calcule le SHA-256 d'un fichier par blocs, sans le charger entièrement en mémoire."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


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


def install_vscode():
    """Installe VS Code via le dépôt APT officiel Microsoft (pas de .deb brut).

    Pourquoi cette méthode plutôt qu'un .deb téléchargé directement :
    - Pas de SHA256 stable disponible pour l'URL "dernière version" de VS Code.
    - Le dépôt APT est signé par une clé GPG, vérifiée à CHAQUE mise à jour future
      (pas seulement au premier téléchargement) -> plus robuste qu'un SHA256 ponctuel.
    - VS Code redevient alors un paquet apt normal, mis à jour par system_update().
    """
    print("\n=== Installation de VS Code ===\n")

    if shutil.which("code"):
        upgrade_package_if_needed("code")
        return

    try:
        subprocess.run(
            "wget -qO- https://packages.microsoft.com/keys/microsoft.asc | "
            "gpg --dearmor > /tmp/microsoft.gpg",
            shell=True,
            check=True,
        )
        subprocess.run(
            [
                "sudo", "install", "-D", "-o", "root", "-g", "root", "-m", "644",
                "/tmp/microsoft.gpg", "/etc/apt/keyrings/packages.microsoft.gpg",
            ],
            check=True,
        )
        os.remove("/tmp/microsoft.gpg")

        subprocess.run(
            "echo 'deb [arch=amd64,arm64,armhf "
            "signed-by=/etc/apt/keyrings/packages.microsoft.gpg] "
            "https://packages.microsoft.com/repos/code stable main' | "
            "sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null",
            shell=True,
            check=True,
        )

        apt_update()
        subprocess.run(["sudo", "apt", "install", "-y", "code"], check=True)
        print("\n==> VS Code installé avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de VS Code : {error}")
        sys.exit(1)


def install_edge():
    """Installe Microsoft Edge via le dépôt APT officiel (même clé GPG que VS Code).

    Le lien de téléchargement direct .deb d'Edge n'est pas vraiment stable
    (le nom exact du fichier change à chaque nouvelle version) -> on privilégie
    le dépôt APT, qui reste à la même URL indéfiniment et se met à jour tout
    seul via system_update() une fois installé.
    """
    print("\n=== Installation de Microsoft Edge ===\n")

    if shutil.which("microsoft-edge"):
        upgrade_package_if_needed("microsoft-edge-stable")
        return

    try:
        subprocess.run(
            "wget -qO- https://packages.microsoft.com/keys/microsoft.asc | "
            "gpg --dearmor > /tmp/microsoft.gpg",
            shell=True,
            check=True,
        )
        subprocess.run(
            [
                "sudo", "install", "-D", "-o", "root", "-g", "root", "-m", "644",
                "/tmp/microsoft.gpg", "/etc/apt/keyrings/packages.microsoft.gpg",
            ],
            check=True,
        )
        os.remove("/tmp/microsoft.gpg")

        subprocess.run(
            "echo 'deb [arch=amd64 "
            "signed-by=/etc/apt/keyrings/packages.microsoft.gpg] "
            "https://packages.microsoft.com/repos/edge stable main' | "
            "sudo tee /etc/apt/sources.list.d/microsoft-edge.list > /dev/null",
            shell=True,
            check=True,
        )

        apt_update()
        subprocess.run(["sudo", "apt", "install", "-y", "microsoft-edge-stable"], check=True)
        print("\n==> Microsoft Edge installé avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation d'Edge : {error}")
        sys.exit(1)


def install_docker():
    """Installe Docker via le dépôt APT officiel (docker-ce), pas le "docker.io" d'Ubuntu.

    Le paquet "docker.io" des dépôts Ubuntu standards est généralement une
    version plus ancienne que celle du dépôt officiel Docker -> on ajoute
    donc leur dépôt + clé GPG, comme pour VS Code et Edge.
    """
    print("\n=== Installation de Docker ===\n")

    if shutil.which("docker"):
        upgrade_package_if_needed("docker-ce")
        return

    try:
        # Retire d'éventuels paquets Docker conflictuels installés autrement
        conflicting = ["docker.io", "docker-doc", "docker-compose", "podman-docker", "containerd", "runc"]
        subprocess.run(["sudo", "apt", "remove", "-y", *conflicting], check=False)

        subprocess.run(["sudo", "install", "-m", "0755", "-d", "/etc/apt/keyrings"], check=True)
        subprocess.run(
            "wget -qO- https://download.docker.com/linux/ubuntu/gpg | "
            "gpg --dearmor | sudo tee /etc/apt/keyrings/docker.gpg > /dev/null",
            shell=True,
            check=True,
        )
        subprocess.run(["sudo", "chmod", "a+r", "/etc/apt/keyrings/docker.gpg"], check=True)

        arch = subprocess.run(
            ["dpkg", "--print-architecture"], capture_output=True, text=True, check=True
        ).stdout.strip()
        codename = subprocess.run(
            ". /etc/os-release && echo \"$VERSION_CODENAME\"",
            shell=True, capture_output=True, text=True, check=True
        ).stdout.strip()

        subprocess.run(
            f"echo 'deb [arch={arch} signed-by=/etc/apt/keyrings/docker.gpg] "
            f"https://download.docker.com/linux/ubuntu {codename} stable' | "
            "sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
            shell=True,
            check=True,
        )

        apt_update()
        subprocess.run(
            [
                "sudo", "apt", "install", "-y",
                "docker-ce", "docker-ce-cli", "containerd.io",
                "docker-buildx-plugin", "docker-compose-plugin",
            ],
            check=True,
        )

        # Permet d'utiliser `docker` sans sudo (effectif après reconnexion/redémarrage)
        subprocess.run(
            ["sudo", "usermod", "-aG", "docker", os.environ.get("USER", "")], check=True
        )
        print("\n==> Docker installé avec succès !")
        print("===> Redémarre ta session pour utiliser `docker` sans sudo.")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de Docker : {error}")
        sys.exit(1)


def install_virtualbox():
    """Installe VirtualBox via le dépôt Ubuntu standard.

    Le dépôt officiel Oracle ne supporte pas encore certaines versions
    récentes d'Ubuntu (ex: resolute/26.04 au moment de l'écriture) -> on
    utilise le dépôt Ubuntu standard, largement suffisant pour un usage
    courant (VM Kali, tests réseau, dossiers partagés).

    L'extension pack affichera un écran de licence INTERACTIF à l'installation
    (le script reste volontairement en mode interactif) -> réponds "yes"/accepter
    quand demandé.
    """
    print("\n=== Installation de VirtualBox ===\n")

    if shutil.which("vboxmanage"):
        print("===> VirtualBox est déjà installé.")
        return

    try:
        apt_update()
        subprocess.run(
            ["sudo", "apt", "install", "-y", "virtualbox", "virtualbox-ext-pack"],
            check=True,
        )
        print("\n==> VirtualBox installé avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de VirtualBox : {error}")
        sys.exit(1)


def install_vscode_extensions():
    """Réinstalle les extensions VS Code listées dans ~/.dotfiles/vscode/extensions.txt.

    On cible toujours ~/.dotfiles/ (chemin fixe) plutôt que le dossier du script
    lui-même : lors du tout premier lancement (script récupéré via wget, en dehors
    de .dotfiles), clone_dotfiles() vient de créer ~/.dotfiles/ un peu plus tôt
    dans l'exécution -> c'est cet emplacement, garanti à jour, qu'il faut lire.
    """
    print("\n=== Installation des extensions VS Code ===\n")

    extensions_file = Path.home() / ".dotfiles" / "vscode" / "extensions.txt"
    if not extensions_file.exists():
        print(f"===> Fichier {extensions_file} introuvable, étape ignorée.")
        return

    extensions = [
        line.strip()
        for line in extensions_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    for ext in extensions:
        print(f"\n--> Installation de {ext}...")
        # check=False : une extension en échec (renommée, retirée du marketplace...)
        # ne doit pas interrompre l'installation des suivantes.
        subprocess.run(["code", "--install-extension", ext], check=False)

    print(f"\n==> {len(extensions)} extension(s) traitée(s).")


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


STEPS = {
    "git": install_git,
    "clone": clone_dotfiles,
    "update": system_update,
    "chrome": lambda: install_deb_packages(DEB_PACKAGES),
    "vscode": install_vscode,
    "edge": install_edge,
    "docker": install_docker,
    "virtualbox": install_virtualbox,
    "tools": lambda: install_apt_packages(APT_PACKAGES),
    "drawio": install_drawio,
    "extensions": install_vscode_extensions,
    "claude": install_claude_desktop,
}


def run_all():
    for step in STEPS.values():
        step()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        step_name = sys.argv[1]
        if step_name not in STEPS:
            print(f"[X] Étape inconnue : {step_name}")
            print(f"Étapes disponibles : {', '.join(STEPS.keys())}")
            sys.exit(1)
        STEPS[step_name]()
    else:
        run_all()
