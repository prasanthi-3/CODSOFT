
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import random
import string
import math
import json
import os
import threading
import time
from datetime import datetime

# ── Theme ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK       = "#0A0A1F"
BG_MID        = "#12122E"
BG_CARD       = "#1A1A3E"
BG_CARD2      = "#1E1E45"
GLASS         = "#22224A"
GLASS_BORDER  = "#3A3A6A"
ACCENT_BLUE   = "#4A9EFF"
ACCENT_PURPLE = "#9B6DFF"
ACCENT_TEAL   = "#00D4AA"
TEXT_PRIMARY  = "#E8E8FF"
TEXT_SECONDARY= "#8888BB"
TEXT_DIM      = "#555588"
GLOW_BLUE     = "#2060CC"
BTN_GENERATE  = "#3A7FE8"
BTN_GEN_HOVER = "#5595FF"
BTN_COPY      = "#2A9E7A"
BTN_COPY_HOVER= "#3DC99A"
STRENGTH_COLORS= ["#FF3355", "#FF6B35", "#FFB830", "#AADD22", "#22DD88"]

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "password_settings.json")

# ── Helpers ───────────────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "length": 16,
    "uppercase": True,
    "lowercase": True,
    "numbers": True,
    "special": True,
    "exclude_ambiguous": False,
    "count": 1,
}

def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
    except Exception:
        return dict(DEFAULT_SETTINGS)

def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

def build_charset(uppercase, lowercase, numbers, special, exclude_ambiguous):
    charset = ""
    ambiguous = "O0Il1|`'\""
    if lowercase:
        charset += string.ascii_lowercase
    if uppercase:
        charset += string.ascii_uppercase
    if numbers:
        charset += string.digits
    if special:
        charset += string.punctuation
    if exclude_ambiguous:
        charset = "".join(c for c in charset if c not in ambiguous)
    return charset

def generate_password(length, charset):
    if not charset:
        return ""
    return "".join(random.SystemRandom().choice(charset) for _ in range(length))

def calculate_entropy(length, charset_size):
    if charset_size <= 1 or length == 0:
        return 0.0
    return length * math.log2(charset_size)

def strength_level(entropy):
    """0=Very Weak, 1=Weak, 2=Fair, 3=Strong, 4=Very Strong"""
    if entropy < 28:   return 0
    if entropy < 40:   return 1
    if entropy < 60:   return 2
    if entropy < 80:   return 3
    return 4

