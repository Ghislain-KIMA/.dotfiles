#!/usr/bin/env python3
import hashlib
import os
import subprocess
from pathlib import Path


def run(cmd, shell=False, check=True, env=None):
    """Exécute une commande système, avec un bip si une saisie sudo est attendue."""
    cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
    needs_input = cmd_str.strip().startswith("sudo")

    if needs_input:
        print("\a", end="", flush=True)  # bip sonore avant une saisie sudo probable

    print(f"\n--> Exécution : {cmd_str}")
    subprocess.run(cmd, shell=shell, check=check, env=env)


def compute_sha256(file_path):
    """Calcule le SHA-256 d'un fichier par blocs, sans le charger entièrement en mémoire."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def main():
    home = Path.home()
    # Personnalisable via la variable d'environnement INSTALL_DIR
    # (ex: INSTALL_DIR=~/.local python3 my_ubuntu.py)
    install_dir = Path(os.environ.get("INSTALL_DIR", str(home / "installed"))).expanduser()
    install_dir.mkdir(parents=True, exist_ok=True)

    apps_dir = home / ".local" / "share" / "applications"
    apps_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Dossier d'installation ciblé : {install_dir} ===")

    # -------------------------------------------------------------
    # 1. Paquets système (APT) : Incontournables
    # -------------------------------------------------------------
    print("\n=== 1. Installation des paquets système via APT ===")
    run(["sudo", "apt", "update"])

    # Pré-accepte la licence VirtualBox Extension Pack (évite un prompt bloquant)
    run(
        "echo 'virtualbox-ext-pack virtualbox-ext-pack/license note' | sudo debconf-set-selections",
        shell=True,
    )
    run(
        [
            "sudo",
            "-E",
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
        ],
        env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"},
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

    # Docker (dépôt officiel + clé GPG)
    print("\n=== Installation de Docker ===")
    run(
        "for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; "
        "do sudo apt remove -y $pkg 2>/dev/null || true; done",
        shell=True,
    )
    run(["sudo", "install", "-m", "0755", "-d", "/etc/apt/keyrings"])
    run(
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | "
        "sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
        shell=True,
    )
    run(["sudo", "chmod", "a+r", "/etc/apt/keyrings/docker.gpg"])
    run(
        'echo "deb [arch=$(dpkg --print-architecture) '
        "signed-by=/etc/apt/keyrings/docker.gpg] "
        "https://download.docker.com/linux/ubuntu "
        '$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | '
        "sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
        shell=True,
    )
    run(["sudo", "apt", "update"])
    run(
        [
            "sudo",
            "apt",
            "install",
            "-y",
            "docker-ce",
            "docker-ce-cli",
            "containerd.io",
            "docker-buildx-plugin",
            "docker-compose-plugin",
        ]
    )
    # Permet d'utiliser `docker` sans sudo (effectif après reconnexion/redémarrage)
    run(["sudo", "usermod", "-aG", "docker", os.environ.get("USER", "")])

    # Claude Desktop (dépôt APT officiel Anthropic + clé GPG)
    print("\n=== Installation de Claude Desktop ===")
    run(
        [
            "sudo",
            "curl",
            "-fsSLo",
            "/usr/share/keyrings/claude-desktop-archive-keyring.asc",
            "https://downloads.claude.ai/claude-desktop/key.asc",
        ]
    )
    # Vérification de l'empreinte de la clé (fingerprint officiel documenté par Anthropic)
    fingerprint_check = subprocess.run(
        ["gpg", "--show-keys", "/usr/share/keyrings/claude-desktop-archive-keyring.asc"],
        capture_output=True,
        text=True,
    )
    expected_fingerprint = "31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE"
    if expected_fingerprint not in fingerprint_check.stdout.replace(" ", ""):
        raise RuntimeError(
            f"Empreinte GPG invalide pour Claude Desktop !\n"
            f"Attendue : {expected_fingerprint}\n"
            f"Obtenue  : {fingerprint_check.stdout}\n"
            f"Installation annulée par sécurité."
        )
    print("--> Empreinte GPG vérifiée avec succès.")

    run(
        "echo 'deb [signed-by=/usr/share/keyrings/claude-desktop-archive-keyring.asc] "
        "https://downloads.claude.ai/claude-desktop/apt/stable stable main' | "
        "sudo tee /etc/apt/sources.list.d/claude-desktop.list > /dev/null",
        shell=True,
    )
    run(["sudo", "apt", "update"])
    run(["sudo", "apt", "install", "-y", "claude-desktop"])

    # -------------------------------------------------------------
    # 2. Logiciels installés dans install_dir (voir INSTALL_DIR)
    # -------------------------------------------------------------
    print(f"\n=== 2. Installation des logiciels dans {install_dir}/ ===")

    # --- VS Code (dépôt APT officiel Microsoft, signé par clé GPG) ---
    print("--> Installation de VS Code (dépôt APT officiel)...")
    run(
        "wget -qO- https://packages.microsoft.com/keys/microsoft.asc | "
        "gpg --dearmor > /tmp/vscode.gpg",
        shell=True,
    )
    run(
        [
            "sudo",
            "install",
            "-D",
            "-o",
            "root",
            "-g",
            "root",
            "-m",
            "644",
            "/tmp/vscode.gpg",
            "/etc/apt/keyrings/packages.microsoft.gpg",
        ]
    )
    os.remove("/tmp/vscode.gpg")
    run(
        "echo 'deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] "
        "https://packages.microsoft.com/repos/code stable main' | "
        "sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null",
        shell=True,
    )
    run(["sudo", "apt", "update"])
    run(["sudo", "apt", "install", "-y", "code"])

    # --- Android Studio (archive officielle .tar.gz + vérification SHA-256) ---
    # Version et somme à mettre à jour manuellement depuis https://developer.android.com/studio
    print("--> Installation d'Android Studio...")
    ANDROID_STUDIO_VERSION = "2026.1.3.8"
    ANDROID_STUDIO_FILENAME = "android-studio-quail3-patch1-linux.tar.gz"
    ANDROID_STUDIO_SHA256 = (
        "5bd5ee5d6e747b13f82fba3241380bd358cc2f4a847815c8e860757df13dc35f"
    )
    ANDROID_STUDIO_URL = (
        f"https://edgedl.me.gvt1.com/android/studio/ide-zips/"
        f"{ANDROID_STUDIO_VERSION}/{ANDROID_STUDIO_FILENAME}"
    )

    android_studio_dir = install_dir / "android-studio"
    if not android_studio_dir.exists():
        archive_path = Path("/tmp") / ANDROID_STUDIO_FILENAME
        run(["wget", ANDROID_STUDIO_URL, "-O", str(archive_path)])

        # Vérification de l'intégrité (SHA-256)
        print("--> Vérification du SHA-256...")
        computed = compute_sha256(archive_path)

        if computed != ANDROID_STUDIO_SHA256:
            archive_path.unlink()
            raise RuntimeError(
                f"SHA-256 invalide pour Android Studio !\n"
                f"Attendu : {ANDROID_STUDIO_SHA256}\n"
                f"Obtenu  : {computed}\n"
                f"Le fichier téléchargé a été supprimé par sécurité."
            )
        print("--> SHA-256 vérifié avec succès.")

        run(["tar", "-xzf", str(archive_path), "-C", str(install_dir)])
        archive_path.unlink()

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

    # --- Miniconda (version épinglée + vérification SHA-256) ---
    # Version et somme à mettre à jour manuellement depuis https://repo.anaconda.com/miniconda/
    print("--> Installation de Miniconda...")
    MINICONDA_FILENAME = "Miniconda3-py314_26.5.3-2-Linux-x86_64.sh"
    MINICONDA_SHA256 = (
        "80bc27f13c4de90f10e387aa45e864de4f0860692c1221aef5900009a2b55302"
    )
    MINICONDA_URL = f"https://repo.anaconda.com/miniconda/{MINICONDA_FILENAME}"

    conda_dir = install_dir / "miniconda3"
    if not conda_dir.exists():
        installer_path = Path("/tmp") / MINICONDA_FILENAME
        run(["wget", MINICONDA_URL, "-O", str(installer_path)])

        # Vérification de l'intégrité (SHA-256)
        print("--> Vérification du SHA-256...")
        computed = compute_sha256(installer_path)

        if computed != MINICONDA_SHA256:
            installer_path.unlink()
            raise RuntimeError(
                f"SHA-256 invalide pour Miniconda !\n"
                f"Attendu : {MINICONDA_SHA256}\n"
                f"Obtenu  : {computed}\n"
                f"Le fichier téléchargé a été supprimé par sécurité."
            )
        print("--> SHA-256 vérifié avec succès.")

        run(["bash", str(installer_path), "-b", "-u", "-p", str(conda_dir)])
        installer_path.unlink()
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

    marker = f"# --- Configurations de vos outils dans {install_dir} ---"
    path_additions = f"""
{marker}
export PATH="{install_dir}/flutter/bin:$PATH"
export PATH="{install_dir}/android-studio/bin:$PATH"
export NVM_DIR="{install_dir}/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \\. "$NVM_DIR/nvm.sh"
"""

    if marker not in bashrc_content:
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
        "claude": ("Claude", "https://claude.ai"),
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
    print(f" Tout est installé dans {install_dir}/ et configuré !")
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
