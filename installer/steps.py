"""Rassemble toutes les étapes d'installation en un dictionnaire unique."""
from installer.core import system_update
from installer.browsers import install_chrome, install_edge
from installer.dev_tools import (
    install_vscode,
    install_docker,
    install_virtualbox,
    install_nodejs,
    install_miniconda,
)
from installer.misc import (
    install_apt_packages,
    install_drawio,
    install_claude_desktop,
    install_rclone,
    install_obs,
)
from installer.vscode_extensions import install_vscode_extensions
from installer.post_config import apply_post_config

STEPS = {
    "update": system_update,
    "chrome": install_chrome,
    "vscode": install_vscode,
    "edge": install_edge,
    "docker": install_docker,
    "virtualbox": install_virtualbox,
    "nodejs": install_nodejs,
    "miniconda": install_miniconda,
    "tools": install_apt_packages,
    "rclone": install_rclone,
    "obs": install_obs,
    "drawio": install_drawio,
    "extensions": install_vscode_extensions,
    "claude": install_claude_desktop,
    "post-config": apply_post_config,
}


def run_all():
    for step in STEPS.values():
        step()
