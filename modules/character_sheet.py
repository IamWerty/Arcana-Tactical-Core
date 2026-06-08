"""
modules/character_sheet.py
==========================
Бланк персонажа — повний перегляд + редагування.
"""
import customtkinter as ctk
from ui.widgets import FONT_MONO
from core.character_manager import (
    STAT_NAMES, SKILLS, CharacterManager, stat_modifier
)

ACCENT = "#00f0ff"
WARN   = "#ffaa00"
PINK   = "#ff007f"
PURPLE = "#a855f7"


class CharacterSheet:
    def __init__(self, parent_frame: ctk.CTkFrame, cm: CharacterManager):
        self.cm = cm
        self.char_id: str | None = None
        self._entries: dict = {}

        self.scroll = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(
            self.scroll, text="// ОБЕРІТЬ ПЕРСОНАЖА\n// АБО СТВОРІТЬ НОВОГО",
            font=ctk.CTkFont(family=FONT_MONO, size=14), text_color="#3a3c52"
        ).pack(expand=True, pady=100)

    # =========================================================================
    # LOAD / REBUILD
    # =========================================================================
    def load(self, char_id: str):
        self.char_id = char_id
        self._rebuild()

    def _rebuild(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._entries = {}
        char = self.cm.get_by_id(self.char_id)
        if not char:
            return
        self._build_sheet(char)

    # =========================================================================
    # TOP-LEVEL BUILD
    # =========================================================================
    def _build_sheet(self, char: dict):
        s = self.scroll
        self._build_header(s, char)
        self._build_combat_stats(s, char)
        self._build_stats(s, char)          # Характеристики + авто-модифікатори
        self._build_skills(s, char)
        self._build_class_section(s, char)
        self._build_inventory(s, char)

    # ── Заголовок ──
    def _build_header(self, parent, char: dict):
        hdr = ctk.CTkFrame(parent, fg_color="#181929", corner_radius=8)
        hdr.pack(fill="x", padx=5, pady=(5, 3))

        # Кнопка зірочки (пункт 4 ТЗ — миттєва зміна)
        is_player = char.get("is_player", True)
        star_btn = ctk.CTkButton(
            hdr,
            text="★ Гравець" if is_player else "○ НПС",
            width=90, height=28, corner_radius=4,
            fg_color="#2a3a2a" if is_player else "#2a2a3a",
            hover_color="#3a4a3a" if is_player else "#3a3a4a",
            text_color=WARN if is_player else "#5f647d",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            command=self._toggle_player_type
        )
        star_btn.pack(side="right", padx=10, pady=8)
        self._entries["_star_btn"] = star_btn

        ctk.CTkLabel(hdr, text=f"{char['name'].upper()}",
                     font=ctk.CTkFont(family=FONT_MONO, size=20, weight="bold"),
                     text_color=ACCENT).pack(side="left", padx=15, pady=10)
        ctk.CTkLabel(hdr, text=f"{char['race']}  •  {char['char_class']}",
                     font=ctk.CTkFont(family=FONT_MONO, size=12),
                     text_color="#787c99").pack(side="left", padx=5)

    # ── Бойові характеристики ──
    def _build_combat_stats(self, parent, char: dict):
        section = self._section(parent, "⚔  БОЙОВІ ХАРАКТЕРИСТИКИ")
        ini = self.cm.initiative(char)
        magic_ac = char.get("ac", 10) + self.cm.modifier(char, "Мудрість")

        fields = [
            ("Рівень",          "level",             str(char["level"]),            False),
            ("HP Макс",         "hp_max",             str(char["hp_max"]),           False),
            ("HP Поточне",      "hp_current",         str(char["hp_current"]),       False),
            ("КД",              "ac",                 str(char["ac"]),               False),
            ("КД vs Магія",     "_magic_ac",          str(magic_ac),                 True),
            ("Ініціатива",      "_initiative",        f"{ini:+}",                    True),
            ("Швидкість (фут)", "speed",              str(char["speed"]),            False),
            ("Золото (gp)",     "gold",               str(char["gold"]),             False),
            ("Ліміт пулів",     "pool_limit",         str(char.get("pool_limit",10)),False),
        ]
        grid = ctk.CTkFrame(section, fg_color="transparent")
        grid.pack(fill="x", padx=5, pady=5)
        for i, (label, key, val, readonly) in enumerate(fields):
            col = (i % 4) * 2
            row = i // 4
            ctk.CTkLabel(grid, text=label,
                         font=ctk.CTkFont(family=FONT_MONO, size=10),
                         text_color="#5f647d", anchor="w").grid(
                row=row*2, column=col, padx=(8, 2), pady=(6, 0), sticky="w")
            ent = ctk.CTkEntry(grid, width=80, fg_color="#1e2030",
                               border_color="#2f334d", text_color="#c0caf5",
                               font=ctk.CTkFont(family=FONT_MONO, size=12), corner_radius=4)
            ent.insert(0, val)
            ent.grid(row=row*2+1, column=col, padx=(8, 2), pady=(0, 4), sticky="w")
            if readonly:
                tc = PURPLE if key == "_magic_ac" else ACCENT
                ent.configure(state="disabled", text_color=tc, border_color=tc)
            else:
                ent.bind("<FocusOut>", lambda e, k=key: self._on_combat_field(k, e.widget.get()))
            self._entries[key] = ent

    def _on_combat_field(self, key: str, val: str):
        char = self.cm.get_by_id(self.char_id)
        if not char:
            return
        try:
            if key == "pool_limit":
                char[key] = float(val)
            else:
                char[key] = int(val)
            self.cm.save_characters()
            # Оновлюємо авторозрахункові поля
            ini = self.cm.initiative(char)
            magic_ac = char.get("ac", 10) + self.cm.modifier(char, "Мудрість")
            if "_initiative" in self._entries:
                e = self._entries["_initiative"]
                e.configure(state="normal")
                e.delete(0, ctk.END); e.insert(0, f"{ini:+}")
                e.configure(state="disabled")
            if "_magic_ac" in self._entries:
                e = self._entries["_magic_ac"]
                e.configure(state="normal")
                e.delete(0, ctk.END); e.insert(0, str(magic_ac))
                e.configure(state="disabled")
        except ValueError:
            pass

    # ── Характеристики (пункти 5, 6, 7) ──
    def _build_stats(self, parent, char: dict):
        section = self._section(parent, "🎲  МОДИФІКАТОРИ ХАРАКТЕРИСТИК")

        # Заголовок колонок
        hdr = ctk.CTkFrame(section, fg_color="#1a1c2e", corner_radius=0)
        hdr.pack(fill="x", padx=8, pady=(4, 0))
        for txt, w in [("Характеристика", 130), ("Знач.", 55), ("Бонус", 55), ("Мод.", 55)]:
            ctk.CTkLabel(hdr, text=txt, width=w,
                         font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                         text_color="#5f647d").pack(side="left", padx=4, pady=3)

        for stat in STAT_NAMES:
            s_data = char.get("stats", {}).get(stat, {"value": 10, "bonus": 0})
            value  = s_data.get("value", 10)
            bonus  = s_data.get("bonus", 0)
            mod    = stat_modifier(value) + bonus

            row = ctk.CTkFrame(section, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=1)

            ctk.CTkLabel(row, text=stat, width=130,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         text_color="#c0caf5", anchor="w").pack(side="left", padx=4)

            # Значення
            ent_val = ctk.CTkEntry(row, width=55, fg_color="#1e2030",
                                   border_color="#2f334d", text_color="#a9e3ff",
                                   font=ctk.CTkFont(family=FONT_MONO, size=12), corner_radius=4)
            ent_val.insert(0, str(value))
            ent_val.pack(side="left", padx=4)

            # Бонус кампанії
            ent_bonus = ctk.CTkEntry(row, width=55, fg_color="#1e2030",
                                     border_color="#2f334d", text_color=WARN,
                                     font=ctk.CTkFont(family=FONT_MONO, size=12), corner_radius=4)
            ent_bonus.insert(0, str(bonus))
            ent_bonus.pack(side="left", padx=4)

            # Авто-модифікатор (readonly)
            lbl_mod = ctk.CTkEntry(row, width=55, fg_color="#0f1018",
                                   border_color=ACCENT, text_color=ACCENT,
                                   font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
                                   corner_radius=4, state="disabled")
            lbl_mod.configure(state="normal")
            lbl_mod.insert(0, f"{mod:+}")
            lbl_mod.configure(state="disabled")
            lbl_mod.pack(side="left", padx=4)

            # Прив'язуємо оновлення
            def _on_stat_change(e, s=stat, ev=ent_val, eb=ent_bonus, lm=lbl_mod):
                self._save_stat_row(s, ev, eb, lm)

            ent_val.bind("<FocusOut>",   _on_stat_change)
            ent_bonus.bind("<FocusOut>", _on_stat_change)

            self._entries[f"stat_val_{stat}"]   = ent_val
            self._entries[f"stat_bonus_{stat}"] = ent_bonus
            self._entries[f"stat_mod_{stat}"]   = lbl_mod

    def _save_stat_row(self, stat: str, ent_val, ent_bonus, lbl_mod):
        char = self.cm.get_by_id(self.char_id)
        if not char:
            return
        try:
            v = int(ent_val.get().strip())
            b = int(ent_bonus.get().strip())
        except ValueError:
            return
        char.setdefault("stats", {})[stat] = {"value": v, "bonus": b}
        mod = stat_modifier(v) + b
        lbl_mod.configure(state="normal")
        lbl_mod.delete(0, ctk.END)
        lbl_mod.insert(0, f"{mod:+}")
        lbl_mod.configure(state="disabled")
        self.cm.save_characters()

        # Оновлюємо ініціативу якщо змінилась Ловкість
        if stat == "Ловкість" and "_initiative" in self._entries:
            ini = self.cm.initiative(char)
            e = self._entries["_initiative"]
            e.configure(state="normal")
            e.delete(0, ctk.END); e.insert(0, f"{ini:+}")
            e.configure(state="disabled")
        # Оновлюємо КД vs Магія якщо змінилась Мудрість
        if stat == "Мудрість" and "_magic_ac" in self._entries:
            magic_ac = char.get("ac", 10) + self.cm.modifier(char, "Мудрість")
            e = self._entries["_magic_ac"]
            e.configure(state="normal")
            e.delete(0, ctk.END); e.insert(0, str(magic_ac))
            e.configure(state="disabled")

    # ── Навики (пункт 5) ──
    def _build_skills(self, parent, char: dict):
        section = self._section(parent, "📋  НАВИКИ")

        # Заголовок
        hdr = ctk.CTkFrame(section, fg_color="#1a1c2e", corner_radius=0)
        hdr.pack(fill="x", padx=8, pady=(4, 0))
        for txt, w in [("Навичка", 140), ("Бонус", 55), ("Разом", 55)]:
            ctk.CTkLabel(hdr, text=txt, width=w,
                         font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                         text_color="#5f647d").pack(side="left", padx=4, pady=3)

        for stat, skill_list in SKILLS.items():
            if not skill_list:
                continue
            ctk.CTkLabel(section, text=stat.upper(),
                         font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                         text_color=WARN).pack(anchor="w", padx=12, pady=(8, 2))

            for skill in skill_list:
                bonus = char.get("skills", {}).get(skill, 0)
                total = self.cm.skill_total(char, skill)

                row = ctk.CTkFrame(section, fg_color="transparent")
                row.pack(fill="x", padx=8, pady=1)

                ctk.CTkLabel(row, text=skill, width=140,
                             font=ctk.CTkFont(family=FONT_MONO, size=11),
                             text_color="#c0caf5", anchor="w").pack(side="left", padx=4)

                ent_bonus = ctk.CTkEntry(row, width=55, fg_color="#1e2030",
                                         border_color="#2f334d", text_color="#c0caf5",
                                         font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=4)
                ent_bonus.insert(0, str(bonus))
                ent_bonus.pack(side="left", padx=4)

                lbl_total = ctk.CTkEntry(row, width=55, fg_color="#0f1018",
                                          border_color=PINK, text_color=PINK,
                                          font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                                          corner_radius=4, state="disabled")
                lbl_total.configure(state="normal")
                lbl_total.insert(0, f"{total:+}")
                lbl_total.configure(state="disabled")
                lbl_total.pack(side="left", padx=4)

                def _on_skill(e, sk=skill, eb=ent_bonus, lt=lbl_total):
                    self._save_skill_row(sk, eb, lt)

                ent_bonus.bind("<FocusOut>", _on_skill)
                self._entries[f"skill_{skill}"] = ent_bonus
                self._entries[f"skill_total_{skill}"] = lbl_total

    def _save_skill_row(self, skill: str, ent_bonus, lbl_total):
        char = self.cm.get_by_id(self.char_id)
        if not char:
            return
        try:
            b = int(ent_bonus.get().strip())
        except ValueError:
            return
        char.setdefault("skills", {})[skill] = b
        total = self.cm.skill_total(char, skill)
        lbl_total.configure(state="normal")
        lbl_total.delete(0, ctk.END)
        lbl_total.insert(0, f"{total:+}")
        lbl_total.configure(state="disabled")
        self.cm.save_characters()

    # ── Клас-специфічне ──
    def _build_class_section(self, parent, char: dict):
        cls = char.get("char_class")
        if cls == "Маг":
            self._build_wizard_section(parent, char)
        self._build_weapon_section(parent, char)   # у всіх

    def _build_wizard_section(self, parent, char: dict):
        section = self._section(parent, "🔮  КЛАС: МАГ", color=ACCENT)
        self._kd_row(section, char)

        ctk.CTkLabel(section, text="БАТАРЕЙКИ (Аркана)",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color=ACCENT).pack(anchor="w", padx=12, pady=(10, 3))
        self._bat_container = ctk.CTkFrame(section, fg_color="#1a1c2e", corner_radius=6)
        self._bat_container.pack(fill="x", padx=8, pady=3)
        self._refresh_batteries(char)

        add_bat_f = ctk.CTkFrame(section, fg_color="transparent")
        add_bat_f.pack(fill="x", padx=8, pady=5)
        self._ent_bat_name = ctk.CTkEntry(add_bat_f, placeholder_text="Ім'я батарейки...",
                                           width=140, fg_color="#1e2030", border_color="#2f334d",
                                           text_color="#c0caf5", font=ctk.CTkFont(size=11))
        self._ent_bat_name.pack(side="left", padx=3)
        self._ent_bat_cap = ctk.CTkEntry(add_bat_f, placeholder_text="Місткість", width=80,
                                          fg_color="#1e2030", border_color="#2f334d",
                                          text_color="#c0caf5", font=ctk.CTkFont(size=11))
        self._ent_bat_cap.pack(side="left", padx=3)
        ctk.CTkButton(add_bat_f, text="+ Батарейка", width=100, height=28,
                      fg_color="#2f334d", hover_color="#444a73",
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      command=self._add_battery).pack(side="left", padx=5)

        ctk.CTkLabel(section, text="КНИГА ЗАКЛИНАНЬ",
                     font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                     text_color=PINK).pack(anchor="w", padx=12, pady=(12, 3))
        self._spell_container = ctk.CTkFrame(section, fg_color="#1a1c2e", corner_radius=6)
        self._spell_container.pack(fill="x", padx=8, pady=3)
        self._refresh_spellbook(char)

        add_spell_f = ctk.CTkFrame(section, fg_color="transparent")
        add_spell_f.pack(fill="x", padx=8, pady=5)
        self._ent_spell_name = ctk.CTkEntry(add_spell_f, placeholder_text="Назва заклинання...",
                                             width=160, fg_color="#1e2030", border_color="#2f334d",
                                             text_color="#c0caf5", font=ctk.CTkFont(size=11))
        self._ent_spell_name.pack(side="left", padx=3)
        ctk.CTkButton(add_spell_f, text="+ Вивчити", width=90, height=28,
                      fg_color="#ff007f", hover_color="#c90062",
                      font=ctk.CTkFont(family=FONT_MONO, size=10),
                      command=self._learn_spell).pack(side="left", padx=5)

    def _build_weapon_section(self, parent, char: dict):
        """Зброя є у всіх — для мага необов'язкова (може бути порожньою)."""
        cls = char.get("char_class")
        title = "⚔  ЗБРОЯ (запасна)" if cls == "Маг" else "⚔  КЛАС: МЕЧНИК"
        color = "#5f647d" if cls == "Маг" else WARN
        section = self._section(parent, title, color=color)
        self._kd_row(section, char)

        row_f = ctk.CTkFrame(section, fg_color="transparent")
        row_f.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(row_f, text="Ім'я зброї:",
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#787c99").pack(side="left", padx=5)
        ent_wname = ctk.CTkEntry(row_f, width=160, fg_color="#1e2030",
                                  border_color="#2f334d", text_color="#c0caf5",
                                  font=ctk.CTkFont(family=FONT_MONO, size=12))
        ent_wname.insert(0, char.get("weapon_name", ""))
        ent_wname.pack(side="left", padx=5)
        ent_wname.bind("<FocusOut>", lambda e: self._save_field("weapon_name", e.widget.get()))

        ctk.CTkLabel(row_f, text="dK:", font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#787c99").pack(side="left", padx=10)
        ent_dk = ctk.CTkEntry(row_f, width=60, fg_color="#1e2030",
                               border_color="#2f334d", text_color="#ffaa00",
                               font=ctk.CTkFont(family=FONT_MONO, size=12))
        ent_dk.insert(0, str(char.get("weapon_dk", 6)))
        ent_dk.pack(side="left", padx=5)
        ent_dk.bind("<FocusOut>", lambda e: self._save_field_int("weapon_dk", e.widget.get()))

    # ── Інвентар ──
    def _build_inventory(self, parent, char: dict):
        section = self._section(parent, "🎒  ІНВЕНТАР")
        self._inv_container = ctk.CTkFrame(section, fg_color="#1a1c2e", corner_radius=6)
        self._inv_container.pack(fill="x", padx=8, pady=3)
        self._refresh_inventory(char)

        add_f = ctk.CTkFrame(section, fg_color="transparent")
        add_f.pack(fill="x", padx=8, pady=5)
        self._ent_item_name   = ctk.CTkEntry(add_f, placeholder_text="Предмет...", width=130,
                                              fg_color="#1e2030", border_color="#2f334d",
                                              text_color="#c0caf5", font=ctk.CTkFont(size=11))
        self._ent_item_name.pack(side="left", padx=2)
        self._ent_item_qty    = ctk.CTkEntry(add_f, placeholder_text="Кіл.", width=45,
                                              fg_color="#1e2030", border_color="#2f334d",
                                              text_color="#c0caf5", font=ctk.CTkFont(size=11))
        self._ent_item_qty.pack(side="left", padx=2)
        self._ent_item_weight = ctk.CTkEntry(add_f, placeholder_text="Вага", width=50,
                                              fg_color="#1e2030", border_color="#2f334d",
                                              text_color="#c0caf5", font=ctk.CTkFont(size=11))
        self._ent_item_weight.pack(side="left", padx=2)
        self._ent_item_cost   = ctk.CTkEntry(add_f, placeholder_text="Ціна (gp)", width=65,
                                              fg_color="#1e2030", border_color="#2f334d",
                                              text_color="#c0caf5", font=ctk.CTkFont(size=11))
        self._ent_item_cost.pack(side="left", padx=2)
        ctk.CTkButton(add_f, text="+", width=30, height=28, fg_color="#2f334d",
                      hover_color="#444a73", font=ctk.CTkFont(size=14),
                      command=self._add_item).pack(side="left", padx=5)

    # =========================================================================
    # REFRESH SUB-COMPONENTS
    # =========================================================================
    def _refresh_batteries(self, char: dict | None = None):
        if char is None:
            char = self.cm.get_by_id(self.char_id)
        for w in self._bat_container.winfo_children():
            w.destroy()
        bats = char.get("batteries", {})
        if not bats:
            ctk.CTkLabel(self._bat_container, text="// Батареї відсутні",
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         text_color="#3a3c52").pack(pady=8)
            return
        for name, info in bats.items():
            f = ctk.CTkFrame(self._bat_container, fg_color="#222538", corner_radius=4)
            f.pack(fill="x", pady=2, padx=4)
            pct = info["current"] / info["max"] if info["max"] > 0 else 0
            col = ACCENT if pct > 0.4 else WARN if pct > 0.15 else "#ff0055"
            ctk.CTkLabel(f, text=f"🔋 {name}",
                         font=ctk.CTkFont(family=FONT_MONO, size=11)).pack(side="left", padx=8)
            ctk.CTkLabel(f, text=f"{info['current']} / {info['max']}",
                         font=ctk.CTkFont(family=FONT_MONO, size=11), text_color=col).pack(side="left")
            def _del(b=name):
                c2 = self.cm.get_by_id(self.char_id)
                if b in c2.get("batteries", {}):
                    del c2["batteries"][b]
                    self.cm.save_characters()
                    self._refresh_batteries()
            ctk.CTkButton(f, text="✖", width=25, height=22, fg_color="transparent",
                          text_color="#ff5555", command=_del).pack(side="right", padx=5)

    def _refresh_spellbook(self, char: dict | None = None):
        if char is None:
            char = self.cm.get_by_id(self.char_id)
        for w in self._spell_container.winfo_children():
            w.destroy()
        all_spells = self.cm.get_all_spells()
        known = set(char.get("known_spells", []))
        if not all_spells:
            ctk.CTkLabel(self._spell_container, text="// Книга пуста",
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         text_color="#3a3c52").pack(pady=8)
            return
        for spell_name, data in all_spells.items():
            f = ctk.CTkFrame(self._spell_container, fg_color="#1d1f35", corner_radius=4)
            f.pack(fill="x", pady=1, padx=4)
            is_known = spell_name in known
            ctk.CTkLabel(f, text="●", text_color=ACCENT if is_known else "#3a3c52",
                         font=ctk.CTkFont(size=10)).pack(side="left", padx=5)
            ctk.CTkLabel(f, text=spell_name,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         text_color="#c0caf5" if is_known else "#5f647d").pack(side="left", padx=2)
            ctk.CTkLabel(f, text=f"[{data['game_formula']}]",
                         font=ctk.CTkFont(family=FONT_MONO, size=10),
                         text_color="#787c99").pack(side="left", padx=5)
            def _toggle(sn=spell_name):
                c = self.cm.get_by_id(self.char_id)
                kn = set(c.get("known_spells", []))
                kn.discard(sn) if sn in kn else kn.add(sn)
                c["known_spells"] = list(kn)
                self.cm.save_characters()
                self._refresh_spellbook()
            btn_text = "✖ Забути" if is_known else "+ Вивчити"
            ctk.CTkButton(f, text=btn_text, width=75, height=22,
                          fg_color="#3d2020" if is_known else "#1e2a1e",
                          font=ctk.CTkFont(size=10), command=_toggle).pack(side="right", padx=5)

    def _refresh_inventory(self, char: dict | None = None):
        if char is None:
            char = self.cm.get_by_id(self.char_id)
        for w in self._inv_container.winfo_children():
            w.destroy()
        items = char.get("inventory", [])
        if not items:
            ctk.CTkLabel(self._inv_container, text="// Інвентар порожній",
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         text_color="#3a3c52").pack(pady=8)
            return
        hf = ctk.CTkFrame(self._inv_container, fg_color="#2a2c40", corner_radius=0)
        hf.pack(fill="x")
        for txt, w in [("Предмет", 150), ("Кіл.", 40), ("Вага", 50), ("Ціна", 60)]:
            ctk.CTkLabel(hf, text=txt, width=w,
                         font=ctk.CTkFont(family=FONT_MONO, size=10),
                         text_color="#5f647d").pack(side="left", padx=4, pady=3)
        for idx, item in enumerate(items):
            f = ctk.CTkFrame(self._inv_container,
                             fg_color="#1d1f35" if idx % 2 == 0 else "#191a2a",
                             corner_radius=0)
            f.pack(fill="x")
            ctk.CTkLabel(f, text=item.get("name","?"), width=150,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         text_color="#c0caf5", anchor="w").pack(side="left", padx=4)
            ctk.CTkLabel(f, text=str(item.get("qty",1)), width=40,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         text_color="#a9b1d6").pack(side="left", padx=4)
            ctk.CTkLabel(f, text=str(item.get("weight","-")), width=50,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         text_color="#a9b1d6").pack(side="left", padx=4)
            ctk.CTkLabel(f, text=str(item.get("cost","-")), width=60,
                         font=ctk.CTkFont(family=FONT_MONO, size=11),
                         text_color="#ffaa00").pack(side="left", padx=4)
            def _del_item(i=idx):
                c = self.cm.get_by_id(self.char_id)
                c["inventory"].pop(i)
                self.cm.save_characters()
                self._refresh_inventory()
            ctk.CTkButton(f, text="✖", width=22, height=20, fg_color="transparent",
                          text_color="#ff5555", font=ctk.CTkFont(size=10),
                          command=_del_item).pack(side="right", padx=5)

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _section(self, parent, title: str, color: str = "#c0caf5") -> ctk.CTkFrame:
        ctk.CTkLabel(parent, text=title,
                     font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
                     text_color=color).pack(anchor="w", padx=10, pady=(14, 3))
        frame = ctk.CTkFrame(parent, fg_color="#181929", corner_radius=8)
        frame.pack(fill="x", padx=5, pady=3)
        return frame

    def _kd_row(self, parent, char: dict):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(f, text="КД (Клас захисту):",
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#787c99").pack(side="left", padx=5)
        ent = ctk.CTkEntry(f, width=80, fg_color="#1e2030", border_color=ACCENT,
                            text_color=ACCENT, font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"))
        ent.insert(0, str(char.get("ac", 10)))
        ent.pack(side="left", padx=5)
        ent.bind("<FocusOut>", lambda e: self._save_field_int("ac", e.widget.get()))

    def _save_field(self, key: str, val: str):
        char = self.cm.get_by_id(self.char_id)
        if char:
            char[key] = val
            self.cm.save_characters()

    def _save_field_int(self, key: str, val: str):
        char = self.cm.get_by_id(self.char_id)
        if char:
            try:
                char[key] = int(val)
                self.cm.save_characters()
            except ValueError:
                pass

    def _toggle_player_type(self):
        char = self.cm.get_by_id(self.char_id)
        if not char:
            return
        char["is_player"] = not char.get("is_player", True)
        self.cm.save_characters()
        btn = self._entries.get("_star_btn")
        if btn:
            is_p = char["is_player"]
            btn.configure(
                text="★ Гравець" if is_p else "○ НПС",
                fg_color="#2a3a2a" if is_p else "#2a2a3a",
                hover_color="#3a4a3a" if is_p else "#3a3a4a",
                text_color=WARN if is_p else "#5f647d"
            )

    def _add_battery(self):
        name = self._ent_bat_name.get().strip()
        cap_str = self._ent_bat_cap.get().strip()
        if not name or not cap_str:
            return
        try:
            cap = int(cap_str)
            char = self.cm.get_by_id(self.char_id)
            if char:
                char.setdefault("batteries", {})[name] = {"max": cap, "current": cap}
                self.cm.save_characters()
                self._ent_bat_name.delete(0, ctk.END)
                self._ent_bat_cap.delete(0, ctk.END)
                self._refresh_batteries()
        except ValueError:
            pass

    def _learn_spell(self):
        name = self._ent_spell_name.get().strip()
        if not name:
            return
        char = self.cm.get_by_id(self.char_id)
        if char:
            known = set(char.get("known_spells", []))
            known.add(name)
            char["known_spells"] = list(known)
            self.cm.save_characters()
            self._ent_spell_name.delete(0, ctk.END)
            self._refresh_spellbook()

    def _add_item(self):
        name = self._ent_item_name.get().strip()
        if not name:
            return
        qty_str    = self._ent_item_qty.get().strip()
        weight_str = self._ent_item_weight.get().strip()
        cost_str   = self._ent_item_cost.get().strip()
        item = {
            "name":   name,
            "qty":    int(qty_str) if qty_str.isdigit() else 1,
            "weight": float(weight_str) if weight_str else "-",
            "cost":   cost_str if cost_str else "-"
        }
        char = self.cm.get_by_id(self.char_id)
        if char:
            char.setdefault("inventory", []).append(item)
            self.cm.save_characters()
            for ent in [self._ent_item_name, self._ent_item_qty,
                        self._ent_item_weight, self._ent_item_cost]:
                ent.delete(0, ctk.END)
            self._refresh_inventory()
