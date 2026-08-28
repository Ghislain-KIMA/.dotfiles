"""Configuration post-installation : services à désactiver, réglages divers.

Certains paquets démarrent et activent leur service automatiquement dès
l'installation (ex: PostgreSQL). Ce module regroupe les ajustements à
appliquer une fois que tout est installé.
"""
import subprocess

# Services installés en tant que dépendances mais qu'on ne veut pas voir
# tourner en permanence ni démarrer automatiquement au boot.
SERVICES_TO_DISABLE = [
    "postgresql",
]


def disable_service(service_name):
    """Arrête un service s'il tourne, et désactive son démarrage automatique."""
    active = subprocess.run(
        ["systemctl", "is-active", service_name], capture_output=True, text=True
    ).stdout.strip()
    if active == "active":
        print(f"--> Arrêt de {service_name}...")
        subprocess.run(["sudo", "systemctl", "stop", service_name], check=False)

    enabled = subprocess.run(
        ["systemctl", "is-enabled", service_name], capture_output=True, text=True
    ).stdout.strip()

    if enabled in ("disabled", "masked"):
        print(f"===> {service_name} est déjà désactivé.")
        return
    if enabled not in ("enabled", "enabled-runtime", "generated", "static", "indirect", "alias"):
        # Service introuvable ou pas géré par systemd -> ignoré silencieusement
        print(f"===> {service_name} introuvable, ignoré.")
        return

    subprocess.run(["sudo", "systemctl", "disable", service_name], check=False)
    print(f"===> {service_name} désactivé (arrêté + pas de démarrage automatique).")


def apply_post_config():
    """Applique tous les ajustements post-installation."""
    print("\n=== Configuration post-installation ===\n")
    for service in SERVICES_TO_DISABLE:
        disable_service(service)
