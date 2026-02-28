
import customtkinter as ctk
import math
import re
from tkinter import font as tkfont


# ──────────────────────────────────────────────────────────────────
#  THEME CONSTANTS
# ──────────────────────────────────────────────────────────────────
COLORS = {
    # Backgrounds
    "body":         "#1A1A3A",   # deep translucent glass
    "body_border":  "#2E2E6A",
    "display_bg":   "#0A0A1F",   # liquid glass pool
    "display_border":"#1E1E5A",
    "history_bg":   "#12122E",
    "header_bg":    "#0F0F28",

    # Text
    "display_text": "#44FFFF",   # neon cyan glow
    "expr_text":    "#8888CC",
    "result_text":  "#44FFFF",
    "history_text": "#9999BB",
    "history_result":"#44FFFF",
    "title_text":   "#CCCCFF",
    "btn_text":     "#FFFFFF",

    # Button gradients (simulated via single color — CTk doesn't do real gradients)
    # Number buttons: blue-purple
    "num_bg":       "#3A3F9E",
    "num_hover":    "#4F55CC",
    "num_active":   "#6B46C1",

    # Operator buttons: pink-orange
    "op_bg":        "#C43B5A",
    "op_hover":     "#E54F6D",
    "op_active":    "#F59E0B",

    # Function buttons: teal-emerald
    "fn_bg":        "#0C7A8A",
    "fn_hover":     "#0EA5E9",
    "fn_active":    "#10B981",

    # Equals: vivid purple-pink
    "eq_bg":        "#7C3AED",
    "eq_hover":     "#A855F7",
    "eq_active":    "#EC4899",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


# ──────────────────────────────────────────────────────────────────
#  CALCULATOR ENGINE
# ──────────────────────────────────────────────────────────────────
class CalcEngine:
    """Pure-logic calculator engine — no UI dependency."""

    def __init__(self):
        self.expression = ""
        self.history: list[tuple[str, str]] = []   # [(expr, result), ...]
        self.max_history = 5
        self.last_result = ""
        self.just_evaluated = False

    # ── input handling ──────────────────────────────────────────
    def input(self, char: str) -> None:
        if self.just_evaluated:
            # After =, start fresh unless appending operator
            if char in "+-×÷%":
                self.expression = self.last_result + char
            else:
                self.expression = char
            self.just_evaluated = False
        else:
            self.expression += char

    def backspace(self) -> None:
        self.just_evaluated = False
        self.expression = self.expression[:-1]

    def clear(self) -> None:
        self.expression = ""
        self.last_result = ""
        self.just_evaluated = False

    def toggle_sign(self) -> None:
        self.just_evaluated = False
        if not self.expression:
            return
        # Try to negate the last number token
        m = re.search(r"(-?\d+\.?\d*)$", self.expression)
        if m:
            num_str = m.group(1)
            if num_str.startswith("-"):
                new_num = num_str[1:]
            else:
                new_num = "-" + num_str
            self.expression = self.expression[: m.start()] + new_num

    # ── evaluation ───────────────────────────────────────────────
    def evaluate(self) -> tuple[str, str]:
        """Returns (display_expr, result_str). Raises on error."""
        expr = self.expression.strip()
        if not expr:
            return "", ""

        display_expr = expr  # what we'll show as the "history" expression
        # Replace display symbols with Python operators
        safe = expr.replace("×", "*").replace("÷", "/").replace("%", "/100")

        # Safety: only allow digits, operators, dot, parens, spaces
        if not re.fullmatch(r"[\d\s\+\-\*/\.\(\)]+", safe):
            raise ValueError("Invalid expression")

        result = eval(safe, {"__builtins__": {}})  # noqa: S307

        # Format result
        if isinstance(result, float):
            if result == int(result) and abs(result) < 1e15:
                result_str = str(int(result))
            else:
                result_str = f"{result:.10g}"
        else:
            result_str = str(result)

        # Store history
        self.history.insert(0, (display_expr, result_str))
        self.history = self.history[: self.max_history]

        self.last_result = result_str
        self.just_evaluated = True
        self.expression = result_str
        return display_expr, result_str


# ──────────────────────────────────────────────────────────────────
#  GLOW EFFECT HELPER (canvas-based fake glow under a widget)
# ──────────────────────────────────────────────────────────────────
def make_glow_button(
    parent,
    text: str,
    fg_color: str,
    hover_color: str,
    active_color: str,
    command=None,
    width: int = 68,
    height: int = 68,
    font_size: int = 20,
    corner_radius: int = 26,
    text_color: str = "#FFFFFF",
):
    """Returns a CTkButton styled for the Liquid Glass theme."""
    btn = ctk.CTkButton(
        parent,
        text=text,
        fg_color=fg_color,
        hover_color=hover_color,
        text_color=text_color,
        font=ctk.CTkFont(family="Segoe UI", size=font_size, weight="bold"),
        corner_radius=corner_radius,
        width=width,
        height=height,
        command=command,
        border_width=1,
        border_color=hover_color,
    )

    # Click animation via color flash
    original_cmd = command
    def animated_cmd():
        btn.configure(fg_color=active_color)
        btn.after(120, lambda: btn.configure(fg_color=fg_color))
        if original_cmd:
            original_cmd()

    btn.configure(command=animated_cmd)
    return btn


# ──────────────────────────────────────────────────────────────────
#  HISTORY PANEL
# ──────────────────────────────────────────────────────────────────
class HistoryPanel(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["history_bg"],
            corner_radius=18,
            border_width=1,
            border_color=COLORS["body_border"],
            **kwargs,
        )
        self._build()

    def _build(self):
        title = ctk.CTkLabel(
            self,
            text="◷  HISTORY",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["history_text"],
        )
        title.pack(pady=(10, 4), padx=12, anchor="w")

        sep = ctk.CTkFrame(self, height=1, fg_color=COLORS["body_border"])
        sep.pack(fill="x", padx=10, pady=(0, 6))

        self.entries_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["body_border"],
        )
        self.entries_frame.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        self._placeholders: list[ctk.CTkFrame] = []

    def update_history(self, history: list[tuple[str, str]]):
        for widget in self.entries_frame.winfo_children():
            widget.destroy()

        if not history:
            lbl = ctk.CTkLabel(
                self.entries_frame,
                text="No calculations yet…",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLORS["history_text"],
            )
            lbl.pack(pady=20)
            return

        for expr, result in history:
            card = ctk.CTkFrame(
                self.entries_frame,
                fg_color="#1A1A3E",
                corner_radius=10,
                border_width=1,
                border_color=COLORS["body_border"],
            )
            card.pack(fill="x", pady=3, padx=2)

            expr_lbl = ctk.CTkLabel(
                card,
                text=expr,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=COLORS["history_text"],
                anchor="e",
            )
            expr_lbl.pack(fill="x", padx=8, pady=(5, 0))

            res_lbl = ctk.CTkLabel(
                card,
                text=f"= {result}",
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                text_color=COLORS["history_result"],
                anchor="e",
            )
            res_lbl.pack(fill="x", padx=8, pady=(0, 5))


