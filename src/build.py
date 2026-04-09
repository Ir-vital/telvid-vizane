import PyInstaller.__main__
import os
import shutil

# --- Configuration ---
APP_NAME = "TelVid-Vizane"
MAIN_SCRIPT = "main.py"
# Pour un meilleur rendu sur Windows, il est recommandé d'utiliser un fichier .ico
# Vous pouvez convertir votre logo-telvid.png en .ico avec un outil en ligne.
ICON_FILE = os.path.join("icons", "logo-telvid.ico")
# ---

# Chemins des dossiers à inclure
data_to_include = [
    ("icons", "icons"),
    ("locales", "locales")
]

# Construire les arguments pour PyInstaller
pyinstaller_args = [
    MAIN_SCRIPT,
    f'--name={APP_NAME}',
    '--onefile',
    '--windowed',  # Pas de console en arrière-plan
    '--clean',
    '--noconfirm',
]

# Utiliser UPX pour compresser l'exécutable final
pyinstaller_args.append('--upx-dir=.') # Cherche upx.exe dans le dossier courant

# Ajouter l'icône si elle existe
if os.path.exists(ICON_FILE):
    pyinstaller_args.append(f'--icon={ICON_FILE}')
else:
    print(f"Attention : Fichier d'icône non trouvé à l'emplacement {ICON_FILE}. Le build continuera sans icône.")

# Ajouter les données (dossiers)
for src, dest in data_to_include:
    if os.path.exists(src):
        pyinstaller_args.append(f'--add-data={src}{os.pathsep}{dest}')
    else:
        print(f"Attention : Dossier de données '{src}' non trouvé. Il ne sera pas inclus dans le build.")

# Lancer PyInstaller
print("--- Lancement de PyInstaller ---")
PyInstaller.__main__.run(pyinstaller_args)

print("\n--- Build terminé ---")
print(f"L'exécutable se trouve dans le dossier : {os.path.join(os.path.abspath(os.path.dirname(__file__)), 'dist')}")