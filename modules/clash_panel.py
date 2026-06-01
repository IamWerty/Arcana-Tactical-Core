"""
modules/clash_panel.py
======================
Права панель для режиму ФІЗИЧНИЙ ДАМАГ.
Реалізує систему "Шкала Спротиву" (Clash Tug-of-War) з md-файлу.

Шкала: від -3 до +3
  +3 → Перемога гравця (крит + prone/stunned)
  -3 → Перемога ворога (повний удар + зброя відлітає)
"""
import random
import customtkinter as ctk
from core.melee_engine import calculate_clash_round
from ui.widgets import FONT_MONO

SCALE_MIN = -3
SCALE_MAX = +3

# Кольори шкали
COLOR_PLAYER = "#00f0ff"
COLOR_ENEMY = "#ff0055"
COLOR_NEUTRAL = "#ffaa00"
COLOR_BG_CARD = "#1a1c2e"


class ClashPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, data_manager):
        self.dm = data_manager
        self.parent = parent_frame

        self.scroll = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self._build()

    # =========================================================================
    # ПОБУДОВА UI
    # =========================================================================
    def _build(self):
        # --- Заголовок ---
        ctk.CTkLabel(self.scroll, text="⚔️  СИСТЕМА CLASH",
                     font=ctk.CTkFont(family=FONT_MONO, size=16, weight="bold"),
                     text_color=COLOR_PLAYER).pack(anchor="w", padx=10, pady=(10, 2))
        ctk.CTkLabel(self.scroll, text="// Шкала Спротиву (Tug-of-War)",
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#5f647d").pack(anchor="w", padx=10, pady=(0, 10))

        # --- Секція налаштування модифікаторів ---
        self._build_modifier_inputs()

        # --- Візуальна шкала ---
        self._build_scale_display()

        # --- Кнопки дій ---
        self._build_action_buttons()

        # --- Лог подій ---
        self._build_log()

        # Перший рендер
        self.refresh_scale()

    def _build_modifier_inputs(self):
        mod_frame = ctk.CTkFrame(self.scroll, fg_color=COLOR_BG_CARD, corner_radius=8)
        mod_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(mod_frame, text="— МОДИФІКАТОРИ АТАКИ (d20 + мод) —",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color="#ff007f").pack(anchor="w", padx=10, pady=(10, 5))

        row = ctk.CTkFrame(mod_frame, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 10))

        # Гравець
        ctk.CTkLabel(row, text="🧑 Гравець +",
                     font=ctk.CTkFont(family=FONT_MONO, size=12), text_color=COLOR_PLAYER,
                     width=110, anchor="w").pack(side="left")
        self.ent_player_mod = ctk.CTkEntry(row, width=60, fg_color="#111322",
                                            border_color=COLOR_PLAYER, text_color=COLOR_PLAYER,
                                            font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
                                            corner_radius=4)
        self.ent_player_mod.insert(0, "5")
        self.ent_player_mod.pack(side="left", padx=5)

        # Ворог
        ctk.CTkLabel(row, text="💀 Ворог +",
                     font=ctk.CTkFont(family=FONT_MONO, size=12), text_color=COLOR_ENEMY,
                     width=80, anchor="w").pack(side="left", padx=(20, 0))
        self.ent_enemy_mod = ctk.CTkEntry(row, width=60, fg_color="#111322",
                                           border_color=COLOR_ENEMY, text_color=COLOR_ENEMY,
                                           font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
                                           corner_radius=4)
        self.ent_enemy_mod.insert(0, "3")
        self.ent_enemy_mod.pack(side="left", padx=5)

    def _build_scale_display(self):
        scale_frame = ctk.CTkFrame(self.scroll, fg_color=COLOR_BG_CARD, corner_radius=8)
        scale_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(scale_frame, text="— ШКАЛА СПРОТИВУ —",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color="#5f647d").pack(anchor="w", padx=10, pady=(10, 5))

        # Легенда
        legend_row = ctk.CTkFrame(scale_frame, fg_color="transparent")
        legend_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(legend_row, text="Ворог тисне ◀",
                     font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=COLOR_ENEMY).pack(side="left")
        ctk.CTkLabel(legend_row, text="▶ Гравець тисне",
                     font=ctk.CTkFont(family=FONT_MONO, size=10), text_color=COLOR_PLAYER).pack(side="right")

        # Сам рядок зі слотами шкали — центрований
        self.scale_slots_frame = ctk.CTkFrame(scale_frame, fg_color="transparent")
        self.scale_slots_frame.pack(anchor="center", pady=(2, 10))

        # Слоти [-3, -2, -1, 0, +1, +2, +3]
        self.scale_slots = []
        for i in range(SCALE_MIN, SCALE_MAX + 1):
            slot = ctk.CTkLabel(
                self.scale_slots_frame,
                text=f"{i:+d}" if i != 0 else " 0 ",
                font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
                width=46, height=36,
                fg_color="#222538", text_color="#5f647d",
                corner_radius=4
            )
            slot.pack(side="left", padx=2)
            self.scale_slots.append((i, slot))

        # Поточний статус
        self.lbl_scale_status = ctk.CTkLabel(
            scale_frame, text="[ Очікування старту Clash ]",
            font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
            text_color=COLOR_NEUTRAL
        )
        self.lbl_scale_status.pack(pady=(0, 6))

        # --- Ручне керування шкалою ---
        ctk.CTkLabel(scale_frame, text="— РУЧНЕ КЕРУВАННЯ —",
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color="#44475a").pack()

        manual_row = ctk.CTkFrame(scale_frame, fg_color="transparent")
        manual_row.pack(pady=(4, 12))

        # Кнопки: -2, -1  |  [ШКАЛА]  |  +1, +2
        btn_cfg = [
            ("-2", -2, COLOR_ENEMY,   "#3a0f1a", "#550d1f"),
            ("-1", -1, "#ff5577",     "#2a1020", "#3d1530"),
            ("+1", +1, "#00ccaa",     "#0d2a22", "#0f3a2e"),
            ("+2", +2, COLOR_PLAYER,  "#0d2535", "#0f3550"),
        ]

        self._manual_btns = []
        for label, delta, fg, bg, hover in btn_cfg:
            btn = ctk.CTkButton(
                manual_row, text=label,
                width=54, height=38,
                font=ctk.CTkFont(family=FONT_MONO, size=15, weight="bold"),
                fg_color=bg, text_color=fg, hover_color=hover,
                border_width=1, border_color=fg,
                corner_radius=6,
                state="disabled",
                command=lambda d=delta: self._action_manual_shift(d)
            )
            btn.pack(side="left", padx=4)
            self._manual_btns.append(btn)

    def _build_action_buttons(self):
        btn_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=8)

        self.btn_start = ctk.CTkButton(
            btn_frame, text="⚔️  ПОЧАТИ CLASH",
            font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
            fg_color="#ff007f", text_color="#ffffff", hover_color="#c90062",
            height=40, corner_radius=6,
            command=self._action_start_clash
        )
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_roll = ctk.CTkButton(
            btn_frame, text="🎲  КИНУТИ КУБИКИ",
            font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
            fg_color="#383a59", text_color="#ffffff", hover_color="#4a4e7a",
            height=40, corner_radius=6,
            state="disabled",
            command=self._action_roll_round
        )
        self.btn_roll.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # Кнопка "Підтримка союзника" — витрата реакції, +1/+2 до кидка
        self.btn_ally = ctk.CTkButton(
            self.scroll, text="🗣️  ПІДТРИМКА СОЮЗНИКА  (+2 до наступного кидка гравця)",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            fg_color="#222538", text_color="#ffaa00", hover_color="#2e3150",
            height=32, corner_radius=6,
            state="disabled",
            command=self._action_ally_support
        )
        self.btn_ally.pack(fill="x", padx=10, pady=(0, 5))

        self.btn_reset = ctk.CTkButton(
            self.scroll, text="↺  СКИНУТИ CLASH",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color="transparent", text_color="#5f647d", hover_color="#1a1c2e",
            height=28,
            command=self._action_reset
        )
        self.btn_reset.pack(fill="x", padx=10)

        # Бонус союзника (внутрішній стан)
        self._ally_bonus = 0

    def _build_log(self):
        ctk.CTkLabel(self.scroll, text="— ЛОГ ЗІТКНЕННЯ —",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color="#5f647d").pack(anchor="w", padx=10, pady=(12, 2))

        self.txt_log = ctk.CTkTextbox(
            self.scroll, fg_color="#090a10",
            font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#a9b1d6",
            height=200
        )
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=(0, 15))
        self.txt_log.insert("1.0", ">> CLASH МОДУЛЬ ГОТОВИЙ. НАТИСНІТЬ 'ПОЧАТИ CLASH'.\n")
        self.txt_log.configure(state="disabled")

    # =========================================================================
    # ОНОВЛЕННЯ ШКАЛИ
    # =========================================================================
    def refresh_scale(self):
        current = self.dm.clash_state["scale"]
        active = self.dm.clash_state["active"]

        for val, slot in self.scale_slots:
            if not active:
                slot.configure(fg_color="#222538", text_color="#5f647d")
                continue

            if val == current:
                if current > 0:
                    slot.configure(fg_color=COLOR_PLAYER, text_color="#000000")
                elif current < 0:
                    slot.configure(fg_color=COLOR_ENEMY, text_color="#ffffff")
                else:
                    slot.configure(fg_color=COLOR_NEUTRAL, text_color="#000000")
            elif val == SCALE_MIN:
                slot.configure(fg_color="#3a1020", text_color=COLOR_ENEMY)
            elif val == SCALE_MAX:
                slot.configure(fg_color="#0d2e35", text_color=COLOR_PLAYER)
            else:
                slot.configure(fg_color="#222538", text_color="#5f647d")

        # Статус-рядок
        if not active:
            self.lbl_scale_status.configure(text="[ Очікування старту Clash ]", text_color=COLOR_NEUTRAL)
        elif current >= SCALE_MAX:
            self.lbl_scale_status.configure(text="⚡ ПЕРЕМОГА ГРАВЦЯ! Крит + Prone/Stunned", text_color=COLOR_PLAYER)
        elif current <= SCALE_MIN:
            self.lbl_scale_status.configure(text="💥 ПЕРЕМОГА ВОРОГА! Гравець відлітає назад", text_color=COLOR_ENEMY)
        else:
            bar = "▓" * (current + 3) + "░" * (SCALE_MAX - current)
            self.lbl_scale_status.configure(text=f"Шкала: {current:+d}  [{bar}]", text_color=COLOR_NEUTRAL)

    # =========================================================================
    # LOG HELPERS
    # =========================================================================
    def _log(self, text: str):
        self.txt_log.configure(state="normal")
        self.txt_log.insert(ctk.END, text + "\n")
        self.txt_log.see(ctk.END)
        self.txt_log.configure(state="disabled")
        self.dm.push_clash_log(text)

    def _log_separator(self):
        self._log("─" * 42)

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def _action_start_clash(self):
        self.dm.reset_clash()
        self._ally_bonus = 0

        self.btn_roll.configure(state="normal")
        self.btn_ally.configure(state="normal")
        for b in self._manual_btns:
            b.configure(state="normal")

        # Очищуємо лог
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", ctk.END)
        self.txt_log.configure(state="disabled")

        self._log(">> CLASH РОЗПОЧАТО! Клинки схрещено.")
        self._log(">> Шкала встановлена на 0 (нейтрально).")
        self._log_separator()
        self.refresh_scale()

    def _action_roll_round(self):
        if not self.dm.clash_state["active"]:
            return

        # Зчитуємо модифікатори
        try:
            player_mod = int(self.ent_player_mod.get().strip())
        except ValueError:
            player_mod = 0
        try:
            enemy_mod = int(self.ent_enemy_mod.get().strip())
        except ValueError:
            enemy_mod = 0

        # Кидки d20
        player_raw = random.randint(1, 20)
        enemy_raw = random.randint(1, 20)
        player_total = player_raw + player_mod + self._ally_bonus
        enemy_total = enemy_raw + enemy_mod

        # Результат раунду
        result = calculate_clash_round(player_total, enemy_total)
        old_scale = self.dm.clash_state["scale"]
        new_scale = max(SCALE_MIN, min(SCALE_MAX, old_scale + result["delta"]))
        self.dm.clash_state["scale"] = new_scale

        # Скидаємо бонус союзника після використання
        if self._ally_bonus != 0:
            self._log(f"   [Бонус союзника +{self._ally_bonus} застосовано!]")
            self._ally_bonus = 0

        # Лог
        self._log(f"🧑 Гравець: d20({player_raw}) + {player_mod} = {player_total}")
        self._log(f"💀 Ворог:   d20({enemy_raw}) + {enemy_mod} = {enemy_total}")
        self._log(f"   ▶ {result['desc']}")
        self._log(f"   Шкала: {old_scale:+d} → {new_scale:+d}")

        self.refresh_scale()

        # Перевірка кінця Clash
        if new_scale >= SCALE_MAX:
            self._log_separator()
            self._log("⚡⚡ ПЕРЕМОГА ГРАВЦЯ!")
            self._log("   Ворог отримує ПОВНИЙ ДАМАГ зброї з АВТО-КРИТОМ.")
            self._log("   Статус: PRONE або STUNNED до кінця наступного ходу.")
            self._log("   Ворог ГУБИТЬ свій хід.")
            self._log_separator()
            self._end_clash()

        elif new_scale <= SCALE_MIN:
            self._log_separator()
            self._log("💥💥 ПЕРЕМОГА ВОРОГА!")
            self._log("   Гравець отримує ПОВНИЙ КУБИК ШКОДИ + модифікатор.")
            self._log("   Зброя гравця відлітає на 10 футів убік.")
            self._log("   Гравець ГУБИТЬ свій хід.")
            self._log_separator()
            self._end_clash()

        else:
            self._log_separator()

    def _action_manual_shift(self, delta: int):
        if not self.dm.clash_state["active"]:
            return
        old = self.dm.clash_state["scale"]
        new = max(SCALE_MIN, min(SCALE_MAX, old + delta))
        self.dm.clash_state["scale"] = new
        sign = "+" if delta > 0 else ""
        who = "🧑 Гравець" if delta > 0 else "💀 Ворог"
        self._log(f"[Ручно] {who} зсуває шкалу {sign}{delta}  ({old:+d} → {new:+d})")
        self.refresh_scale()

        if new >= SCALE_MAX:
            self._log_separator()
            self._log("⚡⚡ ПЕРЕМОГА ГРАВЦЯ!")
            self._log("   Ворог отримує ПОВНИЙ ДАМАГ зброї з АВТО-КРИТОМ.")
            self._log("   Статус: PRONE або STUNNED до кінця наступного ходу.")
            self._log("   Ворог ГУБИТЬ свій хід.")
            self._log_separator()
            self._end_clash()
        elif new <= SCALE_MIN:
            self._log_separator()
            self._log("💥💥 ПЕРЕМОГА ВОРОГА!")
            self._log("   Гравець отримує ПОВНИЙ КУБИК ШКОДИ + модифікатор.")
            self._log("   Зброя гравця відлітає на 10 футів убік.")
            self._log("   Гравець ГУБИТЬ свій хід.")
            self._log_separator()
            self._end_clash()

    def _action_ally_support(self):
        self._ally_bonus = 2
        self._log("🗣️ Союзник вигукує підтримку! Наступний кидок гравця: +2")
        self.btn_ally.configure(state="disabled")  # одноразово за Clash

    def _action_reset(self):
        self.dm.clash_state["active"] = False
        self.dm.clash_state["scale"] = 0
        self._ally_bonus = 0
        self.btn_roll.configure(state="disabled")
        self.btn_ally.configure(state="disabled")
        for b in self._manual_btns:
            b.configure(state="disabled")

        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", ctk.END)
        self.txt_log.insert("1.0", ">> Clash скинуто. Готовий до нового зіткнення.\n")
        self.txt_log.configure(state="disabled")
        self.refresh_scale()

    def _end_clash(self):
        self.dm.clash_state["active"] = False
        self.btn_roll.configure(state="disabled")
        self.btn_ally.configure(state="disabled")
        for b in self._manual_btns:
            b.configure(state="disabled")
        self._log(">> Clash завершено. Натисніть 'ПОЧАТИ CLASH' для нового зіткнення.")