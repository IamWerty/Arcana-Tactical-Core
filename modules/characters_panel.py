"""
modules/characters_panel.py
============================
Вкладка "Персонажі".
Ліворуч — список карточок (прокрутка), праворуч — бланк персонажа.
Пункт 4 ТЗ: клікабельні картки, миттєва зміна зірочки.
"""
import customtkinter as ctk
from core.character_manager import CharacterManager, stat_modifier
from modules.character_sheet import CharacterSheet
from modules.character_create_dialog import CharacterCreateDialog
from ui.widgets import FONT_MONO

ACCENT = "#00f0ff"
WARN   = "#ffaa00"
PINK   = "#ff007f"


class CharactersPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, cm: CharacterManager,
                 on_change_callback=None):
        self.cm = cm
        self._on_change = on_change_callback
        self._selected_id: str | None = None

        parent_frame.grid_columnconfigure(0, weight=3)
        parent_frame.grid_columnconfigure(1, weight=7)
        parent_frame.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(parent_frame, fg_color="#0f1018", corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        self._build_left(left)

        right = ctk.CTkFrame(parent_frame, fg_color="#11121c", corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        self.sheet = CharacterSheet(right, cm)

        self._refresh_list()

    # =========================================================================
    def _build_left(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(12, 6))
        ctk.CTkLabel(hdr, text="ПЕРСОНАЖІ",
                     font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
                     text_color=ACCENT).pack(side="left")
        ctk.CTkButton(hdr, text="+ Новий", width=75, height=28,
                      fg_color="#1a1c2e", text_color=ACCENT, corner_radius=5,
                      font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                      command=self._open_create_dialog).pack(side="right")

        self._list_scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self._list_scroll.pack(fill="both", expand=True, padx=5, pady=5)

    def _refresh_list(self):
        for w in self._list_scroll.winfo_children():
            w.destroy()

        chars = self.cm.get_sorted()
        if not chars:
            ctk.CTkLabel(self._list_scroll,
                         text="// Немає персонажів\n// Натисніть + Новий",
                         font=ctk.CTkFont(family=FONT_MONO, size=12),
                         text_color="#3a3c52", justify="center").pack(pady=40)
            return

        players = [c for c in chars if c.get("is_player")]
        npcs    = [c for c in chars if not c.get("is_player")]

        if players:
            self._group_label("★  ГРАВЦІ")
            for char in players:
                self._char_card(char)
        if npcs:
            self._group_label("○  НПС")
            for char in npcs:
                self._char_card(char)

    def _group_label(self, text: str):
        ctk.CTkLabel(self._list_scroll, text=text,
                     font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                     text_color="#5f647d").pack(anchor="w", padx=8, pady=(10, 2))

    def _char_card(self, char: dict):
        cid = char["id"]
        is_selected = cid == self._selected_id
        bg     = "#1e2040" if is_selected else "#181929"
        border = ACCENT    if is_selected else "#2a2c40"

        card = ctk.CTkFrame(self._list_scroll, fg_color=bg,
                            border_width=1, border_color=border, corner_radius=6,
                            cursor="hand2")
        card.pack(fill="x", padx=5, pady=3)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=8, pady=6)

        # Рядок 1: ім'я + зірочка-кнопка
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x")

        ctk.CTkLabel(row1, text=char["name"],
                     font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
                     text_color="#c0caf5").pack(side="left")

        # Зірочка — миттєва зміна гравець/НПС (пункт 4)
        is_player = char.get("is_player", True)
        star_btn = ctk.CTkButton(
            row1,
            text="★" if is_player else "○",
            width=28, height=22, corner_radius=4,
            fg_color="#2a3a2a" if is_player else "#2a2a3a",
            hover_color="#3a5a3a" if is_player else "#3a3a5a",
            text_color=WARN if is_player else "#5f647d",
            font=ctk.CTkFont(size=13),
            command=lambda c=char: self._toggle_star(c)
        )
        star_btn.pack(side="right")

        # Рядок 2: Клас / Раса / Рівень
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(2, 0))
        cls_col = ACCENT if char.get("char_class") == "Маг" else WARN
        ctk.CTkLabel(row2,
                     text=f"{char['race']}  :  {char.get('char_class','')}  •  Рівень {char.get('level',1)}",
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color=cls_col).pack(side="left")

        # Рядок 3: стислі модифікатори + кнопка видалення
        row3 = ctk.CTkFrame(inner, fg_color="transparent")
        row3.pack(fill="x", pady=(2, 0))

        stats = char.get("stats", {})
        short = {"Сила": "STR", "Ловкість": "DEX", "Статура": "CON",
                 "Інтелект": "INT", "Мудрість": "WIS", "Харизма": "CHA"}
        mods_str = "  ".join(
            f"{short.get(s, s[:3])}:{(stat_modifier(stats[s]['value']) + stats[s]['bonus']):+}"
            for s in short if s in stats
        )
        ctk.CTkLabel(row3, text=mods_str,
                     font=ctk.CTkFont(family=FONT_MONO, size=9),
                     text_color="#5f647d").pack(side="left")

        ctk.CTkButton(row3, text="🗑", width=24, height=20,
                      fg_color="transparent", text_color="#ff5555",
                      font=ctk.CTkFont(size=11),
                      command=lambda c=cid: self._delete_char(c)).pack(side="right")

        # Клік по всій картці (крім кнопок)
        for widget in [card, inner, row1, row2, row3]:
            widget.bind("<Button-1>", lambda e, c=cid: self._select(c))

    def _select(self, char_id: str):
        self._selected_id = char_id
        self._refresh_list()
        self.sheet.load(char_id)

    def _toggle_star(self, char: dict):
        """Миттєво перемикає гравець/НПС і оновлює список."""
        char["is_player"] = not char.get("is_player", True)
        self.cm.save_characters()
        self._refresh_list()
        if self._on_change:
            self._on_change()
        # Якщо цей персонаж відкритий у бланку — оновлюємо кнопку там теж
        if char["id"] == self._selected_id:
            btn = self.sheet._entries.get("_star_btn")
            if btn:
                is_p = char["is_player"]
                btn.configure(
                    text="★ Гравець" if is_p else "○ НПС",
                    fg_color="#2a3a2a" if is_p else "#2a2a3a",
                    hover_color="#3a4a3a" if is_p else "#3a3a4a",
                    text_color=WARN if is_p else "#5f647d"
                )

    def _delete_char(self, char_id: str):
        self.cm.delete_character(char_id)
        if self._selected_id == char_id:
            self._selected_id = None
        self._refresh_list()
        if self._on_change:
            self._on_change()

    def _open_create_dialog(self):
        CharacterCreateDialog(self._list_scroll.winfo_toplevel(), self._on_created)

    def _on_created(self, data: dict):
        self.cm.create_character(
            name=data["name"],
            race=data["race"],
            char_class=data["char_class"],
            weapon_name=data.get("weapon_name", ""),
            weapon_dk=data.get("weapon_dk", 6),
            is_player=data.get("is_player", True)
        )
        self._refresh_list()
        if self._on_change:
            self._on_change()