# ──────────────────────────────────────────────────────────────────
#  MAIN CALCULATOR APP
# ──────────────────────────────────────────────────────────────────
class LiquidGlassCalculator(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.engine = CalcEngine()
        self._history_visible = True

        # ── window setup ─────────────────────────────────────────
        self.title("Calculator")
        self.geometry("620x640")
        self.minsize(480, 580)
        self.resizable(True, True)
        self.configure(fg_color=COLORS["header_bg"])

        self._build_ui()
        self._bind_keyboard()
        self._refresh_display()

    # ── UI construction ──────────────────────────────────────────
    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=COLORS["header_bg"], height=46, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title_lbl = ctk.CTkLabel(
            header,
            text="⬡ CALCULATOR",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["title_text"],
        )
        title_lbl.pack(side="left", padx=18)

        self.history_toggle_btn = ctk.CTkButton(
            header,
            text="◫ History",
            width=90,
            height=28,
            fg_color=COLORS["fn_bg"],
            hover_color=COLORS["fn_hover"],
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=14,
            command=self._toggle_history,
        )
        self.history_toggle_btn.pack(side="right", padx=14)

        # ── Main content row ─────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=(8, 12))

        # ── Calculator body ───────────────────────────────────────
        self.calc_body = ctk.CTkFrame(
            content,
            fg_color=COLORS["body"],
            corner_radius=24,
            border_width=1,
            border_color=COLORS["body_border"],
        )
        self.calc_body.pack(side="left", fill="both", expand=True)

        # ── History panel ─────────────────────────────────────────
        self.history_panel = HistoryPanel(content, width=165)
        self.history_panel.pack(side="right", fill="y", padx=(10, 0))

        # ── Display screen ────────────────────────────────────────
        display_frame = ctk.CTkFrame(
            self.calc_body,
            fg_color=COLORS["display_bg"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["display_border"],
            height=110,
        )
        display_frame.pack(fill="x", padx=14, pady=(14, 10))
        display_frame.pack_propagate(False)

        self.expr_var = ctk.StringVar(value="")
        self.result_var = ctk.StringVar(value="0")

        self.expr_label = ctk.CTkLabel(
            display_frame,
            textvariable=self.expr_var,
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color=COLORS["expr_text"],
            anchor="e",
        )
        self.expr_label.pack(fill="x", padx=14, pady=(10, 0))

        self.result_label = ctk.CTkLabel(
            display_frame,
            textvariable=self.result_var,
            font=ctk.CTkFont(family="Segoe UI", size=34, weight="bold"),
            text_color=COLORS["display_text"],
            anchor="e",
        )
        self.result_label.pack(fill="x", padx=14, pady=(2, 10))

        # ── Button grid ───────────────────────────────────────────
        btn_area = ctk.CTkFrame(self.calc_body, fg_color="transparent")
        btn_area.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        self._build_buttons(btn_area)

    def _build_buttons(self, parent):
        """Build the full button grid."""
        pad = dict(padx=4, pady=4, sticky="nsew")

        # Make all rows/cols expand equally
        for i in range(5):
            parent.rowconfigure(i, weight=1)
        for j in range(4):
            parent.columnconfigure(j, weight=1)

        def fn(text, cmd, col, row, colspan=1, rowspan=1):
            """Helper: create a function/C/backspace button (teal)."""
            b = make_glow_button(
                parent, text,
                fg_color=COLORS["fn_bg"],
                hover_color=COLORS["fn_hover"],
                active_color=COLORS["fn_active"],
                command=cmd,
                font_size=16,
                corner_radius=22,
            )
            b.grid(row=row, column=col, columnspan=colspan, rowspan=rowspan, **pad)

        def op(text, cmd, col, row, colspan=1, rowspan=1):
            """Helper: operator button (pink-orange)."""
            b = make_glow_button(
                parent, text,
                fg_color=COLORS["op_bg"],
                hover_color=COLORS["op_hover"],
                active_color=COLORS["op_active"],
                command=cmd,
                font_size=20,
                corner_radius=22,
            )
            b.grid(row=row, column=col, columnspan=colspan, rowspan=rowspan, **pad)

        def num(text, cmd, col, row, colspan=1, rowspan=1):
            """Helper: number button (blue-purple)."""
            b = make_glow_button(
                parent, text,
                fg_color=COLORS["num_bg"],
                hover_color=COLORS["num_hover"],
                active_color=COLORS["num_active"],
                command=cmd,
                font_size=20,
                corner_radius=22,
            )
            b.grid(row=row, column=col, columnspan=colspan, rowspan=rowspan, **pad)

        def eq_btn(col, row, colspan=1, rowspan=1):
            """Equals button (vivid purple)."""
            b = make_glow_button(
                parent, "=",
                fg_color=COLORS["eq_bg"],
                hover_color=COLORS["eq_hover"],
                active_color=COLORS["eq_active"],
                command=self._equals,
                font_size=24,
                corner_radius=22,
            )
            b.grid(row=row, column=col, columnspan=colspan, rowspan=rowspan, **pad)

        # Row 0 — function row
        fn("C",  self._clear,      0, 0)
        fn("⌫",  self._backspace,  1, 0)
        fn("%",  lambda: self._input("%"), 2, 0)
        fn("±",  self._toggle_sign,3, 0)

        # Row 1 — 7 8 9 ÷
        num("7", lambda: self._input("7"), 0, 1)
        num("8", lambda: self._input("8"), 1, 1)
        num("9", lambda: self._input("9"), 2, 1)
        op("÷",  lambda: self._input("÷"), 3, 1)

        # Row 2 — 4 5 6 ×
        num("4", lambda: self._input("4"), 0, 2)
        num("5", lambda: self._input("5"), 1, 2)
        num("6", lambda: self._input("6"), 2, 2)
        op("×",  lambda: self._input("×"), 3, 2)

        # Row 3 — 1 2 3 -
        num("1", lambda: self._input("1"), 0, 3)
        num("2", lambda: self._input("2"), 1, 3)
        num("3", lambda: self._input("3"), 2, 3)
        op("−",  lambda: self._input("-"), 3, 3)

        # Row 4 — 0 . = +
        num("0", lambda: self._input("0"), 0, 4)
        num(".", lambda: self._input("."), 1, 4)
        eq_btn(2, 4)
        op("+",  lambda: self._input("+"), 3, 4)

    # ── Logic handlers ───────────────────────────────────────────
    def _input(self, char: str):
        self.engine.input(char)
        self._refresh_display()

    def _backspace(self):
        self.engine.backspace()
        self._refresh_display()

    def _clear(self):
        self.engine.clear()
        self._refresh_display()

    def _toggle_sign(self):
        self.engine.toggle_sign()
        self._refresh_display()

    def _equals(self):
        try:
            expr, result = self.engine.evaluate()
            self.expr_var.set(expr + " =")
            self.result_var.set(result)
            self.history_panel.update_history(self.engine.history)
        except ZeroDivisionError:
            self._show_error("Division by zero!")
        except Exception:
            self._show_error("Invalid input!")

    def _show_error(self, msg: str):
        self.engine.clear()
        self.expr_var.set("")
        self.result_var.set(msg)
        self.result_label.configure(text_color="#FF6B6B")
        self.after(1600, lambda: (
            self.result_label.configure(text_color=COLORS["display_text"]),
            self._refresh_display(),
        ))

    def _refresh_display(self):
        expr = self.engine.expression
        self.expr_var.set(expr)
        if not expr:
            self.result_var.set("0")
        else:
            # Live preview
            try:
                safe = expr.replace("×", "*").replace("÷", "/").replace("%", "/100")
                if re.fullmatch(r"[\d\s\+\-\*/\.\(\)]+", safe):
                    val = eval(safe, {"__builtins__": {}})  # noqa: S307
                    if isinstance(val, float):
                        if val == int(val) and abs(val) < 1e15:
                            val = int(val)
                        self.result_var.set(f"{val:.10g}")
                    else:
                        self.result_var.set(str(val))
                else:
                    self.result_var.set("")
            except Exception:
                self.result_var.set("")

    # ── Keyboard bindings ────────────────────────────────────────
    def _bind_keyboard(self):
        mapping = {
            "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
            "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
            "+": "+", "-": "-", "*": "×", "/": "÷",
            ".": ".", "%": "%",
        }
        for key, char in mapping.items():
            self.bind(f"<KeyPress-{key}>", lambda e, c=char: self._input(c))

        self.bind("<Return>",    lambda e: self._equals())
        self.bind("<KP_Enter>",  lambda e: self._equals())
        self.bind("<BackSpace>", lambda e: self._backspace())
        self.bind("<Escape>",    lambda e: self._clear())
        self.bind("<Delete>",    lambda e: self._clear())

    # ── History toggle ────────────────────────────────────────────
    def _toggle_history(self):
        if self._history_visible:
            self.history_panel.pack_forget()
            self.history_toggle_btn.configure(text="◫ History")
            self._history_visible = False
        else:
            self.history_panel.pack(side="right", fill="y", padx=(10, 0))
            self.history_panel.update_history(self.engine.history)
            self.history_toggle_btn.configure(text="✕ History")
            self._history_visible = True


# ──────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = LiquidGlassCalculator()
    app.mainloop()
