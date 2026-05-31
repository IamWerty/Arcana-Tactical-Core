import customtkinter as ctk
import math
import json
import os
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SAVE_FILE = os.path.join(os.path.expanduser("~"), ".arcana_battle_save.json")

class ArcanaTacticalCore(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ARCANE TACTICAL CORE v2.3.0")
        self.geometry("1300x850")
        self.minsize(1150, 750) 
        self.configure(fg_color="#0d0e15")

        # Внутрішні структури даних сесії
        self.batteries = {
            "Мала сура (Альфа)": {"max": 250, "current": 250},
            "Сувій Ліори (Резерв)": {"max": 1000, "current": 1000}
        }
        self.saved_spells = {}  
        self.active_spells = [] 

        self.last_calculated_data = None 

        # Базове значення пулу для фізичного дамагу (може динамічно змінюватися гравцем)
        self.base_pool_limit = 10.0

        # Прапорці для блокування рекурсії повзунків V, A, W
        self.updating_sliders = False

        # Автоматичне завантаження збереженої сесії
        self.load_from_json()
        
        self.setup_ui()

    # =====================================================================
    # СИСТЕМА JSON SAVE/LOAD
    # =====================================================================
    def save_to_json(self):
        data_to_save = {
            "batteries": self.batteries,
            "saved_spells": self.saved_spells,
            "active_spells": self.active_spells
        }
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        except PermissionError:
            print(f"Помилка: Немає доступу до файлу {SAVE_FILE}.")
        except Exception as e:
            print(f"Помилка автозбереження JSON: {e}")

    def load_from_json(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    self.batteries = loaded_data.get("batteries", self.batteries)
                    self.saved_spells = loaded_data.get("saved_spells", self.saved_spells)
                    self.active_spells = loaded_data.get("active_spells", self.active_spells)
            except Exception as e:
                print(f"Помилка завантаження JSON: {e}")

    # =====================================================================
    # АДАПТИВНИЙ UI
    # =====================================================================
    def setup_ui(self):
        # Головна глобальна сітка: [ Aside Панель Навігації (0) ] | [ Робоча Зона Контенту (1) ]
        self.grid_columnconfigure(0, weight=1, minsize=180)
        self.grid_columnconfigure(1, weight=9)
        self.grid_rowconfigure(0, weight=1)

        # ---------------------------------------------------------------------
        # ASIDE ПАНЕЛЬ НАВІГАЦІЇ
        # ---------------------------------------------------------------------
        aside_panel = ctk.CTkFrame(self, fg_color="#090a0f", corner_radius=0, border_width=1, border_color="#1a1c2e")
        aside_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        ctk.CTkLabel(aside_panel, text="CORE MODE", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color="#5f647d").pack(pady=(20, 15), padx=10, anchor="w")

        self.btn_mode_magic = ctk.CTkButton(
            aside_panel, text="🔮 Магічний дамаг", font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            fg_color="#1a1c2e", text_color="#00f0ff", height=40, corner_radius=4, anchor="w",
            command=lambda: self.switch_mode("magic")
        )
        self.btn_mode_magic.pack(fill="x", padx=10, pady=5)

        self.btn_mode_melee = ctk.CTkButton(
            aside_panel, text="⚔️ Фізичний дамаг", font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            fg_color="transparent", text_color="#a9b1d6", height=40, corner_radius=4, anchor="w",
            command=lambda: self.switch_mode("melee")
        )
        self.btn_mode_melee.pack(fill="x", padx=10, pady=5)

        # ---------------------------------------------------------------------
        # ОСНОВНА РОБОЧА ЗОНА
        # ---------------------------------------------------------------------
        self.main_content_area = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main_content_area.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.main_content_area.grid_columnconfigure(0, weight=5, uniform="group1")
        self.main_content_area.grid_columnconfigure(1, weight=6, uniform="group1")
        self.main_content_area.grid_rowconfigure(0, weight=1)

        # КОНТЕЙНЕРИ ДЛЯ ВЕНТИЛЯЦІЇ РЕЖИМІВ (ЛІВА ЧАСТИНА)
        self.magic_constructor_frame = ctk.CTkFrame(self.main_content_area, fg_color="#11121c", corner_radius=0)
        self.melee_constructor_frame = ctk.CTkFrame(self.main_content_area, fg_color="#11121c", corner_radius=0)

        # ПРАВА ПАНЕЛЬ (БОЙОВОЙ ДИСПЕТЧЕР — СПІЛЬНИЙ ДЛЯ ОБОХ РЕЖИМІВ)
        right_panel = ctk.CTkFrame(self.main_content_area, fg_color="#141624", corner_radius=0)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.main_right_scroll = ctk.CTkScrollableFrame(right_panel, fg_color="transparent", corner_radius=0)
        self.main_right_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Ініціалізація підсистем UI
        self.setup_magic_ui()
        self.setup_melee_ui()
        self.setup_right_dispatcher_ui()

        # Дефолтний режим під час запуску
        self.switch_mode("magic")

    # =====================================================================
    # РЕЖИМ 1: МАГІЧНИЙ КОНСТРУКТОР
    # =====================================================================
    def setup_magic_ui(self):
        title_frame = ctk.CTkFrame(self.magic_constructor_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(title_frame, text="01 // Калькулятор рун", font=ctk.CTkFont(family="Consolas", size=18, weight="bold"), text_color="#00f0ff").pack(anchor="w")
        
        calc_scroll = ctk.CTkScrollableFrame(self.magic_constructor_frame, fg_color="#151724", corner_radius=8, height=430)
        calc_scroll.pack(fill="x", padx=20, pady=5)

        self.create_label(calc_scroll, "--- ГЕОМЕТРИЧЕСКИЙ КОНТУР ---", "#ff007f")
        self.cb_size = self.create_dropdown(calc_scroll, "Розмір руни (K_l):", ["До 10 см (K_l = 1.0)", "10-30 см (K_l = 1.2)", "30-100 см (K_l = 1.5)", "1-3 м (K_l = 2.0)"])
        self.cb_shape = self.create_dropdown(calc_scroll, "Контур контроля (A_shape):", ["Проста / Аморфна = 5", "Середня / Гостра = 15", "Складна / Анатомічна = 40"])
        self.cb_vector = self.create_dropdown(calc_scroll, "Канал потока (K_vector):", ["Напрям = 0.0", "Швидкість = 0.2", "Цикл = 0.5", "Повторення = 0.8"])
        self.cb_vector.set("Швидкість = 0.2")

        self.create_label(calc_scroll, "--- МОДИФИКАТОРИ РЕЧОВИНИ ---", "#ff007f")
        self.cb_sm = self.create_dropdown(calc_scroll, "Monolith (S_m):", ["0.5 (Вогонь, Газ, Кислота)", "1.0 (Камінь, Лід, Дерево)", "1.5 (Метал, Чиста Енергія)"])
        self.ent_km = self.create_input(calc_scroll, "Коеф. маси (K_m):", "1.0")
        self.ent_kq = self.create_input(calc_scroll, "Коеф. заряда (K_q):", "1.0")

        self.create_label(calc_scroll, "--- СИСТЕМА ДАМАГА ---", "#ff007f")
        self.ent_ndice = self.create_input(calc_scroll, "К-ть кубів (N_dice):", "3")
        self.cb_dk = self.create_dropdown(calc_scroll, "Тип куба (dK):", ["d4", "d6", "d8", "d10", "d12"])
        self.cb_dk.set("d6")
        self.ent_arcs = self.create_input(calc_scroll, "Дуга прискорення (n):", "1")
        self.cb_dist = self.create_dropdown(calc_scroll, "Дистанция:", ["В радіусі ефективної дальности", "За радіусом дальності"])

        btn_frame = ctk.CTkFrame(self.magic_constructor_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.btn_calc = ctk.CTkButton(btn_frame, text="ВИРАХУВАТИ", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), fg_color="#383a59", text_color="#ffffff", command=self.action_calculate)
        self.btn_calc.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.ent_save_name = ctk.CTkEntry(btn_frame, placeholder_text="Ім'я шаблона...", font=ctk.CTkFont(family="Consolas", size=12), width=140)
        self.ent_save_name.pack(side="left", padx=5)

        self.btn_save = ctk.CTkButton(btn_frame, text="ЗБЕРЕГТИ", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), fg_color="#ff007f", text_color="#ffffff", hover_color="#c90062", command=self.action_save_template)
        self.btn_save.pack(side="left", padx=(5, 0))

        self.txt_calc_output = ctk.CTkTextbox(self.magic_constructor_frame, fg_color="#090a10", font=ctk.CTkFont(family="Consolas", size=11), text_color="#a9b1d6")
        self.txt_calc_output.pack(fill="both", expand=True, padx=20, pady=(5, 20))
        self.txt_calc_output.insert("1.0", ">> МОДУЛЬ МАГІЇ СТАБІЛЬНИЙ.\n>> ЧЕКАЄМО ІНІЦІАЛІЗАЦІЇ ВИРАХУНКУ...")
        self.txt_calc_output.configure(state="disabled")

    # =====================================================================
    # РЕЖИМ 2: БІОМЕХАНІЧНИЙ ФІЗИЧНИЙ КАЛЬКУЛЯТОР
    # =====================================================================
    def setup_melee_ui(self):
        title_frame = ctk.CTkFrame(self.melee_constructor_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(title_frame, text="01 // КАЛЬКУЛЯТОР ФІЗИЧНОГО ДАМАГУ", font=ctk.CTkFont(family="Consolas", size=18, weight="bold"), text_color="#ffaa00").pack(anchor="w")

        melee_scroll = ctk.CTkScrollableFrame(self.melee_constructor_frame, fg_color="#151724", corner_radius=8, height=430)
        melee_scroll.pack(fill="x", padx=20, pady=5)

        # Налаштування пулу прокачки
        self.create_label(melee_scroll, "--- РОЗВИТОК ФІЗИЧНИХ КЛАСІВ ---", "#00f0ff")
        frame_pool = ctk.CTkFrame(melee_scroll, fg_color="transparent")
        frame_pool.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_pool, text="Загальний ліміт пулів:", font=ctk.CTkFont(family="Consolas", size=12), text_color="#787c99").pack(side="left")
        self.ent_melee_pool = ctk.CTkEntry(frame_pool, width=210, fg_color="#1e2030", border_color="#00f0ff", text_color="#00f0ff", corner_radius=6, font=ctk.CTkFont(weight="bold"))
        self.ent_melee_pool.insert(0, "10.0")
        self.ent_melee_pool.pack(side="right")
        self.ent_melee_pool.bind("<KeyRelease>", lambda e: self.action_update_pool_limit())

        # Налаштування характеристик зброї
        self.create_label(melee_scroll, "--- ПАРАМЕТРИ ЗБРОЇ ---", "#ffaa00")
        
        frame_dk = ctk.CTkFrame(melee_scroll, fg_color="transparent")
        frame_dk.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(frame_dk, text="Власний dK зброї:", font=ctk.CTkFont(family="Consolas", size=12), text_color="#787c99").pack(side="left")
        self.ent_melee_dk = ctk.CTkEntry(frame_dk, width=210, fg_color="#1e2030", border_color="#2f334d", text_color="#c0caf5", corner_radius=6)
        self.ent_melee_dk.insert(0, "6") # Стандарт d6
        self.ent_melee_dk.pack(side="right")
        self.ent_melee_dk.bind("<KeyRelease>", lambda e: self.action_calculate_melee())

        # Оновлений вибір типу бойової зброї
        self.cb_weapon_type = self.create_dropdown(melee_scroll, "Клас використовуваної зброї:", 
                                                   ["Колюча (Шпага, Рапіра, Ніж)", 
                                                    "Рубяща (Меч, Сокира)", 
                                                    "Дробяща (Молот, Дворучник)"])
        self.cb_weapon_type.configure(command=lambda v: self.action_calculate_melee())

        # Конструктор повзунків потенціалу тіла
        self.lbl_slider_group_title = ctk.CTkLabel(melee_scroll, text="--- КЕРУВАННЯ ІМПУЛЬСОМ ТІЛА (СУМА СТРОГО = 10.0) ---", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#ff007f")
        self.lbl_slider_group_title.pack(anchor="w", padx=10, pady=(12, 2))

        # ПОВЗУНОК АМПЛІТУДИ (А)
        frame_a = ctk.CTkFrame(melee_scroll, fg_color="transparent")
        frame_a.pack(fill="x", padx=10, pady=8)
        self.lbl_slider_a = ctk.CTkLabel(frame_a, text="Амплітуда замаху (А): 3.3", font=ctk.CTkFont(family="Consolas", size=12), text_color="#c0caf5", width=190, anchor="w")
        self.lbl_slider_a.pack(side="left")
        self.slider_a = ctk.CTkSlider(frame_a, from_=0, to=10, number_of_steps=100, fg_color="#1e2030", progress_color="#ff007f", command=self.on_slider_a_move)
        self.slider_a.set(3.33)
        self.slider_a.pack(side="right", fill="x", expand=True)

        # ПОВЗУНОК ШВИДКОСТІ (V)
        frame_v = ctk.CTkFrame(melee_scroll, fg_color="transparent")
        frame_v.pack(fill="x", padx=10, pady=8)
        self.lbl_slider_v = ctk.CTkLabel(frame_v, text="Швидкість удару (V): 3.3", font=ctk.CTkFont(family="Consolas", size=12), text_color="#00f0ff", width=190, anchor="w")
        self.lbl_slider_v.pack(side="left")
        self.slider_v = ctk.CTkSlider(frame_v, from_=0, to=10, number_of_steps=100, fg_color="#1e2030", progress_color="#00f0ff", command=self.on_slider_v_move)
        self.slider_v.set(3.33)
        self.slider_v.pack(side="right", fill="x", expand=True)

        # ПОВЗУНОК ВАЖКОСТІ (W)
        frame_w = ctk.CTkFrame(melee_scroll, fg_color="transparent")
        frame_w.pack(fill="x", padx=10, pady=8)
        self.lbl_slider_w = ctk.CTkLabel(frame_w, text="Важкість стійки (W): 3.3", font=ctk.CTkFont(family="Consolas", size=12), text_color="#ffaa00", width=190, anchor="w")
        self.lbl_slider_w.pack(side="left")
        self.slider_w = ctk.CTkSlider(frame_w, from_=0, to=10, number_of_steps=100, fg_color="#1e2030", progress_color="#ffaa00", command=self.on_slider_w_move)
        self.slider_w.set(3.34)
        self.slider_w.pack(side="right", fill="x", expand=True)

        # Текстовий дисплей результатів розрахунку механіки удару
        self.txt_melee_output = ctk.CTkTextbox(self.melee_constructor_frame, fg_color="#090a10", font=ctk.CTkFont(family="Consolas", size=11), text_color="#a9b1d6")
        self.txt_melee_output.pack(fill="both", expand=True, padx=20, pady=(15, 20))
        
        self.action_calculate_melee()

    # =====================================================================
    # ДИНАМІЧНИЙ ДИСПЕТЧЕР КУСТАРНОГО ОБМЕЖЕННЯ ПУЛУ
    # =====================================================================
    def action_update_pool_limit(self):
        try:
            val_str = self.ent_melee_pool.get().strip()
            if not val_str: return
            new_limit = float(val_str)
            if new_limit <= 0: return
            
            self.base_pool_limit = new_limit
            self.lbl_slider_group_title.configure(text=f"--- КЕРУВАННЯ ІМПУЛЬСОМ ТІЛА (СУМА СТРОГО = {self.base_pool_limit:.1f}) ---")
            
            # Перебудовуємо межі повзунків під нову місткість
            self.slider_a.configure(to=new_limit)
            self.slider_v.configure(to=new_limit)
            self.slider_w.configure(to=new_limit)
            
            # Пропорційний перерахунок поточних позицій повзунків під нову суму
            current_sum = self.slider_a.get() + self.slider_v.get() + self.slider_w.get()
            if current_sum > 0:
                self.updating_sliders = True
                self.slider_a.set((self.slider_a.get() / current_sum) * new_limit)
                self.slider_v.set((self.slider_v.get() / current_sum) * new_limit)
                self.slider_w.set((self.slider_w.get() / current_sum) * new_limit)
                self.updating_sliders = False
            else:
                self.updating_sliders = True
                self.slider_a.set(new_limit / 3.0)
                self.slider_v.set(new_limit / 3.0)
                self.slider_w.set(new_limit / 3.0)
                self.updating_sliders = False

            self.action_calculate_melee()
        except ValueError:
            pass

    # =====================================================================
    # ЛОГІКА ОДНОЧАСНОГО КЕРУВАННЯ ПОВЗУНКАМИ (ВЗАЄМОЗВ'ЯЗОК ДИНАМІЧНОГО РЕСУРСУ)
    # =====================================================================
    def on_slider_a_move(self, value):
        if self.updating_sliders: return
        self.updating_sliders = True
        
        val_a = float(value)
        val_v = self.slider_v.get()
        val_w = self.slider_w.get()
        
        rem = self.base_pool_limit - val_a
        sum_vw = val_v + val_w
        if sum_vw > 0:
            self.slider_v.set(max(0.0, min(self.base_pool_limit, (val_v / sum_vw) * rem)))
            self.slider_w.set(max(0.0, min(self.base_pool_limit, (val_w / sum_vw) * rem)))
        else:
            self.slider_v.set(rem / 2.0)
            self.slider_w.set(rem / 2.0)
            
        self.updating_sliders = False
        self.action_calculate_melee()

    def on_slider_v_move(self, value):
        if self.updating_sliders: return
        self.updating_sliders = True
        
        val_v = float(value)
        val_a = self.slider_a.get()
        val_w = self.slider_w.get()
        
        rem = self.base_pool_limit - val_v
        sum_aw = val_a + val_w
        if sum_aw > 0:
            self.slider_a.set(max(0.0, min(self.base_pool_limit, (val_a / sum_aw) * rem)))
            self.slider_w.set(max(0.0, min(self.base_pool_limit, (val_w / sum_aw) * rem)))
        else:
            self.slider_a.set(rem / 2.0)
            self.slider_w.set(rem / 2.0)
            
        self.updating_sliders = False
        self.action_calculate_melee()

    def on_slider_w_move(self, value):
        if self.updating_sliders: return
        self.updating_sliders = True
        
        val_w = float(value)
        val_a = self.slider_a.get()
        val_v = self.slider_v.get()
        
        rem = self.base_pool_limit - val_w
        sum_av = val_a + val_v
        if sum_av > 0:
            self.slider_a.set(max(0.0, min(self.base_pool_limit, (val_a / sum_av) * rem)))
            self.slider_v.set(max(0.0, min(self.base_pool_limit, (val_v / sum_av) * rem)))
        else:
            self.slider_a.set(rem / 2.0)
            self.slider_v.set(rem / 2.0)
            
        self.updating_sliders = False
        self.action_calculate_melee()

    # =====================================================================
    # МАТЕМАТИЧНЕ ЯДРО ФІЗИЧНОГО ДАМАГУ (МАСШТАБОВАНИЙ ЛІМІТ БОНУСІВ)
    # =====================================================================
    def action_calculate_melee(self):
        try:
            A = self.slider_a.get()
            V = self.slider_v.get()
            W = self.slider_w.get()
            
            # Оновлюємо лейбли значень над повзунками
            self.lbl_slider_a.configure(text=f"Амплітуда замаху (А): {A:.1f}")
            self.lbl_slider_v.configure(text=f"Швидкість удару (V): {V:.1f}")
            self.lbl_slider_w.configure(text=f"Важкість стійки (W): {W:.1f}")

            # Зчитування типу кубика з текстового поля
            dk_input = self.ent_melee_dk.get().strip()
            dk_sides = int(dk_input) if dk_input.isdigit() and int(dk_input) > 0 else 8
            
            weapon_type = self.cb_weapon_type.get()

            # --- Динамічний поріг зрізу плоского бонусу залежно від пулу воїна ---
            # Бонус не може бути більшим за половину максимального пулу (floor(pool / 2))
            dynamic_flat_limit = math.floor(self.base_pool_limit / 2)

            # --- 1. РОЗРАХУНОК КУБИКИВ ВІД АМПЛІТУДИ ТА КЛАСУ ЗБРОЇ ---
            base_cubes = 1
            extra_cubes = 0
            
            if "Колюча" in weapon_type:
                if A >= 9.0:
                    extra_cubes = 1
                else:
                    extra_cubes = 0
                max_possible_cubes = "2dK (Ліміт колючої геометрії)"
            elif "Рубяща" in weapon_type:
                extra_cubes = math.floor(A / 5.0)
                max_possible_cubes = "3dK"
            else:
                # Дробяща зброя: якщо А >= 5.0, додається строго 1 додатковий кубик (разом максимум 2dK)
                extra_cubes = math.floor(A / 8.0)
                max_possible_cubes = "3dK"
            total_cubes = base_cubes + extra_cubes

            # --- 2. ДИНАМІЧНИЙ ВИБІР ПЛОСКОГО БОНУСУ ТА НАЗВИ МОДИФІКАТОРА ---
            if "Дробяща" in weapon_type:
                flat_damage_bonus = min(dynamic_flat_limit, math.floor(W))
                modifier_name = f"Модифікатор сили (W)   : +{flat_damage_bonus} (Макс для пулу: +{dynamic_flat_limit})"
            elif "Рубяща" in weapon_type:
                flat_damage_bonus = min(dynamic_flat_limit, math.floor(V))
                modifier_name = f"Модифікатор швидкості : +{flat_damage_bonus} (Макс для пулу: +{dynamic_flat_limit})"
            else:
                flat_damage_bonus = math.floor(V)
                modifier_name = f"Модифікатор швидкості : +{flat_damage_bonus}"

            # 3. Ефект Важкості (Бонус до Класу Обладунку КБ)
            ac_bonus = math.floor(W / 2)

            # Розрахунок середнього математичного урону
            avg_single_cube = (1 + dk_sides) / 2
            avg_total_damage = (total_cubes * avg_single_cube) + flat_damage_bonus

            # Конструктор текстової формули для кидка
            game_formula = f"{total_cubes}d{dk_sides} + {flat_damage_bonus}"

            # Обчислення ультимативних пасивних модифікаторів при фокусуванні імпульсу тіла
            special_effects = []
            if "Колюча" in weapon_type and V >= 9.5:
                special_effects.append("УЛЬТРА-ЕФЕКТ [ТОЧКОВИЙ ПРОКОЛ]: Ігнорує КБ від важких обладунків та щитів.")
            elif "Рубяща" in weapon_type and A >= 9.5:
                special_effects.append("УЛЬТРА-ЕФЕКТ [ГЛИБОКИЙ РОЗТИН]: Наносить критичний урон на випадах 19-20.")
            elif "Дробяща" in weapon_type and W >= 9.5:
                special_effects.append("УЛЬТРА-ЕФЕКТ [ЧЕРЕПОЛОМ]: Збиває з ніг, ламає щити або приголомшує ціль.")

            if not special_effects:
                special_effects.append("Активні пасивні бойові ефекти відсутні.")

            # Рендеринг виводу даних на дисплей блоку
            self.txt_melee_output.configure(state="normal")
            self.txt_melee_output.delete("1.0", ctk.END)
            
            log = (
                f">> БІОМЕХАНІЧНИЙ РОЗРАХУНОК ФІЗИЧНОЇ АТАКИ:\n"
                f"--------------------------------------------------\n"
                f"• Клас зброї                 : {weapon_type.split(' (')[0].upper()}\n"
                f"• Загальний ліміт пулу тіла  : {self.base_pool_limit:.1f}\n"
                f"• Потенціал реалізації замаху: макс. {max_possible_cubes}\n"
                f"• Розподіл енергії тіла      : A={A/self.base_pool_limit*100:.0f}% | V={V/self.base_pool_limit*100:.0f}% | W={W/self.base_pool_limit*100:.0f}%\n"
                f"--------------------------------------------------\n"
                f"• {modifier_name}\n"
                f"• Модифікатор захисту (КБ)   : +{ac_bonus}\n"
                f"--------------------------------------------------\n"
                f"• ФОРМУЛА ДЛЯ КИДКА НА СТОЛІ  : {game_formula}\n"
                f"• Очікуваний середній дамаг  : {avg_total_damage:.1f} HP\n"
                f"--------------------------------------------------\n"
                f"{chr(10).join(special_effects)}"
            )
            self.txt_melee_output.insert("1.0", log)
            self.txt_melee_output.configure(state="disabled")

        except Exception as e:
            self.txt_melee_output.configure(state="normal")
            self.txt_melee_output.delete("1.0", ctk.END)
            self.txt_melee_output.insert("1.0", f">> ПОМИЛКА ІНЖЕНЕРІЇ ТІЛА:\n{e}")
            self.txt_melee_output.configure(state="disabled")

    # =====================================================================
    # СЕРВІСНІ СЕКЦІЇ ТА НАЛАШТУВАННЯ ПРАВОЇ ЧАСТИНИ ДИСПЕТЧЕРА
    # =====================================================================
    def switch_mode(self, mode):
        if mode == "magic":
            self.btn_mode_magic.configure(fg_color="#1a1c2e", text_color="#00f0ff")
            self.btn_mode_melee.configure(fg_color="transparent", text_color="#a9b1d6")
            self.melee_constructor_frame.grid_forget()
            self.magic_constructor_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        elif mode == "melee":
            self.btn_mode_melee.configure(fg_color="#1a1c2e", text_color="#ffaa00")
            self.btn_mode_magic.configure(fg_color="transparent", text_color="#a9b1d6")
            self.magic_constructor_frame.grid_forget()
            self.melee_constructor_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.action_calculate_melee()

    def setup_right_dispatcher_ui(self):
        bat_title_frame = ctk.CTkFrame(self.main_right_scroll, fg_color="transparent")
        bat_title_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(bat_title_frame, text="02 // СЛОТИ БАТАРЕЙОК", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color="#00f0ff").pack(side="left")
        
        self.ent_new_bat_name = ctk.CTkEntry(bat_title_frame, placeholder_text="Ім'я...", width=100, font=ctk.CTkFont(size=11))
        self.ent_new_bat_name.pack(side="left", padx=5)
        self.ent_new_bat_cap = ctk.CTkEntry(bat_title_frame, placeholder_text="Місткість", width=60, font=ctk.CTkFont(size=11))
        self.ent_new_bat_cap.pack(side="left", padx=2)
        btn_add_bat = ctk.CTkButton(bat_title_frame, text="+", width=30, fg_color="#2f334d", hover_color="#444a73", command=self.action_add_battery)
        btn_add_bat.pack(side="left", padx=5)

        self.bat_container = ctk.CTkFrame(self.main_right_scroll, fg_color="#1a1c2e", corner_radius=6)
        self.bat_container.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.main_right_scroll, text="03 // SPELL CONFIG BANK (ШАБЛОНИ)", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color="#00f0ff").pack(anchor="w", padx=10, pady=(15, 2))
        
        self.templates_container = ctk.CTkFrame(self.main_right_scroll, fg_color="#1a1c2e", corner_radius=6)
        self.templates_container.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.main_right_scroll, text="04 // ACTIVE SUSTAINED SPELLS (ПІДТРИМУВАННЯ)", font=ctk.CTkFont(family="Consolas", size=14, weight="bold"), text_color="#ff007f").pack(anchor="w", padx=10, pady=(15, 2))
        
        self.active_container = ctk.CTkFrame(self.main_right_scroll, fg_color="#1a1c2e", corner_radius=6)
        self.active_container.pack(fill="x", padx=10, pady=5)

        self.btn_next_round = ctk.CTkButton(
            self.main_right_scroll, 
            text="Н Е К С Т  -  Р А У Н Д  (Списання 10% для підтримки заклинань)", 
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            fg_color="#00f0ff", text_color="#000000", hover_color="#00b8c4",
            height=48, corner_radius=8,
            command=self.action_next_round
        )
        self.btn_next_round.pack(fill="x", padx=10, pady=25)

        self.update_battery_displays()
        self.update_templates_display()
        self.update_active_spells_display()

    def create_label(self, container, text, color):
        lbl = ctk.CTkLabel(container, text=text, font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color=color)
        lbl.pack(anchor="w", padx=10, pady=(12, 2))

    def create_dropdown(self, container, label_text, values):
        frame = ctk.CTkFrame(container, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(family="Consolas", size=12), text_color="#787c99").pack(side="left")
        cb = ctk.CTkComboBox(frame, values=values, width=210, fg_color="#1e2030", border_color="#2f334d", text_color="#c0caf5", corner_radius=6)
        cb.pack(side="right")
        return cb

    def create_input(self, container, label_text, default_val):
        frame = ctk.CTkFrame(container, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=3)
        ctk.CTkLabel(frame, text=label_text, font=ctk.CTkFont(family="Consolas", size=12), text_color="#787c99").pack(side="left")
        ent = ctk.CTkEntry(frame, width=210, fg_color="#1e2030", border_color="#2f334d", text_color="#c0caf5", corner_radius=6)
        ent.insert(0, default_val)
        ent.pack(side="right")
        return ent

    # =====================================================================
    # ОРИГІНАЛЬНЕ ОПЕРАЦІЙНЕ ЯДРО МАГІЇ
    # =====================================================================
    def run_core_formulas(self):
        try:
            kl_idx = ["До 10 см", "10-30 см", "30-100 см", "1-3 м"].index(self.cb_size.get().split(" (")[0])
            K_l = [1.0, 1.2, 1.5, 2.0][kl_idx]
            A_shape = [5, 15, 40][["Проста / Аморфна", "Середня / Гостра", "Складна / Анатомічна"].index(self.cb_shape.get().split(" = ")[0])]
            K_vector = 1.0 + [0.0, 0.2, 0.5, 0.8][["Напрям", "Швидкість", "Цикл", "Повторення"].index(self.cb_vector.get().split(" = ")[0])]
            S_m = [0.5, 1.0, 1.5][["0.5", "1.0", "1.5"].index(self.cb_sm.get().split(" (")[0])]
            K_m = float(self.ent_km.get())
            K_q = float(self.ent_kq.get())
            N_dice = int(self.ent_ndice.get())
            dK = self.cb_dk.get()
            n_arcs = int(self.ent_arcs.get())
            is_far = self.cb_dist.get() != "В радіусі ефективної дальности"

            dk_mass_map = {"d4": 3, "d6": 4, "d8": 5, "d10": 6, "d12": 7}
            m = N_dice * dk_mass_map[dK]

            v0 = 10
            harmonic_sum = sum((v0 * (1.0 / i)) for i in range(1, n_arcs + 1)) if n_arcs > 0 else 0
            v = v0 + harmonic_sum

            A_total = math.ceil(K_l * (((m * K_m * K_q) + A_shape) + (m * K_vector * v)))
            speed_mod = n_arcs * 2
            
            dk_sides = int(dK[1:])
            avg_damage = (((N_dice * (1 + dk_sides) / 2) * S_m) + speed_mod) / (2 if is_far else 1)
            game_formula = f"({N_dice}{dK}{f' * {S_m}' if S_m != 1.0 else ''}) + {speed_mod}{' / 2' if is_far else ''}"

            return {
                "success": True, "A_total": A_total, "m": m, "v": v, "S_m": S_m,
                "speed_mod": speed_mod, "avg_damage": avg_damage, "game_formula": game_formula,
                "raw_params": {
                    "size": self.cb_size.get(), "shape": self.cb_shape.get(), "vector": self.cb_vector.get(),
                    "sm": self.cb_sm.get(), "km": K_m, "kq": K_q, "ndice": N_dice, "dk": dK, "arcs": n_arcs, "dist": self.cb_dist.get()
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def action_calculate(self):
        res = self.run_core_formulas()
        self.txt_calc_output.configure(state="normal")
        self.txt_calc_output.delete("1.0", ctk.END)
        
        if res["success"]:
            self.last_calculated_data = res
            log = (
                f">> МАТЕМАТИЧНА ІНІЦІАЛІЗАЦІІЯ РУНИ:\n"
                f"--------------------------------------------------\n"
                f"• Аркана для створення          : {res['A_total']} ed.\n"
                f"• Маса снаряду (m)              : {res['m']} me ({res['m']*0.125:.3f} kg)\n"
                f"• Швидкість випускання (v)      : {res['v']:.2f} m/s\n"
                f"--------------------------------------------------\n"
                f"• Дамаг спела       : {res['game_formula']}\n"
                f"• Середній дамаг    : {res['avg_damage']:.1f} HP"
            )
        else:
            self.last_calculated_data = None
            log = f">> ОШИБКА РАСЧЕТА СТРУКТУРЫ:\n{res['error']}"
            
        self.txt_calc_output.insert("1.0", log)
        self.txt_calc_output.configure(state="disabled")

    def action_save_template(self):
        name = self.ent_save_name.get().strip()
        if not name:
            messagebox.showwarning("Увага!", "Введіть ім'я руни!")
            return
        res = self.run_core_formulas()
        if not res["success"]:
            return

        self.saved_spells[name] = res
        self.save_to_json() 
        self.update_templates_display()
        self.ent_save_name.delete(0, ctk.END)

    def action_add_battery(self):
        name = self.ent_new_bat_name.get().strip()
        cap_str = self.ent_new_bat_cap.get().strip()
        if not name or not cap_str:
            return
        try:
            cap = int(cap_str)
            self.batteries[name] = {"max": cap, "current": cap}
            self.save_to_json() 
            self.update_battery_displays()
            self.ent_new_bat_name.delete(0, ctk.END)
            self.ent_new_bat_cap.delete(0, ctk.END)
        except:
            pass

    def action_activate_spell(self, spell_name, data):
        available_bats = list(self.batteries.keys())
        if not available_bats:
            messagebox.showerror("Помилка", "Немає доступних батарейок!")
            return

        select_win = ctk.CTkToplevel(self)
        select_win.title("ВИБІР ДЖЕРЕЛА")
        select_win.geometry("350x180")
        select_win.transient(self)
        select_win.grab_set()

        ctk.CTkLabel(select_win, text=f"Активація: {spell_name}\Вартість: {data['A_total']} Аркани\nВиберіть джерело:", font=ctk.CTkFont(family="Consolas", size=12)).pack(pady=10)
        cb_choice = ctk.CTkComboBox(select_win, values=available_bats, width=200)
        cb_choice.pack(pady=5)

        def confirm():
            bat_choice = cb_choice.get()
            cost = data['A_total']
            if self.batteries[bat_choice]["current"] < cost:
                messagebox.showerror("Відмова", "Недостатньо заряду в вибраній батарейці!")
                return
            
            self.batteries[bat_choice]["current"] -= cost
            maintenance = max(1, math.ceil(cost * 0.10))
            
            self.active_spells.append({
                "name": spell_name, "cost": cost, "battery": bat_choice,
                "maintenance": maintenance, "formula": data["game_formula"]
            })
            
            self.save_to_json() 
            self.update_battery_displays()
            self.update_active_spells_display()
            select_win.destroy()

        ctk.CTkButton(select_win, text="ПІДКЛЮЧИТИ І КАСТАНУТИ", fg_color="#00f0ff", text_color="#000000", command=confirm).pack(pady=15)

    def action_deactivate_spell(self, idx):
        if idx < len(self.active_spells):
            self.active_spells.pop(idx)
            self.save_to_json() 
            self.update_active_spells_display()

    def action_next_round(self):
        logs = []
        for spell in list(self.active_spells):
            bat = spell["battery"]
            maint = spell["maintenance"]
            
            if bat in self.batteries:
                if self.batteries[bat]["current"] >= maint:
                    self.batteries[bat]["current"] -= maint
                    logs.append(f"• [Підтримка] '{spell['name']}' удержано. С [{bat}] снято {maint} ед.")
                else:
                    logs.append(f"• !!! ВИПАРОВУВАННЯ: Руна '{spell['name']}' розсіялась! На [{bat}] закінчився заряд.")
                    self.active_spells.remove(spell)
            else:
                self.active_spells.remove(spell)

        self.save_to_json() 
        self.update_battery_displays()
        self.update_active_spells_display()
        
        if logs:
            messagebox.showinfo("ФАЗА ЗАВЕРШЕНА", "Звіт по підтриманню заклинань в раунді:\n\n" + "\n".join(logs))

    # =====================================================================
    # ДИНАМІЧНИЙ РЕНДЕРИНГ ДИСПЕТЧЕРА
    # =====================================================================
    def update_battery_displays(self):
        for widget in self.bat_container.winfo_children():
            widget.destroy()

        if not self.batteries:
            ctk.CTkLabel(self.bat_container, text="// БАТАРЕЇ НЕ ПІДКЛЮЧЕНІ", font=ctk.CTkFont(family="Consolas", size=11), text_color="#5f647d").pack(pady=10)
            return

        for name, info in self.batteries.items():
            frame = ctk.CTkFrame(self.bat_container, fg_color="#222538", height=38, corner_radius=4)
            frame.pack(fill="x", pady=2, padx=5)
            
            pct = info["current"] / info["max"] if info["max"] > 0 else 0
            color = "#00f0ff" if pct > 0.4 else "#ffaa00" if pct > 0.15 else "#ff0055"
            
            ctk.CTkLabel(frame, text=f"🔋 {name}: ", font=ctk.CTkFont(family="Consolas", size=12, weight="bold")).pack(side="left", padx=10)
            ctk.CTkLabel(frame, text=f"{info['current']} / {info['max']} Аркани", font=ctk.CTkFont(family="Consolas", size=12), text_color=color).pack(side="left")
            
            def delete_bat(b_name=name):
                del self.batteries[b_name]
                self.save_to_json()
                self.update_battery_displays()
                
            ctk.CTkButton(frame, text="Видалити", width=60, height=22, fg_color="#44475a", text_color="#ff5555", font=ctk.CTkFont(size=10), command=delete_bat).pack(side="right", padx=10)

    def update_templates_display(self):
        for widget in self.templates_container.winfo_children():
            widget.destroy()

        if not self.saved_spells:
            ctk.CTkLabel(self.templates_container, text="// БАНК ПУСТ. ЗБЕРЕЖІТЬ КОНФИГУРАЦІЮ ЗЛІВА", font=ctk.CTkFont(family="Consolas", size=11), text_color="#5f647d").pack(pady=15)
            return

        for name, data in self.saved_spells.items():
            frame = ctk.CTkFrame(self.templates_container, fg_color="#222538", corner_radius=4)
            frame.pack(fill="x", pady=2, padx=5)
            
            info_str = f"✨ {name} [{data['game_formula']}] — {data['A_total']} Ед."
            ctk.CTkLabel(frame, text=info_str, font=ctk.CTkFont(family="Consolas", size=11)).pack(side="left", padx=10, pady=6)
            
            def delete_template(t_name=name):
                del self.saved_spells[t_name]
                self.save_to_json()
                self.update_templates_display()

            ctk.CTkButton(frame, text="✖", width=25, height=24, fg_color="transparent", text_color="#ff5555", hover_color="#342230", command=delete_template).pack(side="right", padx=5)
            ctk.CTkButton(frame, text="АКТИВИРОВАТЬ", width=90, height=24, fg_color="#ff007f", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), command=lambda n=name, d=data: self.action_activate_spell(n, d)).pack(side="right", padx=2)

            def load_template(d=data):
                p = d["raw_params"]
                self.cb_size.set(p["size"])
                self.cb_shape.set(p["shape"])
                self.cb_vector.set(p["vector"])
                self.cb_sm.set(p["sm"])
                self.ent_km.delete(0, ctk.END)
                self.ent_km.insert(0, str(p["km"]))
                self.ent_kq.delete(0, ctk.END)
                self.ent_kq.insert(0, str(p["kq"]))
                self.ent_ndice.delete(0, ctk.END)
                self.ent_ndice.insert(0, str(p["ndice"]))
                self.cb_dk.set(p["dk"])
                self.ent_arcs.delete(0, ctk.END)
                self.ent_arcs.insert(0, str(p["arcs"]))
                self.cb_dist.set(p["dist"])
                self.switch_mode("magic")
                self.action_calculate()

            ctk.CTkButton(frame, text="👁️", width=30, height=24, fg_color="#3d4466", command=load_template).pack(side="right", padx=2)

    def update_active_spells_display(self):
        for widget in self.active_container.winfo_children():
            widget.destroy()

        if not self.active_spells:
            ctk.CTkLabel(self.active_container, text="// НЕМАЄ АКТИВНИХ ПІДТРИМУВАНИХ РУН", font=ctk.CTkFont(family="Consolas", size=11), text_color="#5f647d").pack(pady=20)
            return

        for idx, spell in enumerate(self.active_spells):
            frame = ctk.CTkFrame(self.active_container, fg_color="#1d2d3d", border_width=1, border_color="#00f0ff", corner_radius=6)
            frame.pack(fill="x", pady=3, padx=5)
            
            desc = f"🔷 {spell['name'].upper()} | Лінк: [{spell['battery']}]\n" \
                   f"   Дамаг: {spell['formula']} | Списання: {spell['maintenance']} од./раунд"
            
            ctk.CTkLabel(frame, text=desc, font=ctk.CTkFont(family="Consolas", size=11), justify="left").pack(side="left", padx=10, pady=6)
            ctk.CTkButton(frame, text="ОТКЛЮЧИТЬ", width=85, height=25, fg_color="#2b3047", hover_color="#ff5555", text_color="#ff5555", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), command=lambda i=idx: self.action_deactivate_spell(i)).pack(side="right", padx=10)

if __name__ == "__main__":
    app = ArcanaTacticalCore()
    app.mainloop()