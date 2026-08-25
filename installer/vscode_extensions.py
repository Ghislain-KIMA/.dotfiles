"""Réinstallation des extensions VS Code."""
import subprocess
from pathlib import Path


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
