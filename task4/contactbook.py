
import customtkinter as ctk
import json
import os
import re
from tkinter import messagebox, Canvas
import tkinter as tk
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import io
import math


# ─────────────────────────────────────────────
#  Theme & Palette
# ─────────────────────────────────────────────
BG_DARK       = "#0A0A1F"
BG_MID        = "#12122E"
BG_CARD       = "#1E1E3A"
BG_CARD_HOVER = "#252548"
GLASS_STROKE  = "#3A3A6A"
GLASS_INNER   = "#2A2A4A"
ACCENT_1      = "#7B6FF0"   # violet
ACCENT_2      = "#4FC3F7"   # cyan
ACCENT_3      = "#F06292"   # pink
STAR_ON       = "#FFD54F"
STAR_OFF      = "#4A4A7A"
TEXT_PRIMARY  = "#E8E8FF"
TEXT_SECONDARY= "#9898C0"
TEXT_DIM      = "#5A5A8A"
SUCCESS       = "#69F0AE"
DANGER        = "#FF5252"

AVATAR_GRADIENTS = [
    ("#7B6FF0", "#4FC3F7"),
    ("#F06292", "#FF8A65"),
    ("#69F0AE", "#26C6DA"),
    ("#FFD54F", "#FF7043"),
    ("#CE93D8", "#7986CB"),
    ("#4DD0E1", "#26A69A"),
    ("#EF9A9A", "#F48FB1"),
    ("#80CBC4", "#4DB6AC"),
]

DATA_FILE = "contacts.json"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def load_contacts() -> list:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_contacts(contacts: list):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2, ensure_ascii=False)


def next_id(contacts: list) -> int:
    return max((c.get("id", 0) for c in contacts), default=0) + 1


def avatar_color(name: str):
    idx = sum(ord(c) for c in name) % len(AVATAR_GRADIENTS)
    return AVATAR_GRADIENTS[idx]


