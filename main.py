"""
main.py — ARCANE TACTICAL CORE v3.0
Дані зберігаються у ./data/ поруч із цим файлом:
  data/spellbook.json   — єдина глобальна книга заклинань
  data/characters.json  — персонажі
  data/battle_save.json — бойовий стан сесії
"""
import customtkinter as ctk

from core.data_manager import DataManager
from core.character_manager import CharacterManager
from modules.magic_left_panel import MagicLeftPanel
from modules.magic_right_panel import MagicRightPanel
from modules.melee_left_panel import MeleeLeftPanel
from modules.clash_panel import ClashPanel
from modules.characters_panel import CharactersPanel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_MONO = "Consolas"


class ArcanaTacticalCore(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ARCANE TACTICAL CORE v3.0")
        self.geometry("1380x900")
        self.minsize(1200, 760)
        self.configure(fg_color="#0d0e15")
        self.dm = DataManager()
        self.cm = CharacterManager()
        self._setup_ui()

    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1, minsize=190)
        self.grid_columnconfigure(1, weight=9)
        self.grid_rowconfigure(0, weight=1)
        self._build_aside()
        self._build_content_area()
        self.switch_mode("magic")

    def _build_aside(self):
        aside = ctk.CTkFrame(self, fg_color="#090a0f", corner_radius=0,
                              border_width=1, border_color="#1a1c2e")
        aside.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(aside, text="CORE MODE",
                     font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
                     text_color="#5f647d").pack(pady=(20, 15), padx=10, anchor="w")
        self.btn_magic = self._aside_btn(aside, "🔮 Магічний дамаг", "#00f0ff", "magic", True)
        self.btn_melee = self._aside_btn(aside, "⚔️ Фізичний дамаг", "#ffaa00", "melee", False)
        self.btn_chars = self._aside_btn(aside, "👤 Персонажі",      "#a855f7", "chars", False)
        ctk.CTkFrame(aside, fg_color="#1a1c2e", height=1).pack(fill="x", padx=10, pady=15)
        ctk.CTkLabel(aside, text="ПЕРСОНАЖІ",
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color="#5f647d").pack(padx=10, anchor="w")
        self.lbl_char_count = ctk.CTkLabel(aside, text="",
                                            font=ctk.CTkFont(family=FONT_MONO, size=11),
                                            text_color="#787c99")
        self.lbl_char_count.pack(padx=10, anchor="w")
        self._update_char_count()

    def _aside_btn(self, parent, text, color, mode, active):
        btn = ctk.CTkButton(
            parent, text=text,
            font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            fg_color="#1a1c2e" if active else "transparent",
            text_color=color if active else "#a9b1d6",
            height=40, corner_radius=4, anchor="w",
            command=lambda m=mode: self.switch_mode(m)
        )
        btn.pack(fill="x", padx=10, pady=5)
        return btn

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.content.grid_columnconfigure(0, weight=5, uniform="cols")
        self.content.grid_columnconfigure(1, weight=6, uniform="cols")
        self.content.grid_rowconfigure(0, weight=1)

        self.magic_left_frame  = ctk.CTkFrame(self.content, fg_color="#11121c", corner_radius=0)
        self.melee_left_frame  = ctk.CTkFrame(self.content, fg_color="#11121c", corner_radius=0)
        self.magic_right_frame = ctk.CTkFrame(self.content, fg_color="#141624", corner_radius=0)
        self.melee_right_frame = ctk.CTkFrame(self.content, fg_color="#141624", corner_radius=0)
        self.chars_frame       = ctk.CTkFrame(self.content, fg_color="#11121c", corner_radius=0)

        # MagicLeftPanel тепер отримує cm для запису у спеллбук
        self.magic_left = MagicLeftPanel(
            self.magic_left_frame, self.dm,
            char_manager=self.cm,
            on_save_callback=self._on_magic_template_saved
        )
        self.magic_right = MagicRightPanel(self.magic_right_frame, self.dm, self.cm)
        self.magic_right.bind_load_template_callback(self.magic_left.load_template)

        self.melee_left  = MeleeLeftPanel(self.melee_left_frame, self.dm, self.cm)
        self.clash_panel = ClashPanel(self.melee_right_frame, self.dm, self.cm)

        self.chars_panel = CharactersPanel(
            self.chars_frame, self.cm,
            on_change_callback=self._on_characters_changed
        )

    def switch_mode(self, mode: str):
        self.btn_magic.configure(fg_color="transparent", text_color="#a9b1d6")
        self.btn_melee.configure(fg_color="transparent", text_color="#a9b1d6")
        self.btn_chars.configure(fg_color="transparent", text_color="#a9b1d6")
        for f in [self.magic_left_frame, self.magic_right_frame,
                   self.melee_left_frame, self.melee_right_frame, self.chars_frame]:
            f.grid_forget()

        if mode == "magic":
            self.btn_magic.configure(fg_color="#1a1c2e", text_color="#00f0ff")
            self.magic_left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.magic_right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        elif mode == "melee":
            self.btn_melee.configure(fg_color="#1a1c2e", text_color="#ffaa00")
            self.melee_left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.melee_right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
            self.melee_left._refresh_char_list()
            self.clash_panel._refresh_char_lists()
            self.melee_left.action_calculate()
        elif mode == "chars":
            self.btn_chars.configure(fg_color="#1a1c2e", text_color="#a855f7")
            self.chars_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

    def _on_magic_template_saved(self):
        """Після збереження руни — оновлюємо спеллбук у правій панелі."""
        self.magic_right.refresh_spellbook()

    def _on_characters_changed(self):
        self.magic_right.refresh_all()
        self.melee_left._refresh_char_list()
        self.clash_panel._refresh_char_lists()
        self._update_char_count()

    def _update_char_count(self):
        chars = self.cm.get_sorted()
        players = sum(1 for c in chars if c.get("is_player"))
        npcs = len(chars) - players
        self.lbl_char_count.configure(text=f"★ Гравці: {players}  ○ НПС: {npcs}")


if __name__ == "__main__":
    app = ArcanaTacticalCore()
    app.mainloop()
