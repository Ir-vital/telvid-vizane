import os
import json
import shutil
import subprocess

# Sauvegarder le fichier de licence actuel
license_file = 'license.json'
license_backup = 'license_backup.json'

# Vérifier si le fichier de licence existe
if os.path.exists(license_file):
    # Créer une sauvegarde
    shutil.copy2(license_file, license_backup)
    print(f"Sauvegarde de la licence créée dans {license_backup}")
    
    # Supprimer le fichier de licence pour forcer le mode gratuit
    os.remove(license_file)
    print("Fichier de licence supprimé temporairement pour afficher le mode gratuit")

# Lancer l'application
print("Lancement de l'application en mode gratuit...")
subprocess.run(["python", "main.py"])

# Restaurer la licence après la fermeture de l'application
if os.path.exists(license_backup):
    shutil.copy2(license_backup, license_file)
    print(f"Licence restaurée depuis {license_backup}")
    
    # Supprimer le fichier de sauvegarde
    os.remove(license_backup)
    print("Fichier de sauvegarde supprimé")

print("Opération terminée.")