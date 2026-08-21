#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path


def run(cmd, shell=False, check=True, env=None):
    """Exécute une commande système, avec un bip si une saisie sudo est attendue."""
    cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
    needs_input = cmd_str.strip().startswith("sudo")

    if needs_input:
        print("\a", end="", flush=True)  # bip sonore avant une saisie sudo probable

    print(f"\n--> Exécution : {cmd_str}")
    subprocess.run(cmd, shell=shell, check=check, env=env)


def main():
    home = Path.home()
    install_dir = home / "installed"
    install_dir.mkdir(parents=True, exist_ok=True)

    apps_dir = home / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)

    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Dossier d'installation ciblé : {install_dir} ===")

    # -------------------------------------------------------------
    # 1. Paquets système (APT) : Incontournables
    # -------------------------------------------------------------
    print("\n=== 1. Installation des paquets système via APT ===")
    run(["sudo", "apt", "update"])
    run(
        [
            "sudo",
            "apt",
            "install",
            "-y",
            "build-essential",
            "gcc",
            "g++",
            "git",
            "default-jdk",
            "rclone",
            "sqlitebrowser",
            "postgresql",
            "postgresql-contrib",
            "virtualbox",
            "virtualbox-ext-pack",
            "inkscape",
            "curl",
            "wget",
            "unzip",
            "tar",
            "xz-utils",
        ]
    )

    # Navigateurs système (.deb obligatoire pour sandbox/sécurité)
    print("\n=== Installation de Google Chrome & Microsoft Edge ===")
    run(
        [
            "wget",
            "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
            "-O",
            "/tmp/chrome.deb",
        ]
    )
    run(["sudo", "apt", "install", "-y", "/tmp/chrome.deb"])
    os.remove("/tmp/chrome.deb")

    run(
        "curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /tmp/microsoft.gpg",
        shell=True,
    )
    run(
        [
            "sudo",
            "install",
            "-o",
            "root",
            "-g",
            "root",
            "-m",
            "644",
            "/tmp/microsoft.gpg",
            "/etc/apt/trusted.gpg.d/",
        ]
    )
    run(
        "echo 'deb [arch=amd64] https://packages.microsoft.com/repos/edge stable main' | sudo tee /etc/apt/sources.list.d/microsoft-edge.list > /dev/null",
        shell=True,
    )
    run(["sudo", "apt", "update"])
    run(["sudo", "apt", "install", "-y", "microsoft-edge-stable"])

    # -------------------------------------------------------------
    # 2. Logiciels installés dans ~/installed/
    # -------------------------------------------------------------
    print("\n=== 2. Installation des logiciels dans ~/installed/ ===")

    # --- VS Code (Archive tar.gz) ---
    print("--> Installation de VS Code...")
    vscode_dir = install_dir / "vscode"
    if not vscode_dir.exists():
        run(
            [
                "wget",
                "https://code.visualstudio.com/sha/download?build=stable&os=linux-x64",
                "-O",
                "/tmp/vscode.tar.gz",
            ]
        )
        vscode_dir.mkdir(parents=True, exist_ok=True)
        run(["tar", "-xzf", "/tmp/vscode.tar.gz", "-C", str(vscode_dir), "--strip-components=1"])
        os.remove("/tmp/vscode.tar.gz")

        # Raccourci .desktop
        (apps_dir / "code.desktop").write_text(f"""[Desktop Entry]
Name=Visual Studio Code
Exec={vscode_dir}/bin/code %F
Icon={vscode_dir}/resources/app/resources/linux/code.png
Type=Application
Categories=Development;IDE;
""")

    # --- Android Studio (Archive tar.gz) ---
    print("--> Installation d'Android Studio...")
    android_studio_dir = install_dir / "android-studio"
    if not android_studio_dir.exists():
        # Téléchargement de la dernière version stable
        run(
            [
                "wget",
                "https://redirector.gvt1.com/edgedl/android/studio/ide-zips/2023.3.1.18/android-studio-2023.3.1.18-linux.tar.gz",
                "-O",
                "/tmp/android-studio.tar.gz",
            ]
        )
        run(["tar", "-xzf", "/tmp/android-studio.tar.gz", "-C", str(install_dir)])
        os.remove("/tmp/android-studio.tar.gz")

        (apps_dir / "android-studio.desktop").write_text(f"""[Desktop Entry]
Name=Android Studio
Exec={android_studio_dir}/bin/studio.sh
Icon={android_studio_dir}/bin/studio.png
Type=Application
Categories=Development;IDE;
""")

    # --- Flutter SDK ---
    print("--> Installation du SDK Flutter...")
    flutter_dir = install_dir / "flutter"
    if not flutter_dir.exists():
        run(
            [
                "git",
                "clone",
                "https://github.com/flutter/flutter.git",
                "-b",
                "stable",
                str(flutter_dir),
            ]
        )

    # --- Miniconda ---
    print("--> Installation de Miniconda...")
    conda_dir = install_dir / "miniconda3"
    if not conda_dir.exists():
        run(
            [
                "wget",
                "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh",
                "-O",
                "/tmp/miniconda.sh",
            ]
        )
        run(["bash", "/tmp/miniconda.sh", "-b", "-u", "-p", str(conda_dir)])
        os.remove("/tmp/miniconda.sh")
        run([str(conda_dir / "bin" / "conda"), "init", "bash"])

    # --- Node.js via NVM ---
    print("--> Installation de NVM & Node.js...")
    nvm_dir = install_dir / "nvm"
    os.environ["NVM_DIR"] = str(nvm_dir)
    nvm_dir.mkdir(parents=True, exist_ok=True)
    run(
        "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash",
        shell=True,
    )

    # -------------------------------------------------------------
    # 3. Mettre à jour le fichier ~/.bashrc (PATH)
    # -------------------------------------------------------------
    print("\n=== 3. Configuration des variables d'environnement (PATH) ===")
    bashrc = home / ".bashrc"
    bashrc_content = bashrc.read_text() if bashrc.exists() else ""

    path_additions = f"""
# --- Configurations de vos outils dans ~/installed ---
export PATH="$HOME/installed/vscode/bin:$PATH"
export PATH="$HOME/installed/flutter/bin:$PATH"
export PATH="$HOME/installed/android-studio/bin:$PATH"
export NVM_DIR="$HOME/installed/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
"""

    if "# --- Configurations de vos outils dans ~/installed ---" not in bashrc_content:
        with open(bashrc, "a") as f:
            f.write(path_additions)

    # -------------------------------------------------------------
    # 4. Web Apps Chrome
    # -------------------------------------------------------------
    print("\n=== 4. Création des raccourcis Web Apps Chrome ===")
    web_apps = {
        "notebooklm": ("NotebookLM", "https://notebooklm.google.com"),
        "deepseek": ("DeepSeek", "https://chat.deepseek.com"),
        "copilot": ("Microsoft Copilot", "https://copilot.microsoft.com"),
        "gemini": ("Google Gemini", "https://gemini.google.com"),
        "whatsapp": ("WhatsApp Web", "https://web.whatsapp.com"),
        "github": ("GitHub", "https://github.com"),
        "gdrive": ("Google Drive", "https://drive.google.com"),
        "youtube": ("YouTube", "https://youtube.com"),
        "gmail": ("Gmail", "https://mail.google.com"),
    }

    for app_id, (name, url) in web_apps.items():
        (apps_dir / f"{app_id}.desktop").write_text(f"""[Desktop Entry]
Name={name}
Exec=/usr/bin/google-chrome --app={url}
Icon=google-chrome
Type=Application
Categories=Network;
""")

    # -------------------------------------------------------------
    # 5. Restauration des dotfiles (git, vscode, ...)
    # -------------------------------------------------------------
    setup_dotfiles()

    print("\n==================================================")
    print(" Tout est installé dans ~/installed/ et configuré !")
    print(" Redémarrez le terminal pour appliquer le PATH.")
    print("==================================================")


def setup_dotfiles():
    """Clone le dépôt .dotfiles unique (s'il n'existe pas déjà) et lance restore_dotfiles.py.

    Ce dépôt contient à la fois my_ubuntu.py (ce script) et restore_dotfiles.py,
    donc si my_ubuntu.py a été récupéré seul via curl sur une machine fraîche,
    ce clone permet de récupérer le reste (configs git/vscode, extensions.txt...).
    """
    print("\n=== 5. Restauration des dotfiles (git, vscode, ...) ===")
    home = Path.home()
    dotfiles_dir = home / ".dotfiles"

    if not dotfiles_dir.exists():
        run(
            [
                "git",
                "clone",
                "https://github.com/TON_USER/.dotfiles.git",
                str(dotfiles_dir),
            ]
        )
    else:
        print(f"--> {dotfiles_dir} existe déjà, clonage ignoré.")

    run(["python3", str(dotfiles_dir / "restore_dotfiles.py")])


if __name__ == "__main__":
    main()