STRENGTH_LABELS = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
class PasswordGeneratorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.history: list[str] = []
        self._anim_running = False

        self._setup_window()
        self._build_ui()
        self._load_settings_to_ui()
        self._generate()  # show a password on startup

    # ── Window ────────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.title("🔐 PASS GENERATOR")
        self.geometry("820x900")
        self.minsize(760, 800)
        self.configure(fg_color=BG_DARK)
        self.resizable(True, True)

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        # Scrollable master frame
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG_DARK, scrollbar_button_color=GLASS,
                                             scrollbar_button_hover_color=GLASS_BORDER)
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

        self._build_header()
        self._build_password_display()
        self._build_length_slider()
        self._build_checkboxes()
        self._build_buttons()
        self._build_strength_meter()
        self._build_multi_section()
        self._build_history_section()
        self._build_statusbar()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        hdr = ctk.CTkFrame(self.scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(20, 0), padx=24)

        ctk.CTkLabel(hdr, text="🔐 ", font=ctk.CTkFont("Segoe UI", 28, "bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")

        ctk.CTkLabel(hdr, text="PASSWORD GENERATOR",
                     font=ctk.CTkFont("Segoe UI", 13), text_color=TEXT_SECONDARY).pack(side="left", padx=(8, 0), pady=(8, 0))

        ver = ctk.CTkLabel(hdr, text="v2.0", font=ctk.CTkFont("Segoe UI", 11),
                           text_color=TEXT_DIM)
        ver.pack(side="right")

        sep = ctk.CTkFrame(self.scroll, height=1, fg_color=GLASS_BORDER)
        sep.pack(fill="x", padx=24, pady=(10, 0))

    # ── Password Display ──────────────────────────────────────────────────────
    def _build_password_display(self):
        card = ctk.CTkFrame(self.scroll, fg_color=GLASS, corner_radius=18,
                            border_width=1, border_color=GLASS_BORDER)
        card.pack(fill="x", padx=24, pady=(18, 0))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        lbl_top = ctk.CTkLabel(inner, text="GENERATED PASSWORD",
                               font=ctk.CTkFont("Segoe UI", 10, "bold"),
                               text_color=TEXT_DIM)
        lbl_top.pack(anchor="w")

        self.pw_var = tk.StringVar(value="")
        self.pw_display = ctk.CTkEntry(
            inner, textvariable=self.pw_var,
            font=ctk.CTkFont("Consolas", 30, "bold"),
            text_color=ACCENT_BLUE,
            fg_color="#0D0D2A",
            border_color=GLOW_BLUE,
            border_width=2,
            corner_radius=12,
            height=70,
            justify="center",
            state="readonly",
        )
        self.pw_display.pack(fill="x", pady=(8, 0))

        self.entropy_label = ctk.CTkLabel(inner, text="Entropy: — bits",
                                          font=ctk.CTkFont("Segoe UI", 12),
                                          text_color=TEXT_SECONDARY)
        self.entropy_label.pack(anchor="e", pady=(6, 0))

    # ── Length Slider ─────────────────────────────────────────────────────────
    def _build_length_slider(self):
        card = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=14,
                            border_width=1, border_color=GLASS_BORDER)
        card.pack(fill="x", padx=24, pady=(12, 0))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(row, text="Password Length",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")

        self.len_label = ctk.CTkLabel(row, text=f"{self.settings['length']} chars",
                                      font=ctk.CTkFont("Consolas", 13, "bold"),
                                      text_color=ACCENT_BLUE)
        self.len_label.pack(side="right")

        self.len_slider = ctk.CTkSlider(
            card, from_=4, to=64, number_of_steps=60,
            command=self._on_length_change,
            button_color=ACCENT_BLUE,
            button_hover_color=BTN_GEN_HOVER,
            progress_color=GLOW_BLUE,
            fg_color="#0D0D2A",
            width=600,
        )
        self.len_slider.pack(fill="x", padx=16, pady=(0, 14))
        self.len_slider.set(self.settings["length"])

        # tick marks
        ticks = ctk.CTkFrame(card, fg_color="transparent")
        ticks.pack(fill="x", padx=16, pady=(0, 10))
        for val in [4, 8, 12, 16, 24, 32, 48, 64]:
            ctk.CTkLabel(ticks, text=str(val),
                         font=ctk.CTkFont("Segoe UI", 9),
                         text_color=TEXT_DIM, width=30).pack(side="left", expand=True)

    # ── Checkboxes ────────────────────────────────────────────────────────────
    def _build_checkboxes(self):
        card = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=14,
                            border_width=1, border_color=GLASS_BORDER)
        card.pack(fill="x", padx=24, pady=(12, 0))

        ctk.CTkLabel(card, text="Character Options",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(12, 6))

        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(0, 4))
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(0, 12))

        chk_style = dict(
            font=ctk.CTkFont("Segoe UI", 13),
            text_color=TEXT_PRIMARY,
            fg_color=ACCENT_BLUE,
            hover_color=BTN_GEN_HOVER,
            border_color=GLASS_BORDER,
            corner_radius=6,
            command=self._on_option_change,
        )

        self.cb_upper = ctk.CTkCheckBox(row1, text="Uppercase  A–Z", **chk_style)
        self.cb_lower = ctk.CTkCheckBox(row1, text="Lowercase  a–z", **chk_style)
        self.cb_nums  = ctk.CTkCheckBox(row2, text="Numbers  0–9",   **chk_style)
        self.cb_spec  = ctk.CTkCheckBox(row2, text="Special  !@#$…", **chk_style)
        self.cb_amb   = ctk.CTkCheckBox(row2, text="Exclude Ambiguous  (0O Il1)", **chk_style)

        for w in [self.cb_upper, self.cb_lower]:
            w.pack(side="left", padx=(0, 24))
        for w in [self.cb_nums, self.cb_spec, self.cb_amb]:
            w.pack(side="left", padx=(0, 24))

    # ── Action Buttons ────────────────────────────────────────────────────────
    def _build_buttons(self):
        row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        row.pack(fill="x", padx=24, pady=(14, 0))

        self.btn_gen = ctk.CTkButton(
            row, text="⚡  Generate Password",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=BTN_GENERATE, hover_color=BTN_GEN_HOVER,
            height=48, corner_radius=14,
            command=self._animate_generate,
        )
        self.btn_gen.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_copy = ctk.CTkButton(
            row, text="📋  Copy",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            fg_color=BTN_COPY, hover_color=BTN_COPY_HOVER,
            height=48, corner_radius=14, width=130,
            command=self._copy_password,
        )
        self.btn_copy.pack(side="right")

    # ── Strength Meter ────────────────────────────────────────────────────────
    def _build_strength_meter(self):
        card = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=14,
                            border_width=1, border_color=GLASS_BORDER)
        card.pack(fill="x", padx=24, pady=(14, 0))

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 4))

        ctk.CTkLabel(header, text="Strength",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")

        self.strength_label = ctk.CTkLabel(header, text="—",
                                            font=ctk.CTkFont("Segoe UI", 13, "bold"),
                                            text_color=TEXT_SECONDARY)
        self.strength_label.pack(side="right")

        # Canvas bar
        self.strength_canvas = tk.Canvas(card, height=18, bg=BG_CARD,
                                         highlightthickness=0)
        self.strength_canvas.pack(fill="x", padx=16, pady=(0, 14))
        self.strength_canvas.bind("<Configure>", self._redraw_strength)

        self._strength_level = 0
        self._strength_frac  = 0.0

    def _redraw_strength(self, event=None):
        c = self.strength_canvas
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        r = h // 2
        # background track
        c.create_rounded_rect = lambda *a, **kw: None  # placeholder
        # Draw bg pill
        self._draw_pill(c, 0, 0, w, h, r, "#1A1A3A")
        # Filled portion
        filled = int(w * self._strength_frac)
        if filled > 0:
            color = STRENGTH_COLORS[self._strength_level]
            self._draw_pill(c, 0, 0, max(filled, h), h, r, color)

    def _draw_pill(self, c, x1, y1, x2, y2, r, color):
        """Draw a pill/rounded rect on a tk Canvas."""
        c.create_arc(x1, y1, x1+2*r, y2, start=90, extent=180, fill=color, outline=color)
        c.create_arc(x2-2*r, y1, x2, y2, start=270, extent=180, fill=color, outline=color)
        c.create_rectangle(x1+r, y1, x2-r, y2, fill=color, outline=color)

    def _update_strength(self, entropy):
        lvl = strength_level(entropy)
        frac = min(1.0, entropy / 100.0)
        self._strength_level = lvl
        self._strength_frac  = frac
        color = STRENGTH_COLORS[lvl]
        self.strength_label.configure(text=STRENGTH_LABELS[lvl], text_color=color)
        self._redraw_strength()

    # ── Multiple Passwords ────────────────────────────────────────────────────
    def _build_multi_section(self):
        card = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=14,
                            border_width=1, border_color=GLASS_BORDER)
        card.pack(fill="x", padx=24, pady=(14, 0))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(hdr, text="Generate Multiple",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")

        self.count_var = tk.IntVar(value=self.settings.get("count", 1))
        for label, val in [("1", 1), ("5", 5), ("10", 10)]:
            rb = ctk.CTkRadioButton(
                hdr, text=label, variable=self.count_var, value=val,
                font=ctk.CTkFont("Segoe UI", 13),
                text_color=TEXT_PRIMARY,
                fg_color=ACCENT_BLUE, hover_color=BTN_GEN_HOVER,
                border_color=GLASS_BORDER,
                command=self._on_count_change,
            )
            rb.pack(side="left", padx=12)

        self.multi_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.multi_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.multi_btn = ctk.CTkButton(
            card, text="Generate Set",
            font=ctk.CTkFont("Segoe UI", 13),
            fg_color=GLASS, hover_color=GLASS_BORDER,
            height=38, corner_radius=10,
            command=self._generate_multi,
        )
        self.multi_btn.pack(padx=16, pady=(0, 12), anchor="w")

    def _generate_multi(self):
        for w in self.multi_frame.winfo_children():
            w.destroy()

        charset = self._get_charset()
        if not charset:
            self._set_status("⚠  Select at least one character type!", "warning")
            return

        length  = int(self.len_slider.get())
        count   = self.count_var.get()

        cols = 2 if count > 1 else 1
        for i in range(count):
            pw = generate_password(length, charset)
            col = i % cols
            row = i // cols
            cell = ctk.CTkFrame(self.multi_frame, fg_color=GLASS,
                                 corner_radius=10, border_width=1,
                                 border_color=GLASS_BORDER)
            cell.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
            self.multi_frame.columnconfigure(col, weight=1)

            ctk.CTkLabel(cell, text=pw, font=ctk.CTkFont("Consolas", 12, "bold"),
                         text_color=ACCENT_TEAL, wraplength=320).pack(side="left", padx=8, pady=6)

            def _copy(p=pw):
                self.clipboard_clear()
                self.clipboard_append(p)
                self._set_status(f"✅  Copied: {p[:20]}…" if len(p) > 20 else f"✅  Copied!", "success")

            ctk.CTkButton(cell, text="Copy", width=50, height=26,
                          font=ctk.CTkFont("Segoe UI", 10),
                          fg_color=BTN_COPY, hover_color=BTN_COPY_HOVER,
                          corner_radius=8, command=_copy).pack(side="right", padx=6, pady=6)

    # ── History ───────────────────────────────────────────────────────────────
    def _build_history_section(self):
        card = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=14,
                            border_width=1, border_color=GLASS_BORDER)
        card.pack(fill="x", padx=24, pady=(14, 0))

        ctk.CTkLabel(card, text="Recent History  (click to reuse)",
                     font=ctk.CTkFont("Segoe UI", 13, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor="w", padx=16, pady=(12, 6))

        self.history_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.history_frame.pack(fill="x", padx=16, pady=(0, 12))
        self._refresh_history()

    def _refresh_history(self):
        for w in self.history_frame.winfo_children():
            w.destroy()

        if not self.history:
            ctk.CTkLabel(self.history_frame, text="No history yet.",
                         font=ctk.CTkFont("Segoe UI", 12), text_color=TEXT_DIM).pack(anchor="w")
            return

        for pw in reversed(self.history[-5:]):
            row = ctk.CTkFrame(self.history_frame, fg_color=GLASS,
                                corner_radius=8, border_width=1, border_color=GLASS_BORDER)
            row.pack(fill="x", pady=2)

            def _reuse(p=pw):
                self.pw_var.set(p)
                charset = self._get_charset()
                ent = calculate_entropy(len(p), max(1, len(charset)))
                self.entropy_label.configure(text=f"Entropy: {ent:.1f} bits")
                self._update_strength(ent)
                self._set_status(f"✅  Reusing password from history.", "success")

            ctk.CTkButton(row, text=pw,
                          font=ctk.CTkFont("Consolas", 11),
                          text_color=TEXT_SECONDARY,
                          fg_color="transparent", hover_color=GLASS_BORDER,
                          anchor="w", height=30, corner_radius=8,
                          command=_reuse).pack(side="left", fill="x", expand=True, padx=4)

            def _del(p=pw):
                if p in self.history:
                    self.history.remove(p)
                self._refresh_history()

            ctk.CTkButton(row, text="✕", width=28, height=28,
                          font=ctk.CTkFont("Segoe UI", 11),
                          text_color=TEXT_DIM,
                          fg_color="transparent", hover_color="#550000",
                          corner_radius=6, command=_del).pack(side="right", padx=4, pady=2)

    # ── Status Bar ────────────────────────────────────────────────────────────
    def _build_statusbar(self):
        self.status_bar = ctk.CTkFrame(self.scroll, fg_color=BG_MID,
                                        corner_radius=10, height=36)
        self.status_bar.pack(fill="x", padx=24, pady=(14, 20))
        self.status_bar.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready — generate your first password!")
        self.status_lbl = ctk.CTkLabel(self.status_bar, textvariable=self.status_var,
                                        font=ctk.CTkFont("Segoe UI", 12),
                                        text_color=TEXT_SECONDARY)
        self.status_lbl.pack(side="left", padx=14, pady=6)

        self.clock_lbl = ctk.CTkLabel(self.status_bar, text="",
                                       font=ctk.CTkFont("Segoe UI", 11),
                                       text_color=TEXT_DIM)
        self.clock_lbl.pack(side="right", padx=14)
        self._tick_clock()

    def _tick_clock(self):
        now = datetime.now().strftime("%H:%M:%S")
        self.clock_lbl.configure(text=now)
        self.after(1000, self._tick_clock)

    def _set_status(self, msg, kind="info"):
        color_map = {"info": TEXT_SECONDARY, "success": ACCENT_TEAL,
                     "warning": "#FFB830", "error": "#FF3355"}
        self.status_var.set(msg)
        self.status_lbl.configure(text_color=color_map.get(kind, TEXT_SECONDARY))

    # ══════════════════════════════════════════════════════════════════════════
    #  LOGIC
    # ══════════════════════════════════════════════════════════════════════════
    def _load_settings_to_ui(self):
        s = self.settings
        self.len_slider.set(s["length"])
        self._on_length_change(s["length"])
        (self.cb_upper.select if s["uppercase"]          else self.cb_upper.deselect)()
        (self.cb_lower.select if s["lowercase"]          else self.cb_lower.deselect)()
        (self.cb_nums.select  if s["numbers"]            else self.cb_nums.deselect)()
        (self.cb_spec.select  if s["special"]            else self.cb_spec.deselect)()
        (self.cb_amb.select   if s["exclude_ambiguous"]  else self.cb_amb.deselect)()
        self.count_var.set(s.get("count", 1))

    def _get_settings(self) -> dict:
        return {
            "length":           int(self.len_slider.get()),
            "uppercase":        bool(self.cb_upper.get()),
            "lowercase":        bool(self.cb_lower.get()),
            "numbers":          bool(self.cb_nums.get()),
            "special":          bool(self.cb_spec.get()),
            "exclude_ambiguous":bool(self.cb_amb.get()),
            "count":            self.count_var.get(),
        }

    def _get_charset(self) -> str:
        s = self._get_settings()
        return build_charset(s["uppercase"], s["lowercase"],
                             s["numbers"], s["special"], s["exclude_ambiguous"])

    def _on_length_change(self, val):
        self.len_label.configure(text=f"{int(float(val))} chars")
        self._auto_save()

    def _on_option_change(self):
        self._auto_save()

    def _on_count_change(self):
        self._auto_save()

    def _auto_save(self):
        self.settings = self._get_settings()
        save_settings(self.settings)

    def _generate(self):
        charset = self._get_charset()
        if not charset:
            self._set_status("⚠  Select at least one character type!", "warning")
            self.pw_var.set("(no charset selected)")
            return

        length = int(self.len_slider.get())
        pw = generate_password(length, charset)
        self.pw_var.set(pw)

        ent = calculate_entropy(length, len(charset))
        self.entropy_label.configure(text=f"Entropy: {ent:.1f} bits")
        self._update_strength(ent)
        self._pw_display_glow()

        # history
        if pw not in self.history:
            self.history.append(pw)
        if len(self.history) > 5:
            self.history.pop(0)
        self._refresh_history()

        self._auto_save()
        self._set_status(f"✅  {length}-char password generated  ·  {ent:.0f} bits entropy", "success")

    def _animate_generate(self):
        """Flash the button, then generate."""
        if self._anim_running:
            return
        self._anim_running = True

        frames = ["⚡ Generating…", "⚡ Mixing…", "⚡ Securing…"]

        def _run():
            for f in frames:
                self.btn_gen.configure(text=f, fg_color=ACCENT_PURPLE)
                time.sleep(0.12)
            self.btn_gen.configure(text="⚡  Generate Password", fg_color=BTN_GENERATE)
            self._anim_running = False
            self.after(0, self._generate)

        threading.Thread(target=_run, daemon=True).start()

    def _pw_display_glow(self):
        """Briefly flash the password entry border."""
        self.pw_display.configure(border_color=ACCENT_TEAL)
        self.after(300, lambda: self.pw_display.configure(border_color=GLOW_BLUE))

    def _copy_password(self):
        pw = self.pw_var.get()
        if not pw or pw.startswith("("):
            self._set_status("⚠  Nothing to copy.", "warning")
            return
        self.clipboard_clear()
        self.clipboard_append(pw)
        self.btn_copy.configure(text="✅  Copied!", fg_color="#1A7A55")
        self.after(1500, lambda: self.btn_copy.configure(text="📋  Copy", fg_color=BTN_COPY))
        self._set_status(f"📋  Copied to clipboard!", "success")


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        app = PasswordGeneratorApp()
        app.mainloop()
    except ImportError as e:
        print(f"\n❌  Missing dependency: {e}")
        print("\n▶  Install with:\n    pip install customtkinter\n")
