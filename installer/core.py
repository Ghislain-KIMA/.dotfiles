"""Fonctions utilitaires partagées par tous les autres modules."""
import hashlib
import os
import subprocess
import sys


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


def compute_sha256(file_path):
    """Calcule le SHA-256 d'un fichier par blocs, sans le charger entièrement en mémoire."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def system_update():
    print("\n=== Lancement de la mise à jour du système ===\n")

    try:
        apt_update()
        subprocess.run(["sudo", "apt", "upgrade", "-y"], check=True)
        print("\n==> Système mis à jour avec succès !")
    except subprocess.CalledProcessError as error:
        print(f"\n[X] Une erreur est survenue lors de la mise à jour du système : {error}")
        sys.exit(1)
