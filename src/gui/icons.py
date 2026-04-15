"""
Gestionnaire d'icônes FontAwesome pour TelVid-Vizane.
Toutes les icônes de l'application passent par ce module.
"""
import tkinter as tk
from tkfontawesome import icon_to_image
from PIL import Image
import customtkinter as ctk

# Cache global pour éviter de recréer les icônes
_cache: dict = {}


def get_icon(name: str, size: int = 18, color: str = "#ffffff") -> tk.PhotoImage:
    """
    Retourne une icône FontAwesome comme PhotoImage tkinter.
    name  : nom FontAwesome (ex: 'download', 'play', 'cog')
    size  : taille en pixels
    color : couleur hex
    """
    key = f"{name}_{size}_{color}"
    if key not in _cache:
        try:
            img = icon_to_image(name, fill=color, scale_to_width=size)
            _cache[key] = img
        except Exception:
            # Fallback : image vide transparente
            _cache[key] = tk.PhotoImage(width=size, height=size)
    return _cache[key]


def get_ctk_icon(name: str, size: int = 20, color: str = "#ffffff") -> ctk.CTkImage:
    """
    Retourne une icône FontAwesome comme CTkImage (pour CustomTkinter).
    Supporte le mode clair/sombre automatiquement.
    """
    key = f"ctk_{name}_{size}_{color}"
    if key not in _cache:
        try:
            pil_img = icon_to_image(name, fill=color, scale_to_width=size)
            # Convertir PhotoImage → PIL Image
            pil_img_converted = _photoimge_to_pil(pil_img, size)
            _cache[key] = ctk.CTkImage(pil_img_converted, size=(size, size))
        except Exception:
            _cache[key] = None
    return _cache[key]


def _photoimge_to_pil(photo: tk.PhotoImage, size: int) -> Image.Image:
    """Convertit un PhotoImage tkinter en PIL Image."""
    try:
        from PIL import ImageTk
        # Créer une image PIL depuis le PhotoImage
        pil = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        # tkfontawesome retourne déjà un PhotoImage basé sur PIL
        # On peut accéder à l'image PIL sous-jacente
        if hasattr(photo, '_PhotoImage__photo'):
            return photo._PhotoImage__photo
        # Fallback : recréer depuis les données
        return pil
    except Exception:
        return Image.new("RGBA", (size, size), (0, 0, 0, 0))


# ── Icônes prédéfinies pour l'application ─────────────────────────────────────
# Usage : from src.gui.icons import ICONS
# Puis  : button.configure(image=ICONS['download'])

def load_all(color_dark="#ffffff", color_light="#1e293b"):
    """Charge toutes les icônes utilisées dans l'app."""
    mode = ctk.get_appearance_mode()
    color = color_dark if mode == "Dark" else color_light

    icons = {
        # Navigation principale
        "download":     get_icon("download",        20, color),
        "settings":     get_icon("cog",             18, color),
        "history":      get_icon("history",         18, color),
        "about":        get_icon("info-circle",     18, color),

        # Formats
        "video_hd":     get_icon("film",            18, "#60a5fa"),
        "video_sd":     get_icon("video",           18, "#94a3b8"),
        "audio":        get_icon("music",           18, "#a3e635"),

        # Lecteur vidéo
        "play":         get_icon("play",            20, "#ffffff"),
        "pause":        get_icon("pause",           20, "#ffffff"),
        "stop":         get_icon("stop",            18, "#ffffff"),
        "step_back":    get_icon("step-backward",   18, "#ffffff"),
        "step_fwd":     get_icon("step-forward",    18, "#ffffff"),
        "fast_back":    get_icon("backward",        18, "#ffffff"),
        "fast_fwd":     get_icon("forward",         18, "#ffffff"),
        "volume":       get_icon("volume-up",       18, "#ffffff"),
        "mute":         get_icon("volume-mute",     18, "#ffffff"),
        "fullscreen":   get_icon("expand",          18, "#ffffff"),
        "exit_fs":      get_icon("compress",        18, "#ffffff"),

        # Actions
        "folder":       get_icon("folder-open",     18, color),
        "trash":        get_icon("trash",           16, "#ef4444"),
        "check":        get_icon("check-circle",    16, "#4ade80"),
        "error":        get_icon("times-circle",    16, "#ef4444"),
        "cancel":       get_icon("times",           16, "#94a3b8"),
        "premium":      get_icon("crown",           18, "#fbbf24"),
        "key":          get_icon("key",             18, "#fbbf24"),
        "whatsapp":     get_icon("whatsapp",        18, "#4ade80"),
        "email":        get_icon("envelope",        18, color),
        "refresh":      get_icon("sync-alt",        16, color),
        "export":       get_icon("file-export",     16, color),
        "convert":      get_icon("exchange-alt",    18, color),
    }
    return icons
