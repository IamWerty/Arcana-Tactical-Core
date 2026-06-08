"""
modules/character_create_dialog.py
===================================
Діалог створення нового персонажа.
Повертає дані через callback після підтвердження або None при скасуванні.
"""
import customtkinter as ctk
from core.character_manager import ALL_RACES, CLASSES

FONT_MONO = "Consolas"
WEAPON_DK_OPTIONS = ["d4 (Легка зброя)", "d6 (Стандарт)", "d8 (Полуторна)",
                     "d10 (Важка)", "d12 (Дворучна важка)"]
DK_MAP = {"d4": 4, "d6": 6, "d8": 8, "d10": 10, "d12": 12}


class CharacterCreateDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_confirm_callback):
        super().__init__(parent)
        self.on_confirm = on_confirm_callback
        self.title("СТВОРЕННЯ ПЕРСОНАЖА")
        self.geometry("480x520")
        self.resizable(False, False)
        self.grab_set()
        self.configure(fg_color="#0d0e15")

        self._build()
        self._on_class_change(None)

    def _build(self):
        # Заголовок
        ctk.CTkLabel(self, text="// ІНІЦІАЛІЗАЦІЯ НОВОЇ СУТНОСТІ",
                     font=ctk.CTkFont(family=FONT_MONO, size=16, weight="bold"),
                     text_color="#00f0ff").pack(pady=(20, 5))
        ctk.CTkLabel(self, text="Заповніть параметри персонажа",
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#5f647d").pack(pady=(0, 15))

        form = ctk.CTkFrame(self, fg_color="#11121c", corner_radius=8)
        form.pack(fill="x", padx=20, pady=5)

        # Ім'я
        self._row(form, "Ім'я персонажа:")
        self.ent_name = ctk.CTkEntry(form, fg_color="#1e2030", border_color="#2f334d",
                                      text_color="#c0caf5", corner_radius=6, width=280,
                                      font=ctk.CTkFont(family=FONT_MONO, size=12))
        self.ent_name.pack(fill="x", padx=15, pady=(0, 10))

        # Раса
        self._row(form, "Раса:")
        self.cb_race = ctk.CTkComboBox(form, values=ALL_RACES, width=280,
                                        fg_color="#1e2030", border_color="#2f334d",
                                        text_color="#c0caf5", corner_radius=6)
        self.cb_race.set(ALL_RACES[0])
        self.cb_race.pack(fill="x", padx=15, pady=(0, 10))

        # Клас
        self._row(form, "Клас:")
        self.cb_class = ctk.CTkComboBox(form, values=CLASSES, width=280,
                                         fg_color="#1e2030", border_color="#2f334d",
                                         text_color="#c0caf5", corner_radius=6,
                                         command=self._on_class_change)
        self.cb_class.set(CLASSES[0])
        self.cb_class.pack(fill="x", padx=15, pady=(0, 10))

        # Тип (гравець / НПС)
        self._row(form, "Тип:")
        self.cb_type = ctk.CTkComboBox(form, values=["★ Гравець", "○ НПС"], width=280,
                                        fg_color="#1e2030", border_color="#2f334d",
                                        text_color="#c0caf5", corner_radius=6)
        self.cb_type.set("★ Гравець")
        self.cb_type.pack(fill="x", padx=15, pady=(0, 10))

        # Блок мечника
        self.warrior_frame = ctk.CTkFrame(self, fg_color="#191a2a", corner_radius=8)
        self.warrior_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.warrior_frame, text="// ЗБРОЯ МЕЧНИКА",
                     font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
                     text_color="#ffaa00").pack(anchor="w", padx=15, pady=(10, 5))

        self._row(self.warrior_frame, "Ім'я зброї:")
        self.ent_weapon = ctk.CTkEntry(self.warrior_frame, fg_color="#1e2030",
                                        border_color="#2f334d", text_color="#c0caf5",
                                        corner_radius=6, width=280,
                                        font=ctk.CTkFont(family=FONT_MONO, size=12))
        self.ent_weapon.insert(0, "Довгий меч")
        self.ent_weapon.pack(fill="x", padx=15, pady=(0, 5))

        self._row(self.warrior_frame, "Кубик зброї (dK):")
        self.cb_dk = ctk.CTkComboBox(self.warrior_frame, values=WEAPON_DK_OPTIONS, width=280,
                                      fg_color="#1e2030", border_color="#2f334d",
                                      text_color="#c0caf5", corner_radius=6)
        self.cb_dk.set(WEAPON_DK_OPTIONS[1])
        self.cb_dk.pack(fill="x", padx=15, pady=(0, 12))

        # Кнопки
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(btn_frame, text="✖ СКАСУВАТИ",
                      fg_color="#2a2b3d", text_color="#a9b1d6",
                      font=ctk.CTkFont(family=FONT_MONO, size=12),
                      command=self.destroy).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="✔ СТВОРИТИ",
                      fg_color="#00f0ff", text_color="#000000",
                      font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
                      command=self._confirm).pack(side="right", expand=True, padx=(5, 0))

    def _row(self, container, text: str):
        ctk.CTkLabel(container, text=text,
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#787c99").pack(anchor="w", padx=15, pady=(8, 2))

    def _on_class_change(self, val):
        cls = self.cb_class.get() if val else CLASSES[0]
        if cls == "Мечник":
            self.warrior_frame.pack(fill="x", padx=20, pady=5)
        else:
            self.warrior_frame.pack_forget()

    def _confirm(self):
        name = self.ent_name.get().strip()
        if not name:
            from tkinter import messagebox
            messagebox.showwarning("Увага!", "Введіть ім'я персонажа!")
            return
        dk_str = self.cb_dk.get().split(" ")[0]  # "d6"
        dk_val = DK_MAP.get(dk_str, 6)
        self.on_confirm({
            "name": name,
            "race": self.cb_race.get(),
            "char_class": self.cb_class.get(),
            "weapon_name": self.ent_weapon.get().strip(),
            "weapon_dk": dk_val,
            "is_player": self.cb_type.get().startswith("★")
        })
        self.destroy()