def make_avatar_image(letter: str, size: int, color_pair: tuple) -> ctk.CTkImage:
    """Render a circular gradient avatar with a letter."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Gradient via radial blend
    c1 = _hex_to_rgb(color_pair[0])
    c2 = _hex_to_rgb(color_pair[1])
    for y in range(size):
        for x in range(size):
            dx, dy = x - size / 2, y - size / 2
            if dx * dx + dy * dy <= (size / 2) ** 2:
                t = (x + y) / (size * 2)
                r = int(c1[0] * (1 - t) + c2[0] * t)
                g = int(c1[1] * (1 - t) + c2[1] * t)
                b = int(c1[2] * (1 - t) + c2[2] * t)
                img.putpixel((x, y), (r, g, b, 255))

    # Letter
    draw = ImageDraw.Draw(img)
    font_size = int(size * 0.44)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter.upper(), font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
              letter.upper(), font=font, fill=(255, 255, 255, 230))

    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"


# ─────────────────────────────────────────────
#  Modal Base
# ─────────────────────────────────────────────

class GlassModal(ctk.CTkToplevel):
    def __init__(self, parent, title: str, width=420, height=520):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        self.grab_set()
        self.lift()
        self.focus_force()

        # Decorative header bar
        ctk.CTkFrame(self, height=4, fg_color=(ACCENT_1, ACCENT_2),
                     corner_radius=0).pack(fill="x", side="top")

        self.title_label = ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont("Helvetica", 20, "bold"),
            text_color=TEXT_PRIMARY
        )
        self.title_label.pack(pady=(18, 0))

        self.body = ctk.CTkFrame(self, fg_color=GLASS_INNER,
                                 corner_radius=16, border_width=1,
                                 border_color=GLASS_STROKE)
        self.body.pack(fill="both", expand=True, padx=20, pady=16)


# ─────────────────────────────────────────────
#  Add / Edit Form
# ─────────────────────────────────────────────

class ContactFormModal(GlassModal):
    def __init__(self, parent, on_save, contact=None):
        mode = "Edit Contact" if contact else "New Contact"
        super().__init__(parent, mode, width=440, height=500)
        self.on_save = on_save
        self.contact = contact

        pad = {"padx": 24, "pady": 6}
        fields_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        fields_frame.pack(fill="both", expand=True, padx=8, pady=8)

        def field_label(text):
            ctk.CTkLabel(fields_frame, text=text,
                         font=ctk.CTkFont("Helvetica", 11),
                         text_color=TEXT_SECONDARY).pack(anchor="w", **pad)

        def field_entry(placeholder, initial=""):
            e = ctk.CTkEntry(
                fields_frame, placeholder_text=placeholder,
                fg_color=BG_MID, border_color=GLASS_STROKE,
                text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_DIM,
                height=40, corner_radius=10,
                font=ctk.CTkFont("Helvetica", 13)
            )
            e.pack(fill="x", padx=24, pady=(0, 4))
            if initial:
                e.insert(0, initial)
            return e

        field_label("Full Name *")
        self.name_entry = field_entry("John Doe", contact.get("name", "") if contact else "")

        field_label("Phone *")
        self.phone_entry = field_entry("+1 555 000 0000", contact.get("phone", "") if contact else "")

        field_label("Email")
        self.email_entry = field_entry("john@example.com", contact.get("email", "") if contact else "")

        # Buttons
        btn_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(8, 16))

        ctk.CTkButton(
            btn_frame, text="Cancel", command=self.destroy,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            text_color=TEXT_SECONDARY, corner_radius=10, height=38, width=120
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Save Contact", command=self._save,
            fg_color=ACCENT_1, hover_color="#6A5FD4",
            text_color="white", corner_radius=10, height=38,
            font=ctk.CTkFont("Helvetica", 13, "bold")
        ).pack(side="right")

    def _save(self):
        name  = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()

        if not name:
            messagebox.showwarning("Missing field", "Name is required.", parent=self)
            return
        if not phone:
            messagebox.showwarning("Missing field", "Phone is required.", parent=self)
            return

        data = {
            "name": name,
            "phone": phone,
            "email": email,
            "favorite": self.contact.get("favorite", False) if self.contact else False,
            "id": self.contact.get("id") if self.contact else None,
        }
        self.on_save(data)
        self.destroy()


# ─────────────────────────────────────────────
#  Detail View Modal
# ─────────────────────────────────────────────

class ContactDetailModal(GlassModal):
    def __init__(self, parent, contact, on_edit, on_delete):
        super().__init__(parent, "Contact Details", width=400, height=480)
        self.contact = contact

        color = avatar_color(contact["name"])
        av = make_avatar_image(contact["name"][0], 80, color)
        ctk.CTkLabel(self.body, image=av, text="").pack(pady=(20, 8))

        ctk.CTkLabel(
            self.body, text=contact["name"],
            font=ctk.CTkFont("Helvetica", 22, "bold"),
            text_color=TEXT_PRIMARY
        ).pack()

        if contact.get("favorite"):
            ctk.CTkLabel(self.body, text="★ Favorite",
                         font=ctk.CTkFont("Helvetica", 12),
                         text_color=STAR_ON).pack(pady=(2, 0))

        sep = ctk.CTkFrame(self.body, height=1, fg_color=GLASS_STROKE)
        sep.pack(fill="x", padx=24, pady=14)

        def info_row(icon, value):
            if not value:
                return
            row = ctk.CTkFrame(self.body, fg_color="transparent")
            row.pack(fill="x", padx=28, pady=4)
            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont("Helvetica", 16),
                         text_color=ACCENT_2, width=28).pack(side="left")
            ctk.CTkLabel(row, text=value, font=ctk.CTkFont("Helvetica", 14),
                         text_color=TEXT_PRIMARY, anchor="w").pack(side="left")

        info_row("📞", contact.get("phone", ""))
        info_row("✉️", contact.get("email", ""))

        btn_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(20, 16))

        ctk.CTkButton(
            btn_frame, text="✏ Edit", command=lambda: [self.destroy(), on_edit(contact)],
            fg_color=ACCENT_1, hover_color="#6A5FD4",
            text_color="white", corner_radius=10, height=36, width=110
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="🗑 Delete", command=lambda: [self.destroy(), on_delete(contact)],
            fg_color=DANGER, hover_color="#CC3333",
            text_color="white", corner_radius=10, height=36, width=110
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame, text="Close", command=self.destroy,
            fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
            text_color=TEXT_SECONDARY, corner_radius=10, height=36, width=80
        ).pack(side="right", padx=(0, 8))


# ─────────────────────────────────────────────
#  Contact Card Widget
# ─────────────────────────────────────────────

class ContactCard(ctk.CTkFrame):
    def __init__(self, parent, contact, on_click, on_edit, on_delete, on_toggle_fav):
        super().__init__(
            parent,
            fg_color=BG_CARD,
            corner_radius=18,
            border_width=1,
            border_color=GLASS_STROKE
        )
        self.contact = contact
        self.on_click = on_click
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_toggle_fav = on_toggle_fav
        self._hovered = False

        self._build()
        self._bind_hover()

    def _build(self):
        c = self.contact
        color = avatar_color(c["name"])

        # Avatar
        av = make_avatar_image(c["name"][0], 56, color)
        av_lbl = ctk.CTkLabel(self, image=av, text="", cursor="hand2")
        av_lbl.pack(pady=(18, 6))
        av_lbl.bind("<Button-1>", lambda e: self.on_click(c))

        # Name
        name_lbl = ctk.CTkLabel(
            self, text=c["name"],
            font=ctk.CTkFont("Helvetica", 14, "bold"),
            text_color=TEXT_PRIMARY, cursor="hand2",
            wraplength=150
        )
        name_lbl.pack(padx=8)
        name_lbl.bind("<Button-1>", lambda e: self.on_click(c))

        # Phone
        ctk.CTkLabel(
            self, text=c.get("phone", ""),
            font=ctk.CTkFont("Helvetica", 11),
            text_color=ACCENT_2
        ).pack(pady=(2, 0))

        # Email
        email = truncate(c.get("email", ""), 24)
        if email:
            ctk.CTkLabel(
                self, text=email,
                font=ctk.CTkFont("Helvetica", 10),
                text_color=TEXT_DIM
            ).pack(pady=(1, 0))

        # Action row
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(pady=(10, 14))

        star_text = "★" if c.get("favorite") else "☆"
        star_color = STAR_ON if c.get("favorite") else STAR_OFF
        self.star_btn = ctk.CTkButton(
            actions, text=star_text, width=32, height=32,
            corner_radius=16, fg_color=BG_MID, hover_color=BG_CARD_HOVER,
            text_color=star_color, font=ctk.CTkFont("Helvetica", 14),
            command=lambda: self.on_toggle_fav(c)
        )
        self.star_btn.pack(side="left", padx=4)

        ctk.CTkButton(
            actions, text="✏", width=32, height=32,
            corner_radius=16, fg_color=BG_MID, hover_color="#3A3A6A",
            text_color=ACCENT_1, font=ctk.CTkFont("Helvetica", 12),
            command=lambda: self.on_edit(c)
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions, text="🗑", width=32, height=32,
            corner_radius=16, fg_color=BG_MID, hover_color="#4A2020",
            text_color=DANGER, font=ctk.CTkFont("Helvetica", 12),
            command=lambda: self.on_delete(c)
        ).pack(side="left", padx=4)

    def _bind_hover(self):
        def on_enter(e):
            self.configure(fg_color=BG_CARD_HOVER, border_color=ACCENT_1)
        def on_leave(e):
            self.configure(fg_color=BG_CARD, border_color=GLASS_STROKE)
        for w in self.winfo_children() + [self]:
            w.bind("<Enter>", on_enter, add="+")
            w.bind("<Leave>", on_leave, add="+")


# ─────────────────────────────────────────────
#  Main Application
# ─────────────────────────────────────────────

class ContactBookApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Contact Book")
        self.geometry("980x720")
        self.minsize(800, 600)
        self.configure(fg_color=BG_DARK)

        self.contacts: list = load_contacts()
        self._query = ""
        self._card_refs = []   # keep image refs alive

        self._build_ui()
        self._refresh_grid()

    # ── UI Construction ──────────────────────

    def _build_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=0, height=72,
                              border_width=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Accent line
        ctk.CTkFrame(header, height=3, fg_color=(ACCENT_1, ACCENT_2),
                     corner_radius=0).place(relwidth=1, rely=1, y=-3)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=28, pady=14)

        ctk.CTkLabel(
            title_frame, text="◈ Contact Book",
            font=ctk.CTkFont("Helvetica", 24, "bold"),
            text_color=TEXT_PRIMARY
        ).pack(side="left")

        self.count_badge = ctk.CTkLabel(
            title_frame, text="0",
            font=ctk.CTkFont("Helvetica", 12, "bold"),
            fg_color=ACCENT_1, corner_radius=12,
            text_color="white", width=32, height=22
        )
        self.count_badge.pack(side="left", padx=(10, 0))

        # ── Toolbar ──
        toolbar = ctk.CTkFrame(self, fg_color=BG_MID, corner_radius=0, height=60)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        search_frame = ctk.CTkFrame(toolbar, fg_color=GLASS_INNER,
                                    corner_radius=12, border_width=1,
                                    border_color=GLASS_STROKE)
        search_frame.pack(side="left", padx=20, pady=12, fill="y")

        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont("Helvetica", 14),
                     text_color=TEXT_DIM, width=28).pack(side="left", padx=(8, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._on_search())
        self.search_entry = ctk.CTkEntry(
            search_frame, textvariable=self.search_var,
            placeholder_text="Search by name or phone…",
            fg_color="transparent", border_width=0,
            text_color=TEXT_PRIMARY, placeholder_text_color=TEXT_DIM,
            font=ctk.CTkFont("Helvetica", 13), width=280, height=36
        )
        self.search_entry.pack(side="left", padx=(4, 10))

        ctk.CTkButton(
            toolbar, text="＋  Add Contact",
            fg_color=ACCENT_1, hover_color="#6A5FD4",
            text_color="white", corner_radius=12, height=40,
            font=ctk.CTkFont("Helvetica", 13, "bold"),
            command=self._open_add_form
        ).pack(side="right", padx=20, pady=10)

        # Sort / filter hint
        ctk.CTkLabel(
            toolbar, text="★ Favorites first",
            font=ctk.CTkFont("Helvetica", 11),
            text_color=TEXT_DIM
        ).pack(side="right", padx=(0, 8))

        # ── Scrollable Grid Area ──
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=BG_DARK, corner_radius=0,
            scrollbar_button_color=GLASS_STROKE,
            scrollbar_button_hover_color=ACCENT_1
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self.grid_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Make 3 columns responsive
        for col in range(3):
            self.grid_frame.columnconfigure(col, weight=1, uniform="cards")

        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.grid_frame,
            text="No contacts yet.\nClick '＋ Add Contact' to get started.",
            font=ctk.CTkFont("Helvetica", 16),
            text_color=TEXT_DIM,
            justify="center"
        )

    # ── Data Operations ───────────────────────

    def _filtered_contacts(self) -> list:
        q = self._query.lower().strip()
        result = self.contacts
        if q:
            result = [
                c for c in result
                if q in c.get("name", "").lower() or q in c.get("phone", "").lower()
            ]
        # Favorites first
        result = sorted(result, key=lambda c: (not c.get("favorite", False), c.get("name", "").lower()))
        return result

    def _save(self):
        save_contacts(self.contacts)

    def _refresh_grid(self):
        # Clear
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self._card_refs.clear()

        filtered = self._filtered_contacts()
        total = len(self.contacts)
        self.count_badge.configure(text=str(total))

        if not filtered:
            msg = "No contacts found." if self._query else "No contacts yet.\nClick '＋ Add Contact' to get started."
            ctk.CTkLabel(
                self.grid_frame, text=msg,
                font=ctk.CTkFont("Helvetica", 16),
                text_color=TEXT_DIM, justify="center"
            ).grid(row=0, column=0, columnspan=3, pady=80)
            return

        for i, contact in enumerate(filtered):
            row, col = divmod(i, 3)
            card = ContactCard(
                self.grid_frame, contact,
                on_click=self._open_detail,
                on_edit=self._open_edit_form,
                on_delete=self._confirm_delete,
                on_toggle_fav=self._toggle_favorite,
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self._card_refs.append(card)

    # ── Handlers ──────────────────────────────

    def _on_search(self):
        self._query = self.search_var.get()
        self._refresh_grid()

    def _open_add_form(self):
        def on_save(data):
            data["id"] = next_id(self.contacts)
            self.contacts.append(data)
            self._save()
            self._refresh_grid()
        ContactFormModal(self, on_save)

    def _open_edit_form(self, contact):
        def on_save(data):
            data["id"] = contact["id"]
            idx = next((i for i, c in enumerate(self.contacts) if c["id"] == contact["id"]), None)
            if idx is not None:
                self.contacts[idx] = data
            self._save()
            self._refresh_grid()
        ContactFormModal(self, on_save, contact=contact)

    def _confirm_delete(self, contact):
        ok = messagebox.askyesno(
            "Delete Contact",
            f"Are you sure you want to delete '{contact['name']}'?",
            icon="warning"
        )
        if ok:
            self.contacts = [c for c in self.contacts if c["id"] != contact["id"]]
            self._save()
            self._refresh_grid()

    def _toggle_favorite(self, contact):
        for c in self.contacts:
            if c["id"] == contact["id"]:
                c["favorite"] = not c.get("favorite", False)
                break
        self._save()
        self._refresh_grid()

    def _open_detail(self, contact):
        ContactDetailModal(
            self, contact,
            on_edit=self._open_edit_form,
            on_delete=self._confirm_delete
        )


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app = ContactBookApp()
    app.mainloop()
