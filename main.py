"""
main.py
=======
Точка входу. Тільки оркестрація — режими, сітка, перемикання.
Бізнес-логіки тут немає.

Архітектура:
  main.py
  ├── core/
  │   ├── data_manager.py   — стан, JSON save/load, clash state
  │   ├── magic_engine.py   — математика магії
  │   └── melee_engine.py   — математика фізичного бою + clash раунди
  ├── ui/
  │   └── widgets.py        — спільні хелпери UI
  └── modules/
      ├── magic_left_panel.py   — ліва панель магічного режиму
      ├── magic_right_panel.py  — права панель магічного режиму (батарейки, банк, активні)
      ├── melee_left_panel.py   — ліва панель фізичного режиму
      └── clash_panel.py        — права панель фізичного режиму (Clash система)
"""
import customtkinter as ctk

from core.data_manager import DataManager
from modules.magic_left_panel import MagicLeftPanel
from modules.magic_right_panel import MagicRightPanel
from modules.melee_left_panel import MeleeLeftPanel
from modules.clash_panel import ClashPanel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

FONT_MONO = "Consolas"


class ArcanaTacticalCore(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ARCANE TACTICAL CORE v2.0")
        self.geometry("1300x850")
        self.minsize(1150, 750)
        self.configure(fg_color="#0d0e15")

        self.dm = DataManager()
        self._setup_ui()

    # =========================================================================
    # LAYOUT
    # =========================================================================
    def _setup_ui(self):
        # Головна сітка: [Aside (0)] | [Контент (1)]
        self.grid_columnconfigure(0, weight=1, minsize=180)
        self.grid_columnconfigure(1, weight=9)
        self.grid_rowconfigure(0, weight=1)

        self._build_aside()
        self._build_content_area()

        # Дефолтний режим
        self.switch_mode("magic")

    def _build_aside(self):
        aside = ctk.CTkFrame(self, fg_color="#090a0f", corner_radius=0,
                              border_width=1, border_color="#1a1c2e")
        aside.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(aside, text="CORE MODE",
                     font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
                     text_color="#5f647d").pack(pady=(20, 15), padx=10, anchor="w")

        self.btn_magic = ctk.CTkButton(
            aside, text="🔮 Магічний дамаг",
            font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            fg_color="#1a1c2e", text_color="#00f0ff",
            height=40, corner_radius=4, anchor="w",
            command=lambda: self.switch_mode("magic")
        )
        self.btn_magic.pack(fill="x", padx=10, pady=5)

        self.btn_melee = ctk.CTkButton(
            aside, text="⚔️ Фізичний дамаг",
            font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            fg_color="transparent", text_color="#a9b1d6",
            height=40, corner_radius=4, anchor="w",
            command=lambda: self.switch_mode("melee")
        )
        self.btn_melee.pack(fill="x", padx=10, pady=5)

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Ліва + Права колонки
        self.content.grid_columnconfigure(0, weight=5, uniform="cols")
        self.content.grid_columnconfigure(1, weight=6, uniform="cols")
        self.content.grid_rowconfigure(0, weight=1)

        # ── Ліві фрейми (по одному на режим) ──
        self.magic_left_frame = ctk.CTkFrame(self.content, fg_color="#11121c", corner_radius=0)
        self.melee_left_frame = ctk.CTkFrame(self.content, fg_color="#11121c", corner_radius=0)

        # ── Праві фрейми (по одному на режим) ──
        self.magic_right_frame = ctk.CTkFrame(self.content, fg_color="#141624", corner_radius=0)
        self.melee_right_frame = ctk.CTkFrame(self.content, fg_color="#141624", corner_radius=0)

        # ── Ініціалізація модулів ──
        self.magic_left = MagicLeftPanel(
            self.magic_left_frame, self.dm,
            on_save_callback=self._on_magic_template_saved
        )
        self.magic_right = MagicRightPanel(self.magic_right_frame, self.dm)
        self.magic_right.bind_load_template_callback(self.magic_left.load_template)

        self.melee_left = MeleeLeftPanel(self.melee_left_frame, self.dm)
        self.clash_panel = ClashPanel(self.melee_right_frame, self.dm)

    # =========================================================================
    # MODE SWITCHING
    # =========================================================================
    def switch_mode(self, mode: str):
        if mode == "magic":
            self.btn_magic.configure(fg_color="#1a1c2e", text_color="#00f0ff")
            self.btn_melee.configure(fg_color="transparent", text_color="#a9b1d6")

            # Ховаємо melee, показуємо magic
            self.melee_left_frame.grid_forget()
            self.melee_right_frame.grid_forget()
            self.magic_left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.magic_right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        elif mode == "melee":
            self.btn_melee.configure(fg_color="#1a1c2e", text_color="#ffaa00")
            self.btn_magic.configure(fg_color="transparent", text_color="#a9b1d6")

            # Ховаємо magic, показуємо melee
            self.magic_left_frame.grid_forget()
            self.magic_right_frame.grid_forget()
            self.melee_left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.melee_right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

            self.melee_left.action_calculate()

    # =========================================================================
    # CALLBACKS (між модулями)
    # =========================================================================
    def _on_magic_template_saved(self):
        """Викликається після збереження шаблона у MagicLeftPanel — оновлює банк."""
        self.magic_right.refresh_templates()


if __name__ == "__main__":
    app = ArcanaTacticalCore()
    app.mainloop()
