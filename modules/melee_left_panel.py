"""
modules/melee_left_panel.py
===========================
Ліва панель ФІЗИЧНОГО ДАМАГУ.
Пункт 2 ТЗ: вибір будь-якого персонажа (не тільки мечника).
Пункт 2 ТЗ: бонус береться від навички "Сприйняття" (а не Мудрості).
"""
import customtkinter as ctk
from core.melee_engine import calculate
from core.character_manager import CharacterManager
from ui.widgets import make_label, make_dropdown, make_readonly_textbox, FONT_MONO

ACCENT = "#00f0ff"
WARN   = "#ffaa00"


class MeleeLeftPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, data_manager, char_manager=None):
        self.dm = data_manager
        self.cm: CharacterManager | None = char_manager
        self.frame = parent_frame
        self.base_pool_limit = 10.0
        self.updating_sliders = False

        self._build()
        self.action_calculate()

    def set_char_manager(self, cm):
        self.cm = cm
        self._refresh_char_list()

    # =========================================================================
    def _build(self):
        title_f = ctk.CTkFrame(self.frame, fg_color="transparent")
        title_f.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(title_f, text="01 // КАЛЬКУЛЯТОР ФІЗИЧНОГО ДАМАГУ",
                     font=ctk.CTkFont(family=FONT_MONO, size=18, weight="bold"),
                     text_color=WARN).pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(self.frame, fg_color="#151724", corner_radius=8, height=430)
        scroll.pack(fill="x", padx=20, pady=5)

        # ── Вибір персонажа (будь-який) ──
        make_label(scroll, "--- ПЕРСОНАЖ (НЕОБОВ'ЯЗКОВО) ---", ACCENT)
        row_char = ctk.CTkFrame(scroll, fg_color="transparent")
        row_char.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(row_char, text="Персонаж:",
                     font=ctk.CTkFont(family=FONT_MONO, size=12), text_color="#787c99").pack(side="left")
        self.cb_char = ctk.CTkComboBox(row_char, values=["— вручну —"], width=210,
                                        fg_color="#1e2030", border_color="#2f334d",
                                        text_color="#c0caf5", corner_radius=6,
                                        command=self._on_char_select)
        self.cb_char.set("— вручну —")
        self.cb_char.pack(side="right")

        # Мод. Сили
        row_str = ctk.CTkFrame(scroll, fg_color="transparent")
        row_str.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(row_str, text="Мод. Сили (авто):",
                     font=ctk.CTkFont(family=FONT_MONO, size=12), text_color="#787c99").pack(side="left")
        self.ent_str_mod = ctk.CTkEntry(row_str, width=210, fg_color="#1e2030",
                                         border_color="#2f334d", text_color=WARN,
                                         corner_radius=6, font=ctk.CTkFont(weight="bold"))
        self.ent_str_mod.insert(0, "0")
        self.ent_str_mod.pack(side="right")
        self.ent_str_mod.bind("<KeyRelease>", lambda e: self.action_calculate())

        # Бонус Сприйняття (пункт 2 ТЗ — замість Мудрості)
        row_per = ctk.CTkFrame(scroll, fg_color="transparent")
        row_per.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(row_per, text="Сприйняття (авто):",
                     font=ctk.CTkFont(family=FONT_MONO, size=12), text_color="#787c99").pack(side="left")
        self.ent_perception = ctk.CTkEntry(row_per, width=210, fg_color="#1e2030",
                                            border_color="#2f334d", text_color="#a855f7",
                                            corner_radius=6, font=ctk.CTkFont(weight="bold"))
        self.ent_perception.insert(0, "0")
        self.ent_perception.pack(side="right")
        self.ent_perception.bind("<KeyRelease>", lambda e: self.action_calculate())

        # ── Ліміт пулу ──
        make_label(scroll, "--- РОЗВИТОК ФІЗИЧНИХ КЛАСІВ ---", ACCENT)
        frame_pool = ctk.CTkFrame(scroll, fg_color="transparent")
        frame_pool.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_pool, text="Загальний ліміт пулів:",
                     font=ctk.CTkFont(family=FONT_MONO, size=12), text_color="#787c99").pack(side="left")
        self.ent_pool = ctk.CTkEntry(frame_pool, width=210, fg_color="#1e2030",
                                      border_color=ACCENT, text_color=ACCENT,
                                      corner_radius=6, font=ctk.CTkFont(weight="bold"))
        self.ent_pool.insert(0, "10.0")
        self.ent_pool.pack(side="right")
        self.ent_pool.bind("<KeyRelease>", lambda e: self._update_pool_limit())

        # ── Параметри зброї ──
        make_label(scroll, "--- ПАРАМЕТРИ ЗБРОЇ ---", WARN)
        frame_dk = ctk.CTkFrame(scroll, fg_color="transparent")
        frame_dk.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_dk, text="Власний dK зброї:",
                     font=ctk.CTkFont(family=FONT_MONO, size=12), text_color="#787c99").pack(side="left")
        self.ent_dk = ctk.CTkEntry(frame_dk, width=210, fg_color="#1e2030",
                                    border_color="#2f334d", text_color="#c0caf5", corner_radius=6)
        self.ent_dk.insert(0, "6")
        self.ent_dk.pack(side="right")
        self.ent_dk.bind("<KeyRelease>", lambda e: self.action_calculate())

        self.lbl_weapon_name = ctk.CTkLabel(scroll, text="",
                                             font=ctk.CTkFont(family=FONT_MONO, size=10),
                                             text_color="#5f647d")
        self.lbl_weapon_name.pack(anchor="w", padx=10)

        self.cb_weapon = make_dropdown(scroll, "Клас використовуваної зброї:",
                                       ["Колюча (Шпага, Рапіра, Ніж)",
                                        "Рубяща (Меч, Сокира)",
                                        "Дробяща (Молот, Дворучник)"])
        self.cb_weapon.configure(command=lambda v: self.action_calculate())

        # ── Слайдери ──
        self.lbl_pool_title = make_label(
            scroll, "--- КЕРУВАННЯ ІМПУЛЬСОМ ТІЛА (СУМА = 10.0) ---", "#ff007f")

        self.lbl_a, self.slider_a = self._make_slider(scroll, "Амплітуда замаху (А)", "#ff007f", 3.33, self._on_a)
        self.lbl_v, self.slider_v = self._make_slider(scroll, "Швидкість удару (V)", ACCENT,   3.33, self._on_v)
        self.lbl_w, self.slider_w = self._make_slider(scroll, "Важкість стійки (W)", WARN,     3.34, self._on_w)

        # ── Вивід ──
        self.txt_output = make_readonly_textbox(
            self.frame, fg_color="#090a10",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color="#a9b1d6"
        )
        self.txt_output.pack(fill="both", expand=True, padx=20, pady=(15, 20))

    @staticmethod
    def _make_slider(container, label: str, color: str, default: float, command):
        frame = ctk.CTkFrame(container, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=8)
        lbl = ctk.CTkLabel(frame, text=f"{label}: {default:.1f}",
                            font=ctk.CTkFont(family=FONT_MONO, size=12), text_color=color,
                            width=190, anchor="w")
        lbl.pack(side="left")
        slider = ctk.CTkSlider(frame, from_=0, to=10, number_of_steps=100,
                                fg_color="#1e2030", progress_color=color, command=command)
        slider.set(default)
        slider.pack(side="right", fill="x", expand=True)
        return lbl, slider

    # ── Character select ──
    def _on_char_select(self, val):
        self.lbl_weapon_name.configure(text="")
        if not self.cm or val == "— вручну —":
            return
        char = self.cm.get_by_name(val)
        if not char:
            return

        # Мод. Сили через нову систему характеристик
        str_total = self.cm.modifier(char, "Сила")
        self.ent_str_mod.delete(0, ctk.END)
        self.ent_str_mod.insert(0, str(str_total))

        # Сприйняття (пункт 2 ТЗ)
        perception = self.cm.skill_total(char, "Сприйняття")
        self.ent_perception.delete(0, ctk.END)
        self.ent_perception.insert(0, str(perception))

        # Зброя — є у всіх персонажів тепер
        dk = char.get("weapon_dk", 6)
        self.ent_dk.delete(0, ctk.END)
        self.ent_dk.insert(0, str(dk))
        wname = char.get("weapon_name", "")
        if wname:
            self.lbl_weapon_name.configure(text=f"// Зброя: {wname}")

        # Ліміт пулів
        pool = char.get("pool_limit", 10.0)
        self.ent_pool.delete(0, ctk.END)
        self.ent_pool.insert(0, str(pool))
        self._update_pool_limit()
        self.action_calculate()

    def _refresh_char_list(self):
        if not self.cm:
            return
        # Пункт 2 ТЗ: всі персонажі, не тільки мечники
        all_names = ["— вручну —"] + [c["name"] for c in self.cm.get_sorted()]
        current = self.cb_char.get()
        self.cb_char.configure(values=all_names)
        if current not in all_names:
            self.cb_char.set("— вручну —")

    # ── Pool ──
    def _update_pool_limit(self):
        try:
            new_limit = float(self.ent_pool.get().strip())
            if new_limit <= 0:
                return
            self.base_pool_limit = new_limit
            self.lbl_pool_title.configure(
                text=f"--- КЕРУВАННЯ ІМПУЛЬСОМ ТІЛА (СУМА = {new_limit:.1f}) ---")
            for s in [self.slider_a, self.slider_v, self.slider_w]:
                s.configure(to=new_limit)
            total = self.slider_a.get() + self.slider_v.get() + self.slider_w.get()
            if total > 0:
                self.updating_sliders = True
                self.slider_a.set(self.slider_a.get() / total * new_limit)
                self.slider_v.set(self.slider_v.get() / total * new_limit)
                self.slider_w.set(self.slider_w.get() / total * new_limit)
                self.updating_sliders = False
            self.action_calculate()
        except ValueError:
            pass

    def _redistribute(self, fixed_val, s1, s2):
        rem = self.base_pool_limit - fixed_val
        v1, v2 = s1.get(), s2.get()
        total = v1 + v2
        if total > 0:
            s1.set(max(0, min(self.base_pool_limit, v1 / total * rem)))
            s2.set(max(0, min(self.base_pool_limit, v2 / total * rem)))
        else:
            s1.set(rem / 2)
            s2.set(rem / 2)

    def _on_a(self, val):
        if self.updating_sliders: return
        self.updating_sliders = True
        self._redistribute(float(val), self.slider_v, self.slider_w)
        self.updating_sliders = False
        self.action_calculate()

    def _on_v(self, val):
        if self.updating_sliders: return
        self.updating_sliders = True
        self._redistribute(float(val), self.slider_a, self.slider_w)
        self.updating_sliders = False
        self.action_calculate()

    def _on_w(self, val):
        if self.updating_sliders: return
        self.updating_sliders = True
        self._redistribute(float(val), self.slider_a, self.slider_v)
        self.updating_sliders = False
        self.action_calculate()

    # =========================================================================
    def action_calculate(self):
        A = self.slider_a.get()
        V = self.slider_v.get()
        W = self.slider_w.get()
        self.lbl_a.configure(text=f"Амплітуда замаху (А): {A:.1f}")
        self.lbl_v.configure(text=f"Швидкість удару (V): {V:.1f}")
        self.lbl_w.configure(text=f"Важкість стійки (W): {W:.1f}")

        try:
            raw = self.ent_str_mod.get().strip().lstrip("+")
            str_mod = int(raw) if raw.lstrip("-").isdigit() else 0
        except Exception:
            str_mod = 0

        try:
            raw_p = self.ent_perception.get().strip().lstrip("+")
            perception = int(raw_p) if raw_p.lstrip("-").isdigit() else 0
        except Exception:
            perception = 0

        try:
            dk_str = self.ent_dk.get().strip()
            dk_sides = int(dk_str) if dk_str.isdigit() and int(dk_str) > 0 else 8
            weapon_type = self.cb_weapon.get()
            res = calculate(A, V, W, dk_sides, weapon_type, self.base_pool_limit)
            pA, pV, pW = res["percentages"]

            # flat_bonus + Сила + Сприйняття (пункт 2 ТЗ)
            total_flat = res["flat_bonus"] + str_mod + perception
            game_formula_str = f"{res['total_cubes']}d{dk_sides} + {total_flat}"
            avg = (res["total_cubes"] * (1 + dk_sides) / 2) + total_flat

            log = (
                f">> БІОМЕХАНІЧНИЙ РОЗРАХУНОК ФІЗИЧНОЇ АТАКИ:\n"
                f"--------------------------------------------------\n"
                f"• Клас зброї                 : {res['weapon_short']}\n"
                f"• Ліміт пулу                 : {self.base_pool_limit:.1f}\n"
                f"• Потенціал реалізації        : макс. {res['max_possible_cubes']}\n"
                f"• Розподіл: A={pA:.0f}% | V={pV:.0f}% | W={pW:.0f}%\n"
                f"--------------------------------------------------\n"
                f"• {res['modifier_name']}\n"
                f"• Мод. Сили                  : {str_mod:+}\n"
                f"• Сприйняття                 : {perception:+}\n"
                f"• Модифікатор захисту (КБ)   : +{res['ac_bonus']}\n"
                f"--------------------------------------------------\n"
                f"• ФОРМУЛА : {game_formula_str}\n"
                f"• Середній дамаг             : {avg:.1f} HP\n"
                f"--------------------------------------------------\n"
                + "\n".join(res["special_effects"])
            )
        except Exception as e:
            log = f">> ПОМИЛКА:\n{e}"

        self.txt_output.delete("1.0", ctk.END)
        self.txt_output.insert("1.0", log)
