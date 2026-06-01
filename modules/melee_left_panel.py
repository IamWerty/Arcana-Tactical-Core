"""
modules/melee_left_panel.py
===========================
Ліва панель для режиму ФІЗИЧНИЙ ДАМАГ.
Слайдери A/V/W, тип зброї, вивід результату.
"""
import customtkinter as ctk
from core.melee_engine import calculate
from ui.widgets import make_label, make_dropdown, FONT_MONO


class MeleeLeftPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, data_manager):
        self.dm = data_manager
        self.frame = parent_frame
        self.base_pool_limit = 10.0
        self.updating_sliders = False

        self._build()
        self.action_calculate()

    # =========================================================================
    # BUILD
    # =========================================================================
    def _build(self):
        title_f = ctk.CTkFrame(self.frame, fg_color="transparent")
        title_f.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(title_f, text="01 // КАЛЬКУЛЯТОР ФІЗИЧНОГО ДАМАГУ",
                     font=ctk.CTkFont(family=FONT_MONO, size=18, weight="bold"),
                     text_color="#ffaa00").pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(self.frame, fg_color="#151724", corner_radius=8, height=430)
        scroll.pack(fill="x", padx=20, pady=5)

        # Ліміт пулу
        make_label(scroll, "--- РОЗВИТОК ФІЗИЧНИХ КЛАСІВ ---", "#00f0ff")
        frame_pool = ctk.CTkFrame(scroll, fg_color="transparent")
        frame_pool.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_pool, text="Загальний ліміт пулів:",
                     font=ctk.CTkFont(family=FONT_MONO, size=12), text_color="#787c99").pack(side="left")
        self.ent_pool = ctk.CTkEntry(frame_pool, width=210, fg_color="#1e2030",
                                      border_color="#00f0ff", text_color="#00f0ff",
                                      corner_radius=6, font=ctk.CTkFont(weight="bold"))
        self.ent_pool.insert(0, "10.0")
        self.ent_pool.pack(side="right")
        self.ent_pool.bind("<KeyRelease>", lambda e: self._update_pool_limit())

        # Параметри зброї
        make_label(scroll, "--- ПАРАМЕТРИ ЗБРОЇ ---", "#ffaa00")
        frame_dk = ctk.CTkFrame(scroll, fg_color="transparent")
        frame_dk.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_dk, text="Власний dK зброї:",
                     font=ctk.CTkFont(family=FONT_MONO, size=12), text_color="#787c99").pack(side="left")
        self.ent_dk = ctk.CTkEntry(frame_dk, width=210, fg_color="#1e2030",
                                    border_color="#2f334d", text_color="#c0caf5", corner_radius=6)
        self.ent_dk.insert(0, "6")
        self.ent_dk.pack(side="right")
        self.ent_dk.bind("<KeyRelease>", lambda e: self.action_calculate())

        self.cb_weapon = make_dropdown(scroll, "Клас використовуваної зброї:",
                                       ["Колюча (Шпага, Рапіра, Ніж)",
                                        "Рубяща (Меч, Сокира)",
                                        "Дробяща (Молот, Дворучник)"])
        self.cb_weapon.configure(command=lambda v: self.action_calculate())

        # Слайдери
        self.lbl_pool_title = make_label(
            scroll, "--- КЕРУВАННЯ ІМПУЛЬСОМ ТІЛА (СУМА СТРОГО = 10.0) ---", "#ff007f")

        self.lbl_a, self.slider_a = self._make_slider(scroll, "Амплітуда замаху (А)", "#ff007f", 3.33, self._on_a)
        self.lbl_v, self.slider_v = self._make_slider(scroll, "Швидкість удару (V)", "#00f0ff", 3.33, self._on_v)
        self.lbl_w, self.slider_w = self._make_slider(scroll, "Важкість стійки (W)", "#ffaa00", 3.34, self._on_w)

        # Вивід
        self.txt_output = ctk.CTkTextbox(self.frame, fg_color="#090a10",
                                          font=ctk.CTkFont(family=FONT_MONO, size=11),
                                          text_color="#a9b1d6")
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

    # =========================================================================
    # SLIDER LOGIC
    # =========================================================================
    def _update_pool_limit(self):
        try:
            new_limit = float(self.ent_pool.get().strip())
            if new_limit <= 0:
                return
            self.base_pool_limit = new_limit
            self.lbl_pool_title.configure(
                text=f"--- КЕРУВАННЯ ІМПУЛЬСОМ ТІЛА (СУМА СТРОГО = {new_limit:.1f}) ---")
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

    def _redistribute(self, fixed_val: float, s1: ctk.CTkSlider, s2: ctk.CTkSlider):
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
    # CALCULATE
    # =========================================================================
    def action_calculate(self):
        A = self.slider_a.get()
        V = self.slider_v.get()
        W = self.slider_w.get()
        self.lbl_a.configure(text=f"Амплітуда замаху (А): {A:.1f}")
        self.lbl_v.configure(text=f"Швидкість удару (V): {V:.1f}")
        self.lbl_w.configure(text=f"Важкість стійки (W): {W:.1f}")

        try:
            dk_str = self.ent_dk.get().strip()
            dk_sides = int(dk_str) if dk_str.isdigit() and int(dk_str) > 0 else 8
            weapon_type = self.cb_weapon.get()
            res = calculate(A, V, W, dk_sides, weapon_type, self.base_pool_limit)
            pA, pV, pW = res["percentages"]

            log = (
                f">> БІОМЕХАНІЧНИЙ РОЗРАХУНОК ФІЗИЧНОЇ АТАКИ:\n"
                f"--------------------------------------------------\n"
                f"• Клас зброї                 : {res['weapon_short']}\n"
                f"• Загальний ліміт пулу тіла  : {self.base_pool_limit:.1f}\n"
                f"• Потенціал реалізації замаху: макс. {res['max_possible_cubes']}\n"
                f"• Розподіл енергії тіла      : A={pA:.0f}% | V={pV:.0f}% | W={pW:.0f}%\n"
                f"--------------------------------------------------\n"
                f"• {res['modifier_name']}\n"
                f"• Модифікатор захисту (КБ)   : +{res['ac_bonus']}\n"
                f"--------------------------------------------------\n"
                f"• ФОРМУЛА ДЛЯ КИДКА НА СТОЛІ : {res['game_formula']}\n"
                f"• Очікуваний середній дамаг  : {res['avg_damage']:.1f} HP\n"
                f"--------------------------------------------------\n"
                + "\n".join(res["special_effects"])
            )
        except Exception as e:
            log = f">> ПОМИЛКА ІНЖЕНЕРІЇ ТІЛА:\n{e}"

        self.txt_output.configure(state="normal")
        self.txt_output.delete("1.0", ctk.END)
        self.txt_output.insert("1.0", log)
        self.txt_output.configure(state="disabled")
