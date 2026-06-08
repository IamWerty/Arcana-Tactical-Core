"""
modules/magic_left_panel.py
"""
import customtkinter as ctk
from core.magic_engine import calculate
from ui.widgets import make_label, make_readonly_textbox, FONT_MONO

_ENTRY_KW = dict(fg_color="#1e2030", border_color="#2f334d",
                 text_color="#c0caf5", corner_radius=6)
_CB_KW    = dict(fg_color="#1e2030", border_color="#2f334d",
                 text_color="#c0caf5", corner_radius=6)


class MagicLeftPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, data_manager,
                 char_manager=None, on_save_callback=None):
        self.dm = data_manager
        self.cm = char_manager
        self.frame = parent_frame
        self._on_save = on_save_callback
        self.last_result = None
        self._build()

    def set_char_manager(self, cm):
        self.cm = cm

    # =========================================================================
    # Хелпери
    # =========================================================================
    @staticmethod
    def _make_combo(container, label_text, values, default=None, width=180):
        frame = ctk.CTkFrame(container, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=4)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)
        ctk.CTkLabel(frame, text=label_text,
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#787c99", anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 8))
        cb = ctk.CTkComboBox(frame, values=values, width=width, **_CB_KW)
        cb.set(default if default else values[0])
        cb.grid(row=0, column=1, sticky="e")
        return cb

    @staticmethod
    def _make_entry(container, label_text, default_val, width=180):
        frame = ctk.CTkFrame(container, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=4)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)
        ctk.CTkLabel(frame, text=label_text,
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#787c99", anchor="w").grid(row=0, column=0, sticky="w", padx=(0, 8))
        ent = ctk.CTkEntry(frame, width=width, **_ENTRY_KW)
        ent.insert(0, default_val)
        ent.grid(row=0, column=1, sticky="e")
        return ent

    # =========================================================================
    # BUILD
    # =========================================================================
    def _build(self):
        title_f = ctk.CTkFrame(self.frame, fg_color="transparent")
        title_f.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(title_f, text="01 // Калькулятор рун",
                     font=ctk.CTkFont(family=FONT_MONO, size=18, weight="bold"),
                     text_color="#00f0ff").pack(anchor="w")

        scroll = ctk.CTkScrollableFrame(self.frame, fg_color="#151724",
                                         corner_radius=8, height=430)
        scroll.pack(fill="x", padx=20, pady=5)

        make_label(scroll, "--- ГЕОМЕТРИЧНИЙ КОНТУР ---", "#ff007f")
        self.cb_size = self._make_combo(
            scroll, "Розмір руни (K_l):",
            ["До 10 см (K_l = 1.0)", "10-30 см (K_l = 1.2)",
             "30-100 см (K_l = 1.5)", "1-3 м (K_l = 2.0)"])
        self.cb_shape = self._make_combo(
            scroll, "Контур контроля (A_shape):",
            ["Проста / Аморфна = 5", "Середня / Гостра = 15",
             "Складна / Анатомічна = 40"])
        self.cb_vector = self._make_combo(
            scroll, "Канал потока (K_vector):",
            ["Напрям = 0.0", "Швидкість = 0.2", "Цикл = 0.5", "Повторення = 0.8"],
            default="Швидкість = 0.2")

        make_label(scroll, "--- МОДИФІКАТОРИ РЕЧОВИНИ ---", "#ff007f")
        self.cb_sm = self._make_combo(
            scroll, "Monolith (S_m):",
            ["0.5 (Вогонь, Газ, Кислота)", "1.0 (Камінь, Лід, Дерево)",
             "1.5 (Метал, Чиста Енергія)"],
            default="1.0 (Камінь, Лід, Дерево)")
        self.ent_km = self._make_entry(scroll, "Коеф. маси (K_m):", "1.0")
        self.ent_kq = self._make_entry(scroll, "Коеф. заряда (K_q):", "1.0")

        make_label(scroll, "--- СИСТЕМА ДАМАГУ ---", "#ff007f")
        self.ent_ndice = self._make_entry(scroll, "К-ть кубів (N_dice):", "3")
        self.cb_dk = self._make_combo(
            scroll, "Тип куба (dK):",
            ["d4", "d6", "d8", "d10", "d12"], default="d6")
        self.ent_arcs = self._make_entry(scroll, "Дуга прискорення (n):", "1")
        self.cb_dist = self._make_combo(
            scroll, "Дистанція:",
            ["В радіусі ефективної дальності", "За радіусом дальності"])

        # ── Прапорець "Чи рухається?" ──
        make_label(scroll, "--- РУХ СНАРЯДУ ---", "#ff007f")
        motion_f = ctk.CTkFrame(scroll, fg_color="#1a1c2e", corner_radius=6)
        motion_f.pack(fill="x", padx=10, pady=6)

        self._is_moving = ctk.BooleanVar(value=True)

        ctk.CTkCheckBox(
            motion_f,
            text="Снаряд рухається  (враховувати кінетичну Аркану)",
            variable=self._is_moving,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color="#c0caf5",
            fg_color="#00f0ff", hover_color="#00b8c4",
            checkmark_color="#000000",
            command=self.action_calculate   # одразу перераховуємо при зміні
        ).pack(anchor="w", padx=12, pady=8)

        self._lbl_motion_hint = ctk.CTkLabel(
            motion_f, text="",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color="#5f647d"
        )
        self._lbl_motion_hint.pack(anchor="w", padx=12, pady=(0, 6))

        # ── Кнопки ──
        btn_f = ctk.CTkFrame(self.frame, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(btn_f, text="ВИРАХУВАТИ",
                      font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
                      fg_color="#383a59", text_color="#ffffff",
                      command=self.action_calculate).pack(side="left", fill="x",
                                                          expand=True, padx=(0, 5))
        self.ent_save_name = ctk.CTkEntry(btn_f,
                                           placeholder_text="Ім'я шаблона...",
                                           font=ctk.CTkFont(family=FONT_MONO, size=12),
                                           width=140)
        self.ent_save_name.pack(side="left", padx=5)
        ctk.CTkButton(btn_f, text="ЗБЕРЕГТИ",
                      font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
                      fg_color="#ff007f", text_color="#ffffff", hover_color="#c90062",
                      command=self.action_save).pack(side="left", padx=(5, 0))

        # ── Вивід (readonly — виділення і копіювання дозволені) ──
        self.txt_output = make_readonly_textbox(
            self.frame, fg_color="#090a10",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color="#a9b1d6"
        )
        self.txt_output.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.txt_output.insert("1.0",
                                ">> МОДУЛЬ МАГІЇ СТАБІЛЬНИЙ.\n"
                                ">> Чекаємо ініціалізації вирахунку...")

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def _gather_params(self) -> dict:
        return {
            "size":      self.cb_size.get(),
            "shape":     self.cb_shape.get(),
            "vector":    self.cb_vector.get(),
            "sm":        self.cb_sm.get(),
            "km":        self.ent_km.get(),
            "kq":        self.ent_kq.get(),
            "ndice":     self.ent_ndice.get(),
            "dk":        self.cb_dk.get(),
            "arcs":      self.ent_arcs.get(),
            "is_far":    self.cb_dist.get() != "В радіусі ефективної дальності",
            "is_moving": self._is_moving.get(),
        }

    def action_calculate(self):
        params = self._gather_params()
        res = calculate(params)
        self.txt_output.delete("1.0", ctk.END)

        if res["success"]:
            self.last_result = res
            m        = res["m"]
            v        = res["v"]
            K_l      = res["K_l"]
            A_shape  = res["A_shape"]
            K_vector = res["K_vector"]
            K_m      = res["K_m"]
            K_q      = res["K_q"]
            n_arcs   = res["n_arcs"]
            is_moving = params["is_moving"]

            mass_part    = m * K_m * K_q
            shape_part   = A_shape
            kinetic_part = m * K_vector * v if is_moving else 0.0
            inner        = mass_part + shape_part + kinetic_part
            before_ceil  = K_l * inner

            # Підказка під чекбоксом
            if is_moving:
                self._lbl_motion_hint.configure(text="")
            else:
                self._lbl_motion_hint.configure(
                    text=f"  ⚠ Кінетична частина виключена  (−{m * K_vector * v:.1f} ед.)",
                    text_color="#ffaa00"
                )

            kinetic_line = (
                f"  [кінетика]        m×K_v×v    = {m}×{K_vector:.2f}×{v:.2f} = {m * K_vector * v:.3f}  ← ВИКЛЮЧЕНО\n"
                if not is_moving else
                f"  [кінетика]        m×K_v×v    = {m}×{K_vector:.2f}×{v:.2f} = {kinetic_part:.3f}\n"
            )

            log = (
                f">> МАТЕМАТИЧНА ІНІЦІАЛІЗАЦІЯ РУНИ:\n"
                f"==================================================\n"
                f"  ВХІДНІ КОЕФІЦІЄНТИ:\n"
                f"  K_l (розмір)    = {K_l}\n"
                f"  A_shape (форма) = {A_shape}\n"
                f"  K_vector        = {K_vector:.2f}  (1 + вектор)\n"
                f"  K_m (маса)      = {K_m}\n"
                f"  K_q (заряд)     = {K_q}\n"
                f"  Рух снаряду     = {'ТАК' if is_moving else 'НІ — кінетика = 0'}\n"
                f"--------------------------------------------------\n"
                f"  МАСА СНАРЯДУ:\n"
                f"  m = base_mass(N_dice) × DK_множник = {m} me\n"
                f"    ({m * 0.125:.4f} kg)\n"
                f"--------------------------------------------------\n"
                f"  ШВИДКІСТЬ:\n"
                f"  v = 10 + Σ(10/i, i=1..{n_arcs}) = {v:.2f} m/s\n"
                f"--------------------------------------------------\n"
                f"  ОБЧИСЛЕННЯ АРКАНИ:\n"
                f"  [маса-частина]    m×K_m×K_q  = {m}×{K_m}×{K_q} = {mass_part:.3f}\n"
                f"  [форма-частина]   A_shape    = {shape_part}\n"
                + kinetic_line +
                f"  ──────────────────────────────────────────\n"
                f"  сума             = {mass_part:.3f} + {shape_part} + {kinetic_part:.3f} = {inner:.3f}\n"
                f"  × K_l            = {inner:.3f} × {K_l} = {before_ceil:.3f}\n"
                f"  A_total = ⌈{before_ceil:.3f}⌉ = {res['A_total']} ed.\n"
                f"==================================================\n"
                f"  ДАМАГ:\n"
                f"  Формула : {res['game_formula']}\n"
                f"  Середній: {res['avg_damage']:.1f} HP"
            )
        else:
            self.last_result = None
            log = f">> ПОМИЛКА РОЗРАХУНКУ:\n{res['error']}"

        self.txt_output.insert("1.0", log)

    def action_save(self):
        from tkinter import messagebox
        name = self.ent_save_name.get().strip()
        if not name:
            messagebox.showwarning("Увага!", "Введіть ім'я руни!")
            return
        res = calculate(self._gather_params())
        if not res["success"]:
            return
        if self.cm:
            self.cm.add_spell(name, res)
        else:
            print(f"[MagicLeftPanel] WARNING: cm не прив'язаний, шаблон '{name}' втрачено!")
        self.ent_save_name.delete(0, ctk.END)
        if self._on_save:
            self._on_save()

    def load_template(self, data: dict):
        p = data["raw_params"]
        self.cb_size.set(p["size"])
        self.cb_shape.set(p["shape"])
        self.cb_vector.set(p["vector"])
        self.cb_sm.set(p["sm"])
        self.ent_km.delete(0, ctk.END);    self.ent_km.insert(0, str(p["km"]))
        self.ent_kq.delete(0, ctk.END);    self.ent_kq.insert(0, str(p["kq"]))
        self.ent_ndice.delete(0, ctk.END); self.ent_ndice.insert(0, str(p["ndice"]))
        self.cb_dk.set(p["dk"])
        self.ent_arcs.delete(0, ctk.END);  self.ent_arcs.insert(0, str(p["arcs"]))
        # Відновлюємо стан руху якщо збережено
        self._is_moving.set(p.get("is_moving", True))
        self.action_calculate()
