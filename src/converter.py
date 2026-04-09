import os
from threading import Thread

try:
    # moviepy 2.x — l'import direct depuis moviepy
    from moviepy import VideoFileClip
except ImportError:
    try:
        # Fallback moviepy 1.x
        from moviepy.editor import VideoFileClip
    except ImportError:
        VideoFileClip = None

class LocalConverter:
    """Gère la conversion de fichiers vidéo locaux en fichiers audio MP3."""

    def __init__(self):
        if VideoFileClip is None:
            # Lève une erreur si la bibliothèque est manquante, ce qui sera attrapé dans main.py
            raise ImportError("La bibliothèque 'moviepy' est requise pour la conversion. Veuillez l'installer avec 'pip install moviepy'.")

    def convert_to_audio(self, input_path, completion_callback=None):
        """
        Convertit un fichier vidéo en MP3 dans un thread séparé pour ne pas bloquer l'interface.

        Args:
            input_path (str): Chemin vers le fichier vidéo d'entrée.
            completion_callback (function, optional): Callback appelé à la fin de la conversion.
                                                      Il reçoit (succès, message, chemin_sortie).
        """
        def convert_thread():
            """La fonction qui s'exécute dans le thread."""
            try:
                if not os.path.exists(input_path):
                    if completion_callback:
                        completion_callback(False, "Le fichier d'entrée n'existe pas.", None)
                    return

                # Déterminer le chemin de sortie (même nom, extension .mp3)
                base, _ = os.path.splitext(input_path)
                output_path = base + ".mp3"
                
                # Charger le clip vidéo, extraire l'audio et l'écrire en MP3
                with VideoFileClip(input_path) as video_clip:
                    with video_clip.audio as audio_clip:
                        audio_clip.write_audiofile(output_path, codec='mp3', logger=None) # logger=None pour éviter les prints de moviepy

                if completion_callback:
                    completion_callback(True, "Conversion terminée avec succès !", output_path)

            except Exception as e:
                error_message = str(e)
                if "This error can be due to the fact that ImageMagick is not installed on your computer" in error_message or "check that you have ffmpeg installed" in error_message:
                    error_message = "Erreur de conversion. Assurez-vous que FFMPEG est installé sur votre système et accessible dans le PATH."
                if completion_callback:
                    completion_callback(False, error_message, None)

        # Lancer la conversion dans un thread pour ne pas geler l'application
        Thread(target=convert_thread, daemon=True).start()