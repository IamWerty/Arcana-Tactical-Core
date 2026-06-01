"""
ui/widgets.py
=============
Спільні хелпери для створення типових UI-елементів.
Всі функції повертають створений widget.
"""
import customtkinter as ctk

FONT_MONO = "Consolas"


def make_label(container, text: str, color: str, size: int = 11):
    lbl = ctk.CTkLabel(
        container, text=text,
        font=ctk.CTkFont(family=FONT_MONO, size=size, weight="bold"),
        text_color=color
    )
    lbl.pack(anchor="w", padx=10, pady=(12, 2))
    return lbl


def make_dropdown(container, label_text: str, values: list, width: int = 210) -> ctk.CTkComboBox:
    frame = ctk.CTkFrame(container, fg_color="transparent")
    frame.pack(fill="x", padx=10, pady=3)
    ctk.CTkLabel(
        frame, text=label_text,
        font=ctk.CTkFont(family=FONT_MONO, size=12),
        text_color="#787c99"
    ).pack(side="left")
    cb = ctk.CTkComboBox(
        frame, values=values, width=width,
        fg_color="#1e2030", border_color="#2f334d",
        text_color="#c0caf5", corner_radius=6
    )
    cb.pack(side="right")
    return cb


def make_input(container, label_text: str, default_val: str, width: int = 210) -> ctk.CTkEntry:
    frame = ctk.CTkFrame(container, fg_color="transparent")
    frame.pack(fill="x", padx=10, pady=3)
    ctk.CTkLabel(
        frame, text=label_text,
        font=ctk.CTkFont(family=FONT_MONO, size=12),
        text_color="#787c99"
    ).pack(side="left")
    ent = ctk.CTkEntry(
        frame, width=width,
        fg_color="#1e2030", border_color="#2f334d",
        text_color="#c0caf5", corner_radius=6
    )
    ent.insert(0, default_val)
    ent.pack(side="right")
    return ent


def make_section_title(container, text: str, color: str = "#00f0ff", size: int = 14):
    lbl = ctk.CTkLabel(
        container, text=text,
        font=ctk.CTkFont(family=FONT_MONO, size=size, weight="bold"),
        text_color=color
    )
    lbl.pack(anchor="w", padx=10, pady=(15, 2))
    return lbl
