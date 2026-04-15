"""
Système d'animations pour TelVid-Vizane.
Effets : fondu, pulse, slide, hover, barre de progression animée.
"""
import customtkinter as ctk
import tkinter as tk


# ── Fondu d'entrée ────────────────────────────────────────────────────────────

def fade_in(widget, duration=300, steps=15, start_alpha=0.0):
    """Fait apparaître une fenêtre en fondu."""
    step_time = duration // steps
    alpha_step = (1.0 - start_alpha) / steps

    def _step(current_alpha):
        if current_alpha >= 1.0:
            widget.attributes("-alpha", 1.0)
            return
        widget.attributes("-alpha", current_alpha)
        widget.after(step_time, _step, current_alpha + alpha_step)

    widget.attributes("-alpha", start_alpha)
    widget.after(10, _step, start_alpha + alpha_step)


def fade_out(widget, duration=200, steps=10, on_done=None):
    """Fait disparaître une fenêtre en fondu."""
    step_time = duration // steps
    alpha_step = 1.0 / steps

    def _step(current_alpha):
        if current_alpha <= 0.0:
            widget.attributes("-alpha", 0.0)
            if on_done:
                on_done()
            return
        widget.attributes("-alpha", current_alpha)
        widget.after(step_time, _step, current_alpha - alpha_step)

    _step(1.0 - alpha_step)


# ── Pulse (bouton qui bat) ────────────────────────────────────────────────────

def pulse_button(button: ctk.CTkButton, color1: str, color2: str,
                 interval: int = 800, repeat: int = 3):
    """Fait pulser un bouton entre deux couleurs."""
    count = [0]

    def _toggle(to_color2: bool):
        if count[0] >= repeat * 2:
            button.configure(fg_color=color1)
            return
        button.configure(fg_color=color2 if to_color2 else color1)
        count[0] += 1
        button.after(interval, _toggle, not to_color2)

    _toggle(True)


# ── Hover animé ───────────────────────────────────────────────────────────────

def animated_hover(widget: ctk.CTkButton,
                   normal_color: str, hover_color: str,
                   steps: int = 8, duration: int = 120):
    """Ajoute un effet de transition de couleur au survol."""
    # Note : CustomTkinter gère déjà hover_color nativement.
    # Cette fonction ajoute un effet de scale (agrandissement léger).
    original_height = widget.cget("height")
    original_width  = widget.cget("width")

    def on_enter(e):
        _scale(widget, original_width, original_height,
               int(original_width * 1.04), int(original_height * 1.08),
               steps=6, duration=80)

    def on_leave(e):
        _scale(widget, int(original_width * 1.04), int(original_height * 1.08),
               original_width, original_height,
               steps=6, duration=80)

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def _scale(widget, from_w, from_h, to_w, to_h, steps, duration):
    """Anime le redimensionnement d'un widget."""
    step_time = max(1, duration // steps)
    dw = (to_w - from_w) / steps
    dh = (to_h - from_h) / steps

    def _step(i, w, h):
        if i >= steps:
            widget.configure(width=to_w, height=to_h)
            return
        widget.configure(width=int(w), height=int(h))
        widget.after(step_time, _step, i + 1, w + dw, h + dh)

    _step(0, from_w, from_h)


# ── Barre de progression indéterminée ─────────────────────────────────────────

class IndeterminateProgress:
    """Barre de progression animée en mode indéterminé (chargement)."""

    def __init__(self, progress_bar: ctk.CTkProgressBar, speed: int = 20):
        self._bar = progress_bar
        self._speed = speed
        self._running = False
        self._pos = 0.0
        self._direction = 1
        self._job = None

    def start(self):
        self._running = True
        self._animate()

    def stop(self):
        self._running = False
        if self._job:
            try:
                self._bar.after_cancel(self._job)
            except Exception:
                pass
        self._bar.set(0)

    def _animate(self):
        if not self._running:
            return
        self._pos += 0.02 * self._direction
        if self._pos >= 1.0:
            self._pos = 1.0
            self._direction = -1
        elif self._pos <= 0.0:
            self._pos = 0.0
            self._direction = 1
        self._bar.set(self._pos)
        self._job = self._bar.after(self._speed, self._animate)


# ── Slide d'entrée ────────────────────────────────────────────────────────────

def slide_in_from_bottom(widget: tk.Widget, distance: int = 30,
                          steps: int = 12, duration: int = 200):
    """Fait glisser un widget depuis le bas."""
    widget.update_idletasks()
    original_y = widget.winfo_y()
    start_y = original_y + distance
    step_time = max(1, duration // steps)
    dy = distance / steps

    def _step(i, y):
        if i >= steps:
            widget.place_configure(y=original_y)
            return
        widget.place_configure(y=int(y))
        widget.after(step_time, _step, i + 1, y - dy)

    widget.place_configure(y=start_y)
    widget.after(10, _step, 0, start_y)


# ── Notification toast ────────────────────────────────────────────────────────

def show_toast(parent, message: str, duration: int = 2500,
               color: str = "#1e293b", text_color: str = "#ffffff"):
    """Affiche une notification toast en bas de la fenêtre."""
    toast = ctk.CTkLabel(
        parent,
        text=message,
        fg_color=color,
        text_color=text_color,
        corner_radius=10,
        font=("Segoe UI", 12),
        padx=16, pady=8
    )
    toast.place(relx=0.5, rely=0.95, anchor="s")
    fade_in(toast, duration=200) if hasattr(toast, 'attributes') else None

    def _remove():
        try:
            toast.place_forget()
            toast.destroy()
        except Exception:
            pass

    parent.after(duration, _remove)


# ── Typing effect pour les labels ─────────────────────────────────────────────

def typing_effect(label: ctk.CTkLabel, text: str,
                  speed: int = 40, on_done=None):
    """Affiche le texte lettre par lettre."""
    label.configure(text="")
    chars = list(text)
    idx = [0]

    def _type():
        if idx[0] >= len(chars):
            if on_done:
                on_done()
            return
        current = "".join(chars[:idx[0] + 1])
        label.configure(text=current)
        idx[0] += 1
        label.after(speed, _type)

    label.after(speed, _type)
