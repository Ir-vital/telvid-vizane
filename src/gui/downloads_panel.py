"""
Panneau des vidéos téléchargées — TelVid-Vizane
Affiche les vidéos avec miniature, titre, durée et bouton lecture.
"""
import os
import threading
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import av


def _get_thumbnail(video_path: str, size=(200, 112)) -> ctk.CTkImage | None:
    """Extrait la première frame d'une vidéo comme miniature."""
    try:
        container = av.open(video_path)
        for frame in container.decode(video=0):
            img = frame.to_image()
            img.thumbnail(size, Image.LANCZOS)
            # Créer une image avec fond noir aux bonnes dimensions
            thumb = Image.new("RGB", size, (20, 20, 20))
            x = (size[0] - img.width) // 2
            y = (size[1] - img.height) // 2
            thumb.paste(img, (x, y))
            container.close()
            return ctk.CTkImage(thumb, size=size)
        container.close()
    except Exception:
        pass
    return None


def _get_duration(video_path: str) -> str:
    """Retourne la durée formatée d'une vidéo."""
    try:
        container = av.open(video_path)
        if container.duration:
            secs = int(container.duration / av.time_base)
            m, s = divmod(secs, 60)
            h, m = divmod(m, 60)
            container.close()
            if h:
                return f"{h}:{m:02d}:{s:02d}"
            return f"{m}:{s:02d}"
        container.close()
    except Exception:
        pass
    return "--:--"


class DownloadedVideoCard(ctk.CTkFrame):
    """Carte d'une vidéo téléchargée."""

    def __init__(self, parent, video_path: str, on_play, **kwargs):
        super().__init__(parent, fg_color="#1a1a2e", corner_radius=10, **kwargs)
        self.video_path = video_path
        self.on_play = on_play
        self._build()
        # Charger miniature en arrière-plan
        threading.Thread(target=self._load_thumb, daemon=True).start()

    def _build(self):
        title = os.path.splitext(os.path.basename(self.video_path))[0]
        if len(title) > 35:
            title = title[:35] + "..."

        # Miniature placeholder
        self._thumb_label = ctk.CTkLabel(
            self, text="⏳", width=200, height=112,
            fg_color="#0f0f1a", corner_radius=8,
            font=("Segoe UI Symbol", 28)
        )
        self._thumb_label.pack(padx=8, pady=(8, 4))

        # Titre
        ctk.CTkLabel(
            self, text=title, font=("Segoe UI", 11, "bold"),
            wraplength=160, justify="center"
        ).pack(padx=8, pady=2)

        # Durée
        self._dur_label = ctk.CTkLabel(
            self, text="...", font=("Segoe UI", 10),
            text_color="#94a3b8"
        )
        self._dur_label.pack(pady=2)

        # Boutons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(4, 8), padx=8, fill="x")

        ctk.CTkButton(
            btn_frame, text="▶  Lire",
            command=lambda: self.on_play(self.video_path),
            height=32, fg_color="#3b82f6", hover_color="#2563eb",
            font=("Segoe UI", 12, "bold"), corner_radius=8
        ).pack(side="left", fill="x", expand=True, padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="📁",
            command=self._open_folder,
            height=32, width=36, fg_color="#374151",
            hover_color="#4b5563", corner_radius=8
        ).pack(side="right")

        # Hover effect
        self.bind("<Enter>", lambda e: self.configure(fg_color="#1e293b"))
        self.bind("<Leave>", lambda e: self.configure(fg_color="#1a1a2e"))

    def _load_thumb(self):
        thumb = _get_thumbnail(self.video_path)
        dur = _get_duration(self.video_path)
        self.after(0, self._update_thumb, thumb, dur)

    def _update_thumb(self, thumb, dur):
        if thumb:
            self._thumb_label.configure(image=thumb, text="")
        self._dur_label.configure(text=dur)

    def _open_folder(self):
        folder = os.path.dirname(self.video_path)
        if os.path.exists(folder):
            os.startfile(folder)


class DownloadsPanel(ctk.CTkFrame):
    """Panneau latéral affichant les vidéos téléchargées."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._cards = {}
        self._build()

    def _build(self):
        # Titre
        ctk.CTkLabel(
            self, text="Vidéos téléchargées",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(12, 4), padx=10)

        ctk.CTkLabel(
            self, text="Cliquez ▶ pour lire dans TelVid Player",
            font=("Segoe UI", 10, "italic"), text_color="#64748b"
        ).pack(pady=(0, 8), padx=10)

        # Liste scrollable
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=6, pady=4)

        self._empty_label = ctk.CTkLabel(
            self._scroll, text="Aucune vidéo téléchargée.",
            text_color="#475569", font=("Segoe UI", 11, "italic")
        )
        self._empty_label.pack(pady=30)

    def add_video(self, video_path: str, on_play_callback):
        """Ajoute une vidéo au panneau."""
        if video_path in self._cards:
            return
        if not os.path.exists(video_path):
            return

        # Cacher le label vide
        self._empty_label.pack_forget()

        card = DownloadedVideoCard(
            self._scroll, video_path, on_play_callback
        )
        card.pack(fill="x", padx=4, pady=6)
        self._cards[video_path] = card

    def remove_video(self, video_path: str):
        """Supprime une vidéo du panneau."""
        if video_path in self._cards:
            self._cards[video_path].destroy()
            del self._cards[video_path]
        if not self._cards:
            self._empty_label.pack(pady=30)
