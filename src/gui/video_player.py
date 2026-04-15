"""
TelVid Player — Lecteur vidéo intégré basé sur python-vlc
Lecteur complet et professionnel, indépendant de VLC pour l'utilisateur final.
"""
import os
import sys
import time
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox


def _setup_vlc_path():
    """Configure le chemin VLC selon l'environnement (dev ou build)."""
    if getattr(sys, 'frozen', False):
        # Mode PyInstaller — VLC est dans le dossier de l'exe
        vlc_dir = os.path.join(sys._MEIPASS, 'vlc')
        if os.path.exists(vlc_dir):
            os.add_dll_directory(vlc_dir)
            os.environ['PYTHON_VLC_MODULE_PATH'] = vlc_dir
            os.environ['PYTHON_VLC_LIB_PATH'] = os.path.join(vlc_dir, 'libvlc.dll')
    else:
        # Mode développement
        vlc_dir = r'C:\Program Files\VideoLAN\VLC'
        if os.path.exists(vlc_dir):
            os.add_dll_directory(vlc_dir)


_setup_vlc_path()

try:
    import vlc
    VLC_AVAILABLE = True
except Exception:
    VLC_AVAILABLE = False


class VideoPlayer(ctk.CTkToplevel):
    """Lecteur vidéo TelVid — basé sur libVLC."""

    SEEK_STEP = 10  # secondes

    def __init__(self, parent, video_path: str):
        super().__init__(parent)

        if not VLC_AVAILABLE:
            messagebox.showerror(
                "Lecteur indisponible",
                "Le moteur vidéo n'a pas pu être chargé.\n"
                "Vérifiez que VLC 64-bit est installé."
            )
            self.destroy()
            return

        self.video_path = video_path
        self._duration = 0
        self._is_fullscreen = False
        self._volume = 70
        self._muted = False
        self._seeking = False
        self._update_job = None

        # Instance VLC
        self._instance = vlc.Instance('--no-xlib', '--quiet')
        self._player = self._instance.media_player_new()

        title = os.path.basename(video_path)
        self.title(f"TelVid Player — {title}")
        self.geometry("960x580")
        self.minsize(640, 400)
        self.configure(fg_color="#0a0a0a")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._load(video_path)

        # Animation fondu d'entrée
        try:
            from src.gui.animations import fade_in
            fade_in(self, duration=300)
        except Exception:
            pass

        # Charger les icônes — symboles Unicode fiables sur tous les systèmes
        self._ico_play    = "▶"
        self._ico_pause   = "⏸"
        self._ico_stop    = "⏹"
        self._ico_restart = "⏮"
        self._ico_rewind  = "⏪"
        self._ico_forward = "⏩"
        self._ico_vol     = "🔊"
        self._ico_mute    = "🔇"
        self._ico_fs      = "⛶"
        self._ico_exit_fs = "⊡"
        self._apply_icons()

        # Raccourcis
        self.bind("<space>",  lambda e: self._toggle_play())
        self.bind("<Left>",   lambda e: self._seek_rel(-self.SEEK_STEP))
        self.bind("<Right>",  lambda e: self._seek_rel(self.SEEK_STEP))
        self.bind("<Up>",     lambda e: self._change_vol(10))
        self.bind("<Down>",   lambda e: self._change_vol(-10))
        self.bind("<f>",      lambda e: self._toggle_fs())
        self.bind("<Escape>", lambda e: self._exit_fs())
        self.focus_set()
    # ── Construction UI ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Canvas vidéo — VLC dessine directement dedans
        self._video_frame = tk.Frame(self, bg="#000000")
        self._video_frame.pack(fill="both", expand=True)

        # Barre de contrôle
        self._ctrl = ctk.CTkFrame(self, fg_color="#111111", height=88)
        self._ctrl.pack(fill="x", side="bottom")
        self._ctrl.pack_propagate(False)

        # Ligne progression
        prog_row = ctk.CTkFrame(self._ctrl, fg_color="transparent")
        prog_row.pack(fill="x", padx=12, pady=(8, 2))

        self._progress = ctk.CTkSlider(
            prog_row, from_=0, to=1000, height=14,
            progress_color="#3b82f6",
            button_color="#60a5fa",
            button_hover_color="#93c5fd",
            command=self._on_seek_drag
        )
        self._progress.set(0)
        self._progress.pack(fill="x", expand=True, side="left")
        self._progress.bind("<ButtonPress-1>",   lambda e: setattr(self, '_seeking', True))
        self._progress.bind("<ButtonRelease-1>", self._on_seek_release)

        self._time_lbl = ctk.CTkLabel(
            prog_row, text="0:00 / 0:00",
            font=("Segoe UI", 11), text_color="#94a3b8", width=110
        )
        self._time_lbl.pack(side="right", padx=6)

        # Ligne boutons
        btn_row = ctk.CTkFrame(self._ctrl, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(2, 8))

        s = dict(width=40, height=36, fg_color="transparent",
                 hover_color="#1e293b", corner_radius=8,
                 font=("Segoe UI Symbol", 17))

        left = ctk.CTkFrame(btn_row, fg_color="transparent")
        left.pack(side="left")

        self._btn_restart  = ctk.CTkButton(left, text="⏮", command=self._restart,              **s)
        self._btn_restart.pack(side="left", padx=2)
        self._btn_rewind   = ctk.CTkButton(left, text="⏪", command=lambda: self._seek_rel(-10), **s)
        self._btn_rewind.pack(side="left", padx=2)

        self._btn_play = ctk.CTkButton(
            left, text="▶", command=self._toggle_play,
            width=50, height=36, fg_color="#3b82f6",
            hover_color="#2563eb", corner_radius=10,
            font=("Segoe UI Symbol", 20)
        )
        self._btn_play.pack(side="left", padx=4)

        self._btn_forward  = ctk.CTkButton(left, text="⏩", command=lambda: self._seek_rel(10), **s)
        self._btn_forward.pack(side="left", padx=2)
        self._btn_stop     = ctk.CTkButton(left, text="⏹", command=self._stop,                  **s)
        self._btn_stop.pack(side="left", padx=2)

        right = ctk.CTkFrame(btn_row, fg_color="transparent")
        right.pack(side="right")

        self._btn_mute = ctk.CTkButton(right, text="🔊", command=self._toggle_mute, **s)
        self._btn_mute.pack(side="left", padx=2)

        self._vol_slider = ctk.CTkSlider(
            right, from_=0, to=100, width=90, height=14,
            progress_color="#3b82f6", button_color="#60a5fa",
            command=self._on_vol_change
        )
        self._vol_slider.set(self._volume)
        self._vol_slider.pack(side="left", padx=6)

        self._btn_fs = ctk.CTkButton(right, text="⛶", command=self._toggle_fs, **s)
        self._btn_fs.pack(side="left", padx=2)

    def _apply_icons(self):
        """Applique les symboles sur tous les boutons du lecteur."""
        self._btn_restart.configure( text=self._ico_restart, image=None)
        self._btn_rewind.configure(  text=self._ico_rewind,  image=None)
        self._btn_play.configure(    text=self._ico_play,    image=None)
        self._btn_forward.configure( text=self._ico_forward, image=None)
        self._btn_stop.configure(    text=self._ico_stop,    image=None)
        self._btn_mute.configure(    text=self._ico_vol,     image=None)
        self._btn_fs.configure(      text=self._ico_fs,      image=None)

    # ── Chargement ────────────────────────────────────────────────────────────

    def _load(self, path: str):
        """Charge un fichier vidéo dans VLC."""
        media = self._instance.media_new(path)
        self._player.set_media(media)

        # Attacher VLC au canvas tkinter
        self.update_idletasks()
        hwnd = self._video_frame.winfo_id()
        if sys.platform == "win32":
            self._player.set_hwnd(hwnd)

        self._player.audio_set_volume(self._volume)
        self._player.play()
        self._btn_play.configure(text="⏸")

        # Attendre que VLC démarre pour récupérer la durée
        self.after(800, self._get_duration)
        self._start_ui_update()

    def _get_duration(self):
        dur = self._player.get_length()
        if dur > 0:
            self._duration = dur
        else:
            self.after(500, self._get_duration)

    # ── Contrôles ─────────────────────────────────────────────────────────────

    def _toggle_play(self):
        state = self._player.get_state()
        if state == vlc.State.Playing:
            self._player.pause()
            self._btn_play.configure(text=self._ico_play)
        elif state in (vlc.State.Paused, vlc.State.Stopped, vlc.State.Ended):
            self._player.play()
            self._btn_play.configure(text=self._ico_pause)

    def _stop(self):
        self._player.stop()
        self._btn_play.configure(text=self._ico_play)
        self._progress.set(0)
        self._time_lbl.configure(text="0:00 / 0:00")

    def _restart(self):
        self._player.set_time(0)
        self._player.play()
        self._btn_play.configure(text=self._ico_pause)

    def _seek_rel(self, delta_sec: int):
        current = self._player.get_time()
        new_time = max(0, current + delta_sec * 1000)
        self._player.set_time(new_time)

    def _on_seek_drag(self, val):
        """Mise à jour du label pendant le drag."""
        if self._duration > 0:
            pos_ms = (float(val) / 1000) * self._duration
            self._time_lbl.configure(
                text=f"{self._fmt(pos_ms)} / {self._fmt(self._duration)}"
            )

    def _on_seek_release(self, event):
        self._seeking = False
        if self._duration > 0:
            pos = self._progress.get() / 1000
            self._player.set_position(pos)

    # ── Volume ────────────────────────────────────────────────────────────────

    def _on_vol_change(self, val):
        self._volume = int(float(val))
        self._muted = False
        self._btn_mute.configure(text="🔊")
        self._player.audio_set_volume(self._volume)

    def _change_vol(self, delta: int):
        new_vol = max(0, min(100, self._volume + delta))
        self._vol_slider.set(new_vol)
        self._on_vol_change(new_vol)

    def _toggle_mute(self):
        self._muted = not self._muted
        self._player.audio_set_mute(self._muted)
        self._btn_mute.configure(text=self._ico_mute if self._muted else self._ico_vol)

    # ── Plein écran ───────────────────────────────────────────────────────────

    def _toggle_fs(self):
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)
        if self._is_fullscreen:
            self._ctrl.pack_forget()
            self._btn_fs.configure(text=self._ico_exit_fs)
        else:
            self._ctrl.pack(fill="x", side="bottom")
            self._btn_fs.configure(text=self._ico_fs)

    def _exit_fs(self):
        if self._is_fullscreen:
            self._toggle_fs()

    # ── Mise à jour UI ────────────────────────────────────────────────────────

    def _start_ui_update(self):
        self._update_ui()

    def _update_ui(self):
        """Met à jour la barre de progression et le temps toutes les 500ms."""
        try:
            if not self._seeking and self._player:
                pos = self._player.get_position()
                t   = self._player.get_time()
                dur = self._player.get_length()

                if dur > 0:
                    self._duration = dur
                    self._progress.set(pos * 1000)
                    self._time_lbl.configure(
                        text=f"{self._fmt(t)} / {self._fmt(dur)}"
                    )

                # Mettre à jour le bouton play selon l'état
                state = self._player.get_state()
                if state == vlc.State.Playing:
                    self._btn_play.configure(text=self._ico_pause)
                elif state in (vlc.State.Paused, vlc.State.Stopped):
                    self._btn_play.configure(text=self._ico_play)
                elif state == vlc.State.Ended:
                    self._btn_play.configure(text=self._ico_play)
                    self._progress.set(0)

            self._update_job = self.after(500, self._update_ui)
        except Exception:
            pass

    # ── Utilitaires ───────────────────────────────────────────────────────────

    def _fmt(self, ms) -> str:
        """Formate des millisecondes en m:ss ou h:mm:ss."""
        secs = max(0, int(ms / 1000))
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    # ── Fermeture ─────────────────────────────────────────────────────────────

    def _on_close(self):
        if self._update_job:
            self.after_cancel(self._update_job)
        try:
            self._player.stop()
            self._player.release()
            self._instance.release()
        except Exception:
            pass
        self.destroy()
