"""
modules/clash_panel.py
======================
Права панель ФІЗИЧНОГО ДАМАГУ — Clash система.
Оновлено: вибір персонажів з дропдаунів, або ручне введення.
"""
import customtkinter as ctk
from core.melee_engine import calculate_clash_round
from ui.widgets import make_section_title, make_readonly_textbox, FONT_MONO

ACCENT = "#00f0ff"
WARN   = "#ffaa00"
PINK   = "#ff007f"


class ClashPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, data_manager, char_manager=None):
        self.dm = data_manager
        self.cm = char_manager

        self.scroll = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self._build()

    def set_char_manager(self, cm):
        self.cm = cm
        self._refresh_char_lists()

    # =========================================================================
    def _build(self):
        # Заголовок
        ctk.CTkLabel(self.scroll, text="02 // CLASH СИСТЕМА",
                     font=ctk.CTkFont(family=FONT_MONO, size=18, weight="bold"),
                     text_color=WARN).pack(anchor="w", padx=10, pady=(15, 5))
        ctk.CTkLabel(self.scroll,
                     text="Протистояння двох бійців. Шкала: -3 (поразка) до +3 (перемога).",
                     font=ctk.CTkFont(family=FONT_MONO, size=10),
                     text_color="#5f647d", wraplength=380, justify="left").pack(anchor="w", padx=10, pady=(0, 10))

        self._build_combatant("ГРАВЕЦЬ / АТАКУЮЧИЙ", side="player")
        self._build_combatant("ВОРОГ / ЗАХИСНИК", side="enemy")
        self._build_scale()
        self._build_log()
        self._build_controls()

    # ── Блок учасника (гравець або ворог) ──
    def _build_combatant(self, title: str, side: str):
        make_section_title(self.scroll, title,
                           color=ACCENT if side == "player" else "#ff5555")

        frame = ctk.CTkFrame(self.scroll, fg_color="#181929", corner_radius=8)
        frame.pack(fill="x", padx=10, pady=3)

        # Дропдаун персонажа
        row1 = ctk.CTkFrame(frame, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(row1, text="Персонаж:",
                     font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#787c99",
                     width=90, anchor="w").pack(side="left")
        cb = ctk.CTkComboBox(row1, values=["— вручну —"], width=200,
                              fg_color="#1e2030", border_color="#2f334d",
                              text_color="#c0caf5", corner_radius=6,
                              command=lambda v, s=side: self._on_char_select(v, s))
        cb.set("— вручну —")
        cb.pack(side="left", padx=5)

        # Модифікатор (авто або ручний)
        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(4, 10))
        ctk.CTkLabel(row2, text="Мод. Сили:",
                     font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#787c99",
                     width=90, anchor="w").pack(side="left")
        ent_mod = ctk.CTkEntry(row2, width=70, fg_color="#1e2030", border_color="#2f334d",
                                text_color=WARN, font=ctk.CTkFont(family=FONT_MONO, size=12))
        ent_mod.insert(0, "0")
        ent_mod.pack(side="left", padx=5)
        ctk.CTkLabel(row2, text="(ручне перекриття)",
                     font=ctk.CTkFont(family=FONT_MONO, size=9), text_color="#5f647d").pack(side="left", padx=5)

        row3 = ctk.CTkFrame(frame, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(row3, text="Сприйняття:",
                     font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#787c99",
                     width=90, anchor="w").pack(side="left")
        ent_wis = ctk.CTkEntry(row3, width=70, fg_color="#1e2030", border_color="#2f334d",
                                text_color="#a855f7", font=ctk.CTkFont(family=FONT_MONO, size=12))
        ent_wis.insert(0, "0")
        ent_wis.pack(side="left", padx=5)
        ctk.CTkLabel(row3, text="(+ до ініціативи)",
                     font=ctk.CTkFont(family=FONT_MONO, size=9), text_color="#5f647d").pack(side="left", padx=5)

        if side == "player":
            self.cb_player = cb
            self.ent_player_mod = ent_mod
            self.ent_player_wis = ent_wis
        else:
            self.cb_enemy = cb
            self.ent_enemy_mod = ent_mod
            self.ent_enemy_wis = ent_wis

        self._refresh_char_lists()

    def _on_char_select(self, val, side):
        if not self.cm or val == "— вручну —":
            return
        char = self.cm.get_by_name(val)
        if not char:
            return
        str_mod     = self.cm.modifier(char, "Сила")
        perception  = self.cm.skill_total(char, "Сприйняття")
        ent_str = self.ent_player_mod if side == "player" else self.ent_enemy_mod
        ent_wis = self.ent_player_wis if side == "player" else self.ent_enemy_wis
        ent_str.delete(0, ctk.END); ent_str.insert(0, str(str_mod))
        ent_wis.delete(0, ctk.END); ent_wis.insert(0, str(perception))

    def _refresh_char_lists(self):
        if not self.cm:
            return
        names = ["— вручну —"] + [c["name"] for c in self.cm.get_sorted()]
        for cb in [getattr(self, "cb_player", None), getattr(self, "cb_enemy", None)]:
            if cb:
                current = cb.get()
                cb.configure(values=names)
                if current not in names:
                    cb.set("— вручну —")

    # ── Шкала ──
    def _build_scale(self):
        make_section_title(self.scroll, "ШКАЛА PROTISTOYANYA", color=WARN)
        scale_f = ctk.CTkFrame(self.scroll, fg_color="#181929", corner_radius=8)
        scale_f.pack(fill="x", padx=10, pady=5)

        # Візуальна шкала (центрована, без дублюючого лейбла)
        self.scale_bar = ctk.CTkFrame(scale_f, fg_color="transparent")
        self.scale_bar.pack(anchor="center", pady=15)
        self._draw_scale_bar(0)

    def _draw_scale_bar(self, val: int):
        for w in self.scale_bar.winfo_children():
            w.destroy()
        labels = ["-3", "-2", "-1", "0", "+1", "+2", "+3"]
        colors_inactive = ["#ff5555", "#ff7744", "#ffaa44", "#444a73", "#44aaff", "#44ddaa", "#00f0ff"]
        for i, lbl in enumerate(labels):
            scale_val = i - 3
            is_active = scale_val == val
            if is_active:
                bg = WARN
                tc = "#000000"
                size = 18
                w_h = (58, 58)
            else:
                bg = "#1a1c2e"
                tc = colors_inactive[i]
                size = 12
                w_h = (44, 44)
            ctk.CTkButton(self.scale_bar, text=lbl, width=w_h[0], height=w_h[1],
                          fg_color=bg, text_color=tc, hover_color=bg,
                          font=ctk.CTkFont(family=FONT_MONO, size=size, weight="bold"),
                          corner_radius=6).pack(side="left", padx=3)

    # ── Лог ──
    def _build_log(self):
        make_section_title(self.scroll, "БОЙ-ЛОГ", color="#a9b1d6")
        self.txt_log = make_readonly_textbox(
            self.scroll, fg_color="#090a10",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color="#a9b1d6", height=180
        )
        self.txt_log.pack(fill="x", padx=10, pady=5)
        self.txt_log.insert("1.0", ">> Clash система готова. Введіть кидки нижче.\n")

    # ── Контроли раунду ──
    def _build_controls(self):
        ctrl = ctk.CTkFrame(self.scroll, fg_color="#181929", corner_radius=8)
        ctrl.pack(fill="x", padx=10, pady=10)

        # Кидки
        row = ctk.CTkFrame(ctrl, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(12, 5))

        ctk.CTkLabel(row, text="Кидок гравця (d20):",
                     font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#787c99").pack(side="left")
        self.ent_player_roll = ctk.CTkEntry(row, width=60, fg_color="#1e2030",
                                             border_color="#2f334d", text_color=ACCENT,
                                             font=ctk.CTkFont(family=FONT_MONO, size=13))
        self.ent_player_roll.pack(side="left", padx=8)

        ctk.CTkLabel(row, text="Кидок ворога (d20):",
                     font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#787c99").pack(side="left", padx=(15, 0))
        self.ent_enemy_roll = ctk.CTkEntry(row, width=60, fg_color="#1e2030",
                                            border_color="#2f334d", text_color="#ff5555",
                                            font=ctk.CTkFont(family=FONT_MONO, size=13))
        self.ent_enemy_roll.pack(side="left", padx=8)

        # Кнопки
        btn_row = ctk.CTkFrame(ctrl, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(5, 12))

        ctk.CTkButton(btn_row, text="⚔ РАУНД",
                      font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
                      fg_color=WARN, text_color="#000000", hover_color="#c48800",
                      height=42, command=self._action_round).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_row, text="↺ RESET",
                      font=ctk.CTkFont(family=FONT_MONO, size=12),
                      fg_color="#2a2b3d", text_color="#a9b1d6",
                      height=42, command=self._action_reset).pack(side="right", padx=(5, 0))

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def _get_mod(self, side: str) -> int:
        ent = self.ent_player_mod if side == "player" else self.ent_enemy_mod
        try:
            return int(ent.get().strip())
        except ValueError:
            return 0

    def _get_wis(self, side: str) -> int:
        ent = self.ent_player_wis if side == "player" else self.ent_enemy_wis
        try:
            return int(ent.get().strip())
        except ValueError:
            return 0

    def _action_round(self):
        try:
            p_roll = int(self.ent_player_roll.get().strip())
            e_roll = int(self.ent_enemy_roll.get().strip())
        except ValueError:
            self._log(">> ПОМИЛКА: Введіть числові значення кидків!\n")
            return

        p_mod = self._get_mod("player")
        e_mod = self._get_mod("enemy")
        p_wis = self._get_wis("player")
        e_wis = self._get_wis("enemy")
        p_total = p_roll + p_mod + p_wis
        e_total = e_roll + e_mod + e_wis

        result = calculate_clash_round(p_total, e_total)

        scale = self.dm.clash_state["scale"] + result["delta"]
        scale = max(-3, min(3, scale))
        self.dm.clash_state["scale"] = scale

        # Визначити імена
        p_name = self.cb_player.get() if self.cb_player.get() != "— вручну —" else "Гравець"
        e_name = self.cb_enemy.get() if self.cb_enemy.get() != "— вручну —" else "Ворог"

        p_parts = f"{p_roll}+STR{p_mod:+}+WIS{p_wis:+}={p_total}"
        e_parts = f"{e_roll}+STR{e_mod:+}+WIS{e_wis:+}={e_total}"
        log = (
            f"► {p_name} [{p_parts}]  vs  {e_name} [{e_parts}]\n"
            f"  {result['desc']}\n"
            f"  Шкала: {scale:+d}\n"
        )
        if abs(scale) == 3:
            winner = p_name if scale > 0 else e_name
            log += f"  ★★★ ФІНАЛ! {winner.upper()} ПЕРЕМАГАЄ!\n"

        self.dm.push_clash_log(log)
        self._log(log)
        self._draw_scale_bar(scale)

        # Очистити кидки
        for ent in [self.ent_player_roll, self.ent_enemy_roll]:
            ent.delete(0, ctk.END)

    def _action_reset(self):
        self.dm.reset_clash()
        self._draw_scale_bar(0)
        self.txt_log.delete("1.0", ctk.END)
        self.txt_log.insert("1.0", ">> Clash скинуто. Новий бій!\n")

    def _log(self, text: str):
        self.txt_log.insert(ctk.END, text)
        self.txt_log.see(ctk.END)