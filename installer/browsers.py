"""Installation des navigateurs : Chrome, Edge."""
import os
import shutil
import subprocess
import sys

from installer.core import apt_update, upgrade_package_if_needed

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


def install_chrome():
    install_deb_packages(DEB_PACKAGES)


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
