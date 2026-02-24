import customtkinter as ctk
import json
import os
from datetime import datetime
from tkinter import messagebox
import tkinter as tk


# ── Constants ──────────────────────────────────────────────────────────────────
TASKS_FILE = "tasks.json"

COLORS = {
    "bg_dark":       "#0A0A1F",
    "bg_mid":        "#12122A",
    "bg_card":       "#1E1E3C",
    "bg_card_hover": "#252545",
    "glass":         "#1A1A38",
    "glass_border":  "#2E2E5A",
    "accent_blue":   "#4A90FF",
    "accent_purple": "#8B5CF6",
    "text_primary":  "#E8E8FF",
    "text_secondary":"#8888BB",
    "text_muted":    "#5555AA",
    "high":          "#FF4444",
    "medium":        "#FFDD44",
    "low":           "#44FF88",
    "success":       "#44FF88",
    "danger":        "#FF4444",
    "warning":       "#FFDD44",
    "btn_add":       "#4A90FF",
    "btn_add_hover": "#5AA0FF",
    "complete_bg":   "#1A3A2A",
}

PRIORITY_COLORS = {"High": COLORS["high"], "Medium": COLORS["medium"], "Low": COLORS["low"]}
PRIORITY_BG     = {"High": "#2A1A1A",      "Medium": "#2A2A1A",         "Low": "#1A2A1A"}


# ── Data Layer ─────────────────────────────────────────────────────────────────
def load_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)


def new_task(text, priority="Medium"):
    return {
        "id": int(datetime.now().timestamp() * 1000),
        "text": text,
        "priority": priority,
        "completed": False,
        "created": datetime.now().isoformat()
    }


