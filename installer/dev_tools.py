"""Outils de développement : VS Code, Docker, VirtualBox, Node.js, Miniconda."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

from installer.core import apt_update, upgrade_package_if_needed, compute_sha256
from installer.config import (
    NVM_DIR,
    CONDA_DIR,
    NVM_VERSION,
    NODE_VERSION,
    MINICONDA_FILENAME,
    MINICONDA_SHA256,
    MINICONDA_URL,
)


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


def install_nodejs():
    """Installe Node.js via NVM (Node Version Manager), sans sudo.

    Pas de dépôt APT ici volontairement : NVM permet de changer de version
    de Node facilement, ne nécessite aucun privilège root (tout s'installe
    dans ~/.nvm), et c'est la méthode officiellement recommandée par le
    projet nvm-sh lui-même.
    """
    print("\n=== Installation de Node.js (via NVM) ===\n")

    if not (NVM_DIR / "nvm.sh").exists():
        try:
            subprocess.run(
                f"wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/{NVM_VERSION}/install.sh | bash",
                shell=True,
                check=True,
            )
            print("\n==> NVM installé avec succès !")
        except subprocess.CalledProcessError as error:
            print(f"\n[X] Une erreur est survenue lors de l'installation de NVM : {error}")
            sys.exit(1)
    else:
        print("===> NVM est déjà installé.")

    # nvm est une fonction shell (chargée via nvm.sh), pas un exécutable :
    # on doit la charger et l'appeler dans le même processus bash.
    try:
        subprocess.run(
            f'export NVM_DIR="{NVM_DIR}"; . "$NVM_DIR/nvm.sh"; '
            f"nvm install {NODE_VERSION} && node -v && npm -v",
            shell=True,
            check=True,
        )
        print(f"\n==> Node.js {NODE_VERSION} installé avec succès via NVM !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de Node.js : {error}")
        sys.exit(1)


def install_miniconda():
    """Installe Miniconda : version épinglée + SHA-256 vérifié (pas de dépôt APT officiel).

    Version et somme à mettre à jour manuellement depuis https://repo.anaconda.com/miniconda/
    (dans installer/config.py).
    """
    print("\n=== Installation de Miniconda ===\n")

    if shutil.which("conda"):
        print("===> Miniconda est déjà installé (mise à jour manuelle : `conda update conda`).")
        return

    try:
        installer_path = Path("/tmp") / MINICONDA_FILENAME
        subprocess.run(["wget", MINICONDA_URL, "-O", str(installer_path)], check=True)

        print("==> Vérification du SHA-256...")
        computed = compute_sha256(installer_path)
        if computed != MINICONDA_SHA256:
            installer_path.unlink()
            print(
                f"\n[X] SHA-256 invalide pour Miniconda !\n"
                f"Attendu : {MINICONDA_SHA256}\n"
                f"Obtenu  : {computed}\n"
                f"Fichier supprimé par sécurité."
            )
            sys.exit(1)
        print("===> SHA-256 vérifié avec succès.")

        subprocess.run(
            ["bash", str(installer_path), "-b", "-u", "-p", str(CONDA_DIR)], check=True
        )
        installer_path.unlink()
        subprocess.run([str(CONDA_DIR / "bin" / "conda"), "init", "bash"], check=True)
        print("\n==> Miniconda installé avec succès ! (redémarre ton terminal)")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de l'installation de Miniconda : {error}")
        sys.exit(1)
