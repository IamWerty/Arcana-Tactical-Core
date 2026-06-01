"""
modules/magic_left_panel.py
===========================
Ліва панель для режиму МАГІЧНИЙ ДАМАГ.
Калькулятор рун: форма введення + кнопки вирахувати/зберегти + текстовий вивід.
"""
import customtkinter as ctk
from core.magic_engine import calculate
from ui.widgets import make_label, make_dropdown, make_input, FONT_MONO


class MagicLeftPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, data_manager, on_save_callback=None):
        self.dm = data_manager
        self.frame = parent_frame
        self._on_save = on_save_callback  # викликається після збереження шаблона
        self.last_result = None

        self._build()

    # =========================================================================
    # BUILD
    # =========================================================================
    def _build(self):
        title_f = ctk.CTkFrame(self.frame, fg_color="transparent")
        title_f.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(title_f, text="01 // Калькулятор рун",
                     font=ctk.CTkFont(family=FONT_MONO, size=18, weight="bold"),
                     text_color="#00f0ff").pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(self.frame, fg_color="#151724", corner_radius=8, height=430)
        scroll.pack(fill="x", padx=20, pady=5)

        make_label(scroll, "--- ГЕОМЕТРИЧНИЙ КОНТУР ---", "#ff007f")
        self.cb_size = make_dropdown(scroll, "Розмір руни (K_l):",
                                     ["До 10 см (K_l = 1.0)", "10-30 см (K_l = 1.2)",
                                      "30-100 см (K_l = 1.5)", "1-3 м (K_l = 2.0)"])
        self.cb_shape = make_dropdown(scroll, "Контур контроля (A_shape):",
                                      ["Проста / Аморфна = 5", "Середня / Гостра = 15",
                                       "Складна / Анатомічна = 40"])
        self.cb_vector = make_dropdown(scroll, "Канал потока (K_vector):",
                                       ["Напрям = 0.0", "Швидкість = 0.2", "Цикл = 0.5", "Повторення = 0.8"])
        self.cb_vector.set("Швидкість = 0.2")

        make_label(scroll, "--- МОДИФІКАТОРИ РЕЧОВИНИ ---", "#ff007f")
        self.cb_sm = make_dropdown(scroll, "Monolith (S_m):",
                                   ["0.5 (Вогонь, Газ, Кислота)", "1.0 (Камінь, Лід, Дерево)",
                                    "1.5 (Метал, Чиста Енергія)"])
        self.ent_km = make_input(scroll, "Коеф. маси (K_m):", "1.0")
        self.ent_kq = make_input(scroll, "Коеф. заряда (K_q):", "1.0")

        make_label(scroll, "--- СИСТЕМА ДАМАГУ ---", "#ff007f")
        self.ent_ndice = make_input(scroll, "К-ть кубів (N_dice):", "3")
        self.cb_dk = make_dropdown(scroll, "Тип куба (dK):", ["d4", "d6", "d8", "d10", "d12"])
        self.cb_dk.set("d6")
        self.ent_arcs = make_input(scroll, "Дуга прискорення (n):", "1")
        self.cb_dist = make_dropdown(scroll, "Дистанція:",
                                     ["В радіусі ефективної дальності", "За радіусом дальності"])

        # Кнопки
        btn_f = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_f, text="ВИРАХУВАТИ",
                      font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
                      fg_color="#383a59", text_color="#ffffff",
                      command=self.action_calculate).pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.ent_save_name = ctk.CTkEntry(btn_f, placeholder_text="Ім'я шаблона...",
                                           font=ctk.CTkFont(family=FONT_MONO, size=12), width=140)
        self.ent_save_name.pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="ЗБЕРЕГТИ",
                      font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
                      fg_color="#ff007f", text_color="#ffffff", hover_color="#c90062",
                      command=self.action_save).pack(side="left", padx=(5, 0))

        # Вивід
        self.txt_output = ctk.CTkTextbox(self.frame, fg_color="#090a10",
                                          font=ctk.CTkFont(family=FONT_MONO, size=11),
                                          text_color="#a9b1d6")
        self.txt_output.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.txt_output.insert("1.0", ">> МОДУЛЬ МАГІЇ СТАБІЛЬНИЙ.\n>> Чекаємо ініціалізації вирахунку...")
        self.txt_output.configure(state="disabled")

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def _gather_params(self) -> dict:
        return {
            "size": self.cb_size.get(),
            "shape": self.cb_shape.get(),
            "vector": self.cb_vector.get(),
            "sm": self.cb_sm.get(),
            "km": self.ent_km.get(),
            "kq": self.ent_kq.get(),
            "ndice": self.ent_ndice.get(),
            "dk": self.cb_dk.get(),
            "arcs": self.ent_arcs.get(),
            "is_far": self.cb_dist.get() != "В радіусі ефективної дальності"
        }

    def action_calculate(self):
        res = calculate(self._gather_params())
        self.txt_output.configure(state="normal")
        self.txt_output.delete("1.0", ctk.END)

        if res["success"]:
            self.last_result = res
            log = (
                f">> МАТЕМАТИЧНА ІНІЦІАЛІЗАЦІЯ РУНИ:\n"
                f"--------------------------------------------------\n"
                f"• Аркана для створення     : {res['A_total']} ed.\n"
                f"• Маса снаряду (m)         : {res['m']} me ({res['m']*0.125:.3f} kg)\n"
                f"• Швидкість випускання (v) : {res['v']:.2f} m/s\n"
                f"--------------------------------------------------\n"
                f"• Дамаг спела   : {res['game_formula']}\n"
                f"• Середній дамаг: {res['avg_damage']:.1f} HP"
            )
        else:
            self.last_result = None
            log = f">> ПОМИЛКА РОЗРАХУНКУ:\n{res['error']}"

        self.txt_output.insert("1.0", log)
        self.txt_output.configure(state="disabled")

    def action_save(self):
        from tkinter import messagebox
        name = self.ent_save_name.get().strip()
        if not name:
            messagebox.showwarning("Увага!", "Введіть ім'я руни!")
            return
        res = calculate(self._gather_params())
        if not res["success"]:
            return
        self.dm.saved_spells[name] = res
        self.dm.save_to_json()
        self.ent_save_name.delete(0, ctk.END)
        if self._on_save:
            self._on_save()

    def load_template(self, data: dict):
        """Завантажує параметри з шаблона у поля форми."""
        p = data["raw_params"]
        self.cb_size.set(p["size"])
        self.cb_shape.set(p["shape"])
        self.cb_vector.set(p["vector"])
        self.cb_sm.set(p["sm"])
        self.ent_km.delete(0, ctk.END); self.ent_km.insert(0, str(p["km"]))
        self.ent_kq.delete(0, ctk.END); self.ent_kq.insert(0, str(p["kq"]))
        self.ent_ndice.delete(0, ctk.END); self.ent_ndice.insert(0, str(p["ndice"]))
        self.cb_dk.set(p["dk"])
        self.ent_arcs.delete(0, ctk.END); self.ent_arcs.insert(0, str(p["arcs"]))
        self.action_calculate()