# ── Main Application ───────────────────────────────────────────────────────────
class TodoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("✦ Todo List")
        self.geometry("760x900")
        self.minsize(600, 700)
        self.configure(fg_color=COLORS["bg_dark"])

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.tasks = load_tasks()
        self.current_filter = "All"
        self.edit_id = None

        self._build_ui()
        self._refresh_tasks()

    # ── UI Construction ────────────────────────────────────────────────────────
    def _build_ui(self):
        # Root scroll container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        outer = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_rowconfigure(3, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        self._build_header(outer)
        self._build_input(outer)
        self._build_filters(outer)
        self._build_task_area(outer)
        self._build_footer(outer)

    def _build_header(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color=COLORS["glass"], corner_radius=20,
                            border_width=1, border_color=COLORS["glass_border"])
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 8))
        hdr.grid_columnconfigure(1, weight=1)

        # Glow dot
        dot = ctk.CTkLabel(hdr, text="◈", font=("Georgia", 28), text_color=COLORS["accent_blue"])
        dot.grid(row=0, column=0, padx=(20, 10), pady=18)

        title_col = ctk.CTkFrame(hdr, fg_color="transparent")
        title_col.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(title_col, text="Todo List",
                     font=("Georgia", 22, "bold"), text_color=COLORS["text_primary"]
                     ).pack(anchor="w")
        ctk.CTkLabel(title_col, text="Material Expressive · Glass Edition",
                     font=("Helvetica", 11), text_color=COLORS["text_muted"]
                     ).pack(anchor="w")

        date_str = datetime.now().strftime("%A, %B %d")
        ctk.CTkLabel(hdr, text=date_str, font=("Helvetica", 12),
                     text_color=COLORS["text_secondary"]
                     ).grid(row=0, column=2, padx=20, pady=18)

    def _build_input(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["glass"], corner_radius=18,
                             border_width=1, border_color=COLORS["glass_border"])
        frame.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        frame.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(inner, text="New Task", font=("Helvetica", 11, "bold"),
                     text_color=COLORS["text_muted"]).grid(row=0, column=0, sticky="w", pady=(0, 4))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew")
        row.grid_columnconfigure(0, weight=1)

        self.task_entry = ctk.CTkEntry(
            row, placeholder_text="✦ What needs to be done?",
            height=44, corner_radius=12,
            fg_color=COLORS["bg_card"], border_color=COLORS["glass_border"],
            text_color=COLORS["text_primary"],
            placeholder_text_color=COLORS["text_muted"],
            font=("Helvetica", 13)
        )
        self.task_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.task_entry.bind("<Return>", lambda e: self._add_or_save())

        self.priority_var = ctk.StringVar(value="Medium")
        prio = ctk.CTkOptionMenu(
            row, values=["High", "Medium", "Low"],
            variable=self.priority_var, width=110, height=44, corner_radius=12,
            fg_color=COLORS["bg_card"], button_color=COLORS["bg_card"],
            button_hover_color=COLORS["bg_card_hover"],
            dropdown_fg_color=COLORS["bg_mid"],
            text_color=COLORS["text_primary"],
            font=("Helvetica", 13)
        )
        prio.grid(row=0, column=1, padx=(0, 8))

        self.add_btn = ctk.CTkButton(
            row, text="Add Task", width=110, height=44, corner_radius=12,
            fg_color=COLORS["btn_add"], hover_color=COLORS["btn_add_hover"],
            text_color="white", font=("Helvetica", 13, "bold"),
            command=self._add_or_save
        )
        self.add_btn.grid(row=0, column=2)

        self.cancel_btn = ctk.CTkButton(
            row, text="Cancel", width=80, height=44, corner_radius=12,
            fg_color=COLORS["bg_card"], hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_secondary"], font=("Helvetica", 12),
            command=self._cancel_edit
        )
        self.cancel_btn.grid(row=0, column=3, padx=(6, 0))
        self.cancel_btn.grid_remove()

    def _build_filters(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 8))

        self.filter_btns = {}
        for label in ["All", "Active", "Completed"]:
            btn = ctk.CTkButton(
                frame, text=label, width=100, height=34, corner_radius=17,
                font=("Helvetica", 12, "bold"),
                command=lambda l=label: self._set_filter(l)
            )
            btn.pack(side="left", padx=(0, 8))
            self.filter_btns[label] = btn

        self._update_filter_styles()

    def _build_task_area(self, parent):
        self.task_scroll = ctk.CTkScrollableFrame(
            parent, fg_color=COLORS["bg_dark"], corner_radius=0,
            scrollbar_button_color=COLORS["glass_border"],
            scrollbar_button_hover_color=COLORS["text_muted"]
        )
        self.task_scroll.grid(row=3, column=0, sticky="nsew", padx=20, pady=0)
        self.task_scroll.grid_columnconfigure(0, weight=1)

        self.empty_label = ctk.CTkLabel(
            self.task_scroll, text="✦ No tasks here yet\nAdd one above to get started",
            font=("Helvetica", 14), text_color=COLORS["text_muted"],
            justify="center"
        )

    def _build_footer(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["glass"], corner_radius=18,
                             border_width=1, border_color=COLORS["glass_border"])
        frame.grid(row=4, column=0, sticky="ew", padx=20, pady=(8, 20))

        inner = ctk.CTkFrame(frame, fg_color="transparent")
        inner.pack(padx=20, pady=12)

        self.stat_total = self._stat_pill(inner, "Total", "0", COLORS["accent_blue"])
        self.stat_done  = self._stat_pill(inner, "Completed", "0", COLORS["success"])
        self.stat_pend  = self._stat_pill(inner, "Pending", "0", COLORS["warning"])

    def _stat_pill(self, parent, label, value, color):
        pill = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=14)
        pill.pack(side="left", padx=8)
        ctk.CTkLabel(pill, text=value, font=("Georgia", 22, "bold"), text_color=color
                     ).pack(padx=16, pady=(8, 0))
        ctk.CTkLabel(pill, text=label, font=("Helvetica", 10), text_color=COLORS["text_muted"]
                     ).pack(padx=16, pady=(0, 8))
        return pill.winfo_children()[0]  # returns the value label

    # ── Task Rendering ─────────────────────────────────────────────────────────
    def _refresh_tasks(self):
        for w in self.task_scroll.winfo_children():
            w.destroy()

        filtered = [t for t in self.tasks if self._passes_filter(t)]

        if not filtered:
            self.empty_label = ctk.CTkLabel(
                self.task_scroll,
                text="✦ No tasks here\nAdd one above to get started",
                font=("Helvetica", 14), text_color=COLORS["text_muted"], justify="center"
            )
            self.empty_label.pack(pady=80)
        else:
            for i, task in enumerate(filtered):
                self._render_card(task, i)

        self._update_stats()
        self._update_filter_styles()

    def _passes_filter(self, task):
        if self.current_filter == "Active":    return not task["completed"]
        if self.current_filter == "Completed": return task["completed"]
        return True

    def _render_card(self, task, idx):
        pcolor = PRIORITY_COLORS.get(task["priority"], COLORS["text_muted"])
        is_done = task["completed"]
        card_bg = COLORS["complete_bg"] if is_done else COLORS["bg_card"]

        outer = ctk.CTkFrame(self.task_scroll, fg_color=pcolor, corner_radius=16)
        outer.grid(row=idx, column=0, sticky="ew", pady=4)
        outer.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(outer, fg_color=card_bg, corner_radius=14)
        inner.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)
        inner.grid_columnconfigure(1, weight=1)

        # Checkbox
        check_var = ctk.BooleanVar(value=is_done)
        chk = ctk.CTkCheckBox(
            inner, text="", variable=check_var, width=30, height=30,
            checkbox_width=22, checkbox_height=22, corner_radius=11,
            fg_color=pcolor, hover_color=pcolor,
            border_color=COLORS["glass_border"],
            command=lambda t=task, v=check_var: self._toggle(t, v)
        )
        chk.grid(row=0, column=0, padx=(14, 8), pady=16)

        # Text
        font_strike = ("Helvetica", 13)
        text_color  = COLORS["text_muted"] if is_done else COLORS["text_primary"]
        display     = f"̶{task['text']}̶" if is_done else task["text"]

        txt = ctk.CTkLabel(inner, text=task["text"], font=font_strike,
                           text_color=text_color, anchor="w", wraplength=380, justify="left")
        if is_done:
            txt.configure(text_color=COLORS["text_muted"])
        txt.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=16)

        # Strike line overlay for completed
        if is_done:
            txt.configure(font=("Helvetica", 13))
            # We'll just mute it; true strikethrough requires tkinter Text widget

        # Priority badge
        badge = ctk.CTkLabel(inner, text=task["priority"],
                             font=("Helvetica", 10, "bold"), text_color="black",
                             fg_color=pcolor, corner_radius=8,
                             width=60, height=22)
        badge.grid(row=0, column=2, padx=6, pady=16)

        # Buttons
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.grid(row=0, column=3, padx=(0, 12), pady=16)

        edit_btn = ctk.CTkButton(
            btn_frame, text="✎", width=32, height=32, corner_radius=10,
            fg_color=COLORS["glass"], hover_color=COLORS["glass_border"],
            text_color=COLORS["accent_blue"], font=("Helvetica", 14),
            command=lambda t=task: self._start_edit(t)
        )
        edit_btn.pack(side="left", padx=(0, 4))

        del_btn = ctk.CTkButton(
            btn_frame, text="✕", width=32, height=32, corner_radius=10,
            fg_color=COLORS["glass"], hover_color="#3A1A1A",
            text_color=COLORS["danger"], font=("Helvetica", 14),
            command=lambda t=task: self._delete(t)
        )
        del_btn.pack(side="left")

    # ── Actions ────────────────────────────────────────────────────────────────
    def _add_or_save(self):
        text = self.task_entry.get().strip()
        if not text:
            self.task_entry.configure(border_color=COLORS["danger"])
            self.after(800, lambda: self.task_entry.configure(border_color=COLORS["glass_border"]))
            return

        if self.edit_id is not None:
            for t in self.tasks:
                if t["id"] == self.edit_id:
                    t["text"] = text
                    t["priority"] = self.priority_var.get()
                    break
            self.edit_id = None
            self.add_btn.configure(text="Add Task")
            self.cancel_btn.grid_remove()
        else:
            self.tasks.append(new_task(text, self.priority_var.get()))

        save_tasks(self.tasks)
        self.task_entry.delete(0, "end")
        self.priority_var.set("Medium")
        self._refresh_tasks()

    def _start_edit(self, task):
        self.edit_id = task["id"]
        self.task_entry.delete(0, "end")
        self.task_entry.insert(0, task["text"])
        self.priority_var.set(task["priority"])
        self.add_btn.configure(text="Save Task")
        self.cancel_btn.grid()
        self.task_entry.focus()

    def _cancel_edit(self):
        self.edit_id = None
        self.task_entry.delete(0, "end")
        self.priority_var.set("Medium")
        self.add_btn.configure(text="Add Task")
        self.cancel_btn.grid_remove()

    def _toggle(self, task, var):
        task["completed"] = var.get()
        save_tasks(self.tasks)
        self._refresh_tasks()

    def _delete(self, task):
        if messagebox.askyesno("Delete Task", f'Delete "{task["text"]}"?', parent=self):
            self.tasks = [t for t in self.tasks if t["id"] != task["id"]]
            if self.edit_id == task["id"]:
                self._cancel_edit()
            save_tasks(self.tasks)
            self._refresh_tasks()

    def _set_filter(self, f):
        self.current_filter = f
        self._refresh_tasks()

    def _update_filter_styles(self):
        for label, btn in self.filter_btns.items():
            if label == self.current_filter:
                btn.configure(fg_color=COLORS["accent_blue"], text_color="white",
                              hover_color=COLORS["btn_add_hover"])
            else:
                btn.configure(fg_color=COLORS["glass"], text_color=COLORS["text_secondary"],
                              hover_color=COLORS["glass_border"])

    def _update_stats(self):
        total = len(self.tasks)
        done  = sum(1 for t in self.tasks if t["completed"])
        pend  = total - done
        self.stat_total.configure(text=str(total))
        self.stat_done.configure(text=str(done))
        self.stat_pend.configure(text=str(pend))


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
