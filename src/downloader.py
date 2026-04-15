import os
import yt_dlp
from threading import Thread
import tempfile
import shutil
try:
    from src.logger import log_download_start, log_download_success, log_download_error
except ImportError:
    # Fallback si le logger n'est pas disponible
    def log_download_start(url, format_type="unknown"):
        print(f"Début téléchargement - URL: {url}, Format: {format_type}")
    def log_download_success(url, title, file_path, duration=None):
        print(f"Téléchargement réussi - URL: {url}, Titre: {title}")
    def log_download_error(url, error_message):
        print(f"Erreur téléchargement - URL: {url}, Erreur: {error_message}")


class VideoDownloader:
    """Gère le téléchargement de vidéos en utilisant yt-dlp."""

    def __init__(self):
        pass

    def _get_ydl_opts(self, output_path, format_option, is_premium, progress_callback, pause_event=None):
        """Construit un dictionnaire d'options yt-dlp pour un téléchargement spécifique."""
        temp_dir = tempfile.mkdtemp(prefix="telvid_")

        # Template de sortie selon le format
        if format_option == "audio":
            outtmpl = os.path.join(output_path, '%(title)s.%(ext)s')
        else:
            outtmpl = os.path.join(output_path, '%(title)s.mp4')

        # Wrapper du progress_callback pour gérer la pause
        def progress_with_pause(d):
            if pause_event:
                pause_event.wait()  # Bloque si en pause, continue sinon
            if progress_callback:
                progress_callback(d)

        # Template de sortie selon le format
        if format_option == "audio":
            outtmpl = os.path.join(output_path, '%(title)s.%(ext)s')
        else:
            outtmpl = os.path.join(output_path, '%(title)s.mp4')

        opts = {
            'outtmpl': outtmpl,
            'noplaylist': True,
            'ignoreerrors': True,
            'no_warnings': False,
            'quiet': True,
            'verbose': False,
            'progress_hooks': [progress_with_pause] if progress_callback else [],
            'extractaudio': False,
            'audioformat': 'mp3',
            'audioquality': '320' if is_premium else '128',
            'retries': 3,
            'fragment_retries': 3,
            'skip_unavailable_fragments': True,
            'keep_fragments': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'cachedir': temp_dir,
        }

        if format_option == "audio":
            opts['format'] = 'bestaudio/best'
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320' if is_premium else '128',
            }]
        elif format_option == "video_hd":
            opts['format'] = 'bestvideo[ext=mp4][height>=720]+bestaudio[ext=m4a]/bestvideo[height>=720]+bestaudio/best[height>=720]/best'
            opts['merge_output_format'] = 'mp4'
            opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
            opts['postprocessor_args'] = ['-c:v', 'copy', '-c:a', 'aac']
        else:  # video_sd
            opts['format'] = 'bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best'
            opts['merge_output_format'] = 'mp4'
            opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
            opts['postprocessor_args'] = ['-c:v', 'copy', '-c:a', 'aac']

        return opts, temp_dir
        
        return opts, temp_dir

    def download_video(self, url, output_path, format_option, is_premium,
                       progress_callback=None, completion_callback=None,
                       ydl_instance=None, pause_event=None, cancel_event=None):
        """
        Télécharge une vidéo depuis une URL dans un thread séparé pour ne pas bloquer l'UI.

        Args:
            url (str): L'URL de la vidéo à télécharger.
            output_path (str): Le chemin du dossier où sauvegarder la vidéo.
            format_option (str): Le format choisi ('audio', 'video_hd', 'video_sd').
            is_premium (bool): Si l'utilisateur a une licence premium.
            progress_callback (function, optional): Callback pour suivre la progression du téléchargement.
            completion_callback (function, optional): Callback appelé à la fin du téléchargement.
            ydl_instance (yt_dlp.YoutubeDL, optional): Instance pour permettre l'annulation.
        """
        # Vérifier que l'URL n'est pas vide
        if not url or not url.strip():
            if completion_callback:
                completion_callback(False, "L'URL est vide", None)
            return

        # Valider l'URL
        url = url.strip()
        if not self._is_valid_url(url):
            if completion_callback:
                completion_callback(False, "URL invalide ou non supportée", None)
            return

        # Vérifier que le dossier de sortie existe
        if not os.path.exists(output_path):
            try:
                os.makedirs(output_path, exist_ok=True)
            except Exception as e:
                if completion_callback:
                    completion_callback(False, f"Impossible de créer le dossier de sortie: {str(e)}", None)
                return

        # Lancer le téléchargement dans un thread séparé pour ne pas bloquer l'interface
        def download_thread():
            video_title = "Vidéo inconnue"
            file_path = None
            temp_dir = None
            try:
                ydl_opts, temp_dir = self._get_ydl_opts(
                    output_path, format_option, is_premium,
                    progress_callback, pause_event
                )

                log_download_start(url, format_option)

                # Extraire les infos sans télécharger
                with yt_dlp.YoutubeDL({**ydl_opts, 'skip_download': True, 'quiet': True}) as ydl:
                    try:
                        info_dict = ydl.extract_info(url, download=False)
                        if info_dict:
                            video_title = info_dict.get('title', 'Vidéo')
                            video_title = self._sanitize_filename(video_title)
                            file_path = ydl.prepare_filename(info_dict)
                    except Exception as e:
                        log_download_error(url, f"Erreur extraction info: {str(e)}")
                        if completion_callback:
                            completion_callback(False, f"Impossible d'extraire les informations: {str(e)}", None)
                        return

                # Vérifier annulation avant de démarrer
                if cancel_event and cancel_event.is_set():
                    if completion_callback:
                        completion_callback(False, "Téléchargement annulé", None)
                    return

                # Télécharger
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)

                    # Vérifier annulation après téléchargement
                    if cancel_event and cancel_event.is_set():
                        if completion_callback:
                            completion_callback(False, "Téléchargement annulé", None)
                        return

                    if info:
                        actual_title = info.get('title', video_title)
                        duration = info.get('duration')

                        # Corriger le chemin final — on force toujours .mp4 pour les vidéos
                        if file_path and format_option != "audio":
                            base = os.path.splitext(file_path)[0]
                            mp4_path = base + ".mp4"
                            if os.path.exists(mp4_path):
                                file_path = mp4_path

                        log_download_success(url, actual_title, file_path, duration)
                        if completion_callback:
                            completion_callback(True, actual_title, file_path)
                    else:
                        log_download_error(url, "Aucune information retournée")
                        if completion_callback:
                            completion_callback(False, "Échec du téléchargement", None)
                            
            except Exception as e:
                error_msg = str(e)
                log_download_error(url, error_msg)
                if completion_callback:
                    completion_callback(False, f"{video_title}: {error_msg}", None)
            finally:
                # Nettoyer le dossier temporaire
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                    except:
                        pass

        Thread(target=download_thread, daemon=True).start()

    def _is_valid_url(self, url):
        """Valide une URL de vidéo"""
        import re
        import urllib.parse
        # Vérification basique de la structure de l'URL
        try:
            result = urllib.parse.urlparse(url)
            if not all([result.scheme in ('http', 'https'), result.netloc]):
                return False
        except Exception:
            return False

        # Patterns pour les plateformes supportées
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
            r'(?:https?://)?(?:www\.)?youtu\.be/[\w-]+',
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+',
            r'(?:https?://)?(?:www\.)?vimeo\.com/\d+',
            r'(?:https?://)?(?:www\.)?dailymotion\.com/video/[\w-]+',
            r'(?:https?://)?(?:www\.)?twitch\.tv/',
            r'(?:https?://)?(?:www\.)?facebook\.com/',
            r'(?:https?://)?(?:www\.)?fb\.watch/',
            r'(?:https?://)?(?:www\.)?instagram\.com/',
            r'(?:https?://)?(?:www\.)?twitter\.com/',
            r'(?:https?://)?(?:www\.)?x\.com/',
            r'(?:https?://)?(?:www\.)?tiktok\.com/',
        ]

        return any(re.match(pattern, url, re.IGNORECASE) for pattern in patterns)

    def _sanitize_filename(self, filename):
        """Nettoie un nom de fichier pour éviter les caractères problématiques"""
        import re
        # Remplacer les caractères interdits
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limiter la longueur
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip()

    def get_video_info(self, url):
        """
        Récupère les informations sur la vidéo sans la télécharger.

        Args:
            url (str): L'URL de la vidéo.

        Returns:
            dict: Un dictionnaire contenant les informations de la vidéo ou une erreur.
        """
        with yt_dlp.YoutubeDL({'noplaylist': True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Inconnu'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Inconnu'),
                    'thumbnail': info.get('thumbnail', None),
                }
            except Exception as e:
                return {'error': str(e)}