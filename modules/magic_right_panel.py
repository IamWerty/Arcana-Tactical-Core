"""
modules/magic_right_panel.py
============================
Права панель МАГІЧНОГО ДАМАГУ.
Єдина книга заклинань — cm.get_all_spells() (data/spellbook.json).
Якщо активний маг — показуємо тільки вивчені ним заклинання;
кнопка "Всі" дозволяє побачити повний список.
"""
import math
from tkinter import messagebox
import customtkinter as ctk
from ui.widgets import make_section_title, FONT_MONO

ACCENT = "#00f0ff"
PINK   = "#ff007f"
WARN   = "#ffaa00"


class MagicRightPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, data_manager, char_manager=None):
        self.dm = data_manager
        self.cm = char_manager
        self._load_cb = None
        self._show_all_spells = False   # перемикач "вивчені / всі"

        self.scroll = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        self._build()

    def _build(self):
        self._build_char_selector()
        self._build_arcana_control()
        self._build_spellbook_section()
        self._build_active_spells_section()
        self._build_next_round_button()
        self.refresh_all()

    # ── Вибір мага ──
    def _build_char_selector(self):
        hdr = ctk.CTkFrame(self.scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(hdr, text="02 // АКТИВНИЙ МАГ",
                     font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
                     text_color=ACCENT).pack(side="left")
        self.cb_char = ctk.CTkComboBox(hdr, values=["— немає —"], width=200,
                                        fg_color="#1e2030", border_color="#2f334d",
                                        text_color="#c0caf5", corner_radius=6,
                                        command=self._on_char_change)
        self.cb_char.pack(side="right")

        # Бойові характеристики мага: INT + WIS (пункт 1 ТЗ)
        self.lbl_char_stats = ctk.CTkLabel(self.scroll, text="",
                                            font=ctk.CTkFont(family=FONT_MONO, size=11),
                                            text_color="#a855f7")
        self.lbl_char_stats.pack(anchor="w", padx=14, pady=(2, 0))

        # Загальна Аркана над батарейками
        self.lbl_arcana_total = ctk.CTkLabel(self.scroll, text="",
                                              font=ctk.CTkFont(family=FONT_MONO, size=11,
                                                               weight="bold"),
                                              text_color=ACCENT)
        self.lbl_arcana_total.pack(anchor="w", padx=14, pady=(2, 2))

        # Вертикальний прокручуваний список батарейок (пункт 1 ТЗ)
        self.bat_list_frame = ctk.CTkScrollableFrame(
            self.scroll, fg_color="#0f1018", corner_radius=6, height=80
        )
        self.bat_list_frame.pack(fill="x", padx=10, pady=(0, 5))

        # lbl_arcana — порожній, для зворотної сумісності з _apply_arcana_change
        self.lbl_arcana = ctk.CTkLabel(self.scroll, text="",
                                        font=ctk.CTkFont(family=FONT_MONO, size=1))
        self.lbl_arcana.pack()

        self._refresh_char_list()

    # ── Ручне керування Арканою ──
    def _build_arcana_control(self):
        make_section_title(self.scroll, "02.1 // РУЧНЕ КЕРУВАННЯ АРКАНОЮ", color=WARN)
        frame = ctk.CTkFrame(self.scroll, fg_color="#181929", corner_radius=8)
        frame.pack(fill="x", padx=10, pady=(0, 5))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(10, 4))

        ctk.CTkLabel(row, text="Батарейка:",
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#787c99", width=80, anchor="w").pack(side="left")
        self.cb_arcana_bat = ctk.CTkComboBox(
            row, values=["— немає —"], width=230,
            fg_color="#1e2030", border_color="#2f334d",
            text_color="#c0caf5", corner_radius=6
        )
        self.cb_arcana_bat.pack(side="left", padx=6)

        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=(4, 10))

        ctk.CTkLabel(row2, text="Кількість:",
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     text_color="#787c99", width=80, anchor="w").pack(side="left")
        self.ent_arcana_amount = ctk.CTkEntry(
            row2, width=90,
            fg_color="#1e2030", border_color="#2f334d",
            text_color=WARN, font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            corner_radius=6
        )
        self.ent_arcana_amount.insert(0, "10")
        self.ent_arcana_amount.pack(side="left", padx=6)

        ctk.CTkButton(
            row2, text="− Відняти", width=90, height=32,
            fg_color="#3d1a1a", text_color="#ff5555", hover_color="#5a1a1a",
            font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
            command=self._action_drain_manual
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            row2, text="+ Додати", width=90, height=32,
            fg_color="#1a3d1a", text_color="#44ff88", hover_color="#1a5a1a",
            font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold"),
            command=self._action_charge_manual
        ).pack(side="left", padx=4)

        self.lbl_arcana_feedback = ctk.CTkLabel(
            frame, text="",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color="#5f647d"
        )
        self.lbl_arcana_feedback.pack(anchor="w", padx=12, pady=(0, 8))

    def _refresh_arcana_bat_list(self):
        """Оновлює список батарейок у дропдауні ручного керування."""
        char = self._active_char()
        if char:
            bats = list(char.get("batteries", {}).keys())
        else:
            bats = list(self.dm.batteries.keys())
        values = bats if bats else ["— немає —"]
        current = self.cb_arcana_bat.get()
        self.cb_arcana_bat.configure(values=values)
        if current not in values:
            self.cb_arcana_bat.set(values[0])

    def _action_drain_manual(self):
        self._apply_arcana_change(drain=True)

    def _action_charge_manual(self):
        self._apply_arcana_change(drain=False)

    def _apply_arcana_change(self, drain: bool):
        try:
            amount = int(self.ent_arcana_amount.get().strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.lbl_arcana_feedback.configure(
                text="✖ Введіть ціле позитивне число", text_color="#ff5555")
            return

        bat_name = self.cb_arcana_bat.get()
        if bat_name == "— немає —":
            self.lbl_arcana_feedback.configure(
                text="✖ Оберіть батарейку", text_color="#ff5555")
            return

        char = self._active_char()
        if char:
            bats = char.get("batteries", {})
            if bat_name not in bats:
                return
            bat = bats[bat_name]
            if drain:
                actual = min(amount, bat["current"])
                bat["current"] = max(0, bat["current"] - amount)
                msg = f"− {actual} з [{bat_name}]  →  {bat['current']}/{bat['max']}"
                col = "#ff5555"
            else:
                space = bat["max"] - bat["current"]
                actual = min(amount, space)
                bat["current"] = min(bat["max"], bat["current"] + amount)
                msg = f"+ {actual} до [{bat_name}]  →  {bat['current']}/{bat['max']}"
                col = "#44ff88"
            self.cm.save_characters()
        else:
            bats = self.dm.batteries
            if bat_name not in bats:
                return
            bat = bats[bat_name]
            if drain:
                actual = min(amount, bat["current"])
                bat["current"] = max(0, bat["current"] - amount)
                msg = f"− {actual} з [{bat_name}]  →  {bat['current']}/{bat['max']}"
                col = "#ff5555"
            else:
                space = bat["max"] - bat["current"]
                actual = min(amount, space)
                bat["current"] = min(bat["max"], bat["current"] + amount)
                msg = f"+ {actual} до [{bat_name}]  →  {bat['current']}/{bat['max']}"
                col = "#44ff88"
            self.dm.save_to_json()

        self.lbl_arcana_feedback.configure(text=msg, text_color=col)
        self._update_arcana_label()

    # ── Книга заклинань ──
    def _build_spellbook_section(self):
        # Заголовок + перемикач "вивчені / всі"
        hdr = ctk.CTkFrame(self.scroll, fg_color="transparent")
        hdr.pack(fill="x", padx=10, pady=(10, 2))
        ctk.CTkLabel(hdr, text="03 // КНИГА ЗАКЛИНАНЬ",
                     font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
                     text_color=ACCENT).pack(side="left")
        self.btn_toggle_spells = ctk.CTkButton(
            hdr, text="Показати всі", width=110, height=26,
            fg_color="#1a1c2e", text_color="#787c99",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            command=self._toggle_spell_view
        )
        self.btn_toggle_spells.pack(side="right")

        self.spellbook_container = ctk.CTkFrame(self.scroll, fg_color="#1a1c2e", corner_radius=6)
        self.spellbook_container.pack(fill="x", padx=10, pady=5)

    def _toggle_spell_view(self):
        self._show_all_spells = not self._show_all_spells
        label = "Тільки вивчені" if self._show_all_spells else "Показати всі"
        self.btn_toggle_spells.configure(text=label)
        self.refresh_spellbook()

    # ── Активні заклинання ──
    def _build_active_spells_section(self):
        make_section_title(self.scroll, "04 // ACTIVE SUSTAINED SPELLS", color=PINK)
        self.active_container = ctk.CTkFrame(self.scroll, fg_color="#1a1c2e", corner_radius=6)
        self.active_container.pack(fill="x", padx=10, pady=5)

    def _build_next_round_button(self):
        self.btn_next_round = ctk.CTkButton(
            self.scroll,
            text="Н Е К С Т  -  Р А У Н Д  (Підтримка заклинань)",
            font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            fg_color=ACCENT, text_color="#000000", hover_color="#00b8c4",
            height=48, corner_radius=8, command=self._action_next_round
        )
        self.btn_next_round.pack(fill="x", padx=10, pady=25)

    # ── refresh ──
    def refresh_all(self):
        self._refresh_char_list()
        self._refresh_arcana_bat_list()
        self.refresh_spellbook()
        self.refresh_active_spells()

    def _refresh_char_list(self):
        if not self.cm:
            self.cb_char.configure(values=["— немає —"])
            self.cb_char.set("— немає —")
            return
        mages = [c["name"] for c in self.cm.get_sorted() if c["char_class"] == "Маг"]
        values = mages if mages else ["— немає —"]
        current = self.cb_char.get()
        self.cb_char.configure(values=values)
        if current not in values:
            self.cb_char.set(values[0])
        self._update_arcana_label()

    def _on_char_change(self, val):
        self._update_arcana_label()
        self._refresh_arcana_bat_list()
        self.lbl_arcana_feedback.configure(text="")
        self.refresh_spellbook()
        self.refresh_active_spells()

    def _update_arcana_label(self):
        char = self._active_char()

        # Очищуємо вертикальний список батарейок
        for w in self.bat_list_frame.winfo_children():
            w.destroy()

        if not char:
            self.lbl_char_stats.configure(text="")
            self.lbl_arcana_total.configure(text="")
            return

        # INT + WIS над батарейками (пункт 1 ТЗ)
        if self.cm:
            int_mod = self.cm.modifier(char, "Інтелект")
            wis_mod = self.cm.modifier(char, "Мудрість")
            arcana_sk = self.cm.skill_total(char, "Аркани")
            self.lbl_char_stats.configure(
                text=f"INT {int_mod:+}  |  WIS {wis_mod:+}  |  Аркани {arcana_sk:+}"
            )

        # Загальна Аркана
        bats = char.get("batteries", {})
        total = sum(b["current"] for b in bats.values())
        self.lbl_arcana_total.configure(
            text=f"Загальна Аркана: {total}" if bats else "Немає батарейок"
        )

        # Вертикальний список батарейок (пункт 1 ТЗ)
        if not bats:
            ctk.CTkLabel(self.bat_list_frame, text="// Немає батарейок",
                         font=ctk.CTkFont(family=FONT_MONO, size=10),
                         text_color="#3a3c52").pack(anchor="w", padx=8, pady=4)
            return
        for name, b in bats.items():
            pct = b["current"] / b["max"] if b["max"] > 0 else 0
            col = ACCENT if pct > 0.4 else WARN if pct > 0.15 else "#ff0055"
            row = ctk.CTkFrame(self.bat_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"🔋 {name}",
                         font=ctk.CTkFont(family=FONT_MONO, size=10),
                         text_color="#c0caf5").pack(side="left", padx=6)
            ctk.CTkLabel(row, text=f"{b['current']} / {b['max']}",
                         font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                         text_color=col).pack(side="right", padx=6)

    def _active_char(self):
        if not self.cm:
            return None
        return self.cm.get_by_name(self.cb_char.get())

    def refresh_spellbook(self):
        for w in self.spellbook_container.winfo_children():
            w.destroy()

        if not self.cm:
            self._spellbook_empty("// CharacterManager не підключений")
            return

        all_spells = self.cm.get_all_spells()
        if not all_spells:
            self._spellbook_empty("// Книга заклинань порожня.\n// Збережіть руну в Калькуляторі.")
            return

        char = self._active_char()
        if char and not self._show_all_spells:
            # Показуємо тільки вивчені
            known = set(char.get("known_spells", []))
            spells_to_show = {k: v for k, v in all_spells.items() if k in known}
            if not spells_to_show:
                self._spellbook_empty(
                    "// Маг не вивчив жодного заклинання.\n"
                    "// Натисніть 'Показати всі' або відкрийте бланк персонажа."
                )
                return
        else:
            spells_to_show = all_spells

        for name, data in spells_to_show.items():
            frame = ctk.CTkFrame(self.spellbook_container, fg_color="#222538", corner_radius=4)
            frame.pack(fill="x", pady=2, padx=5)

            # Мітка "вивчено" якщо є активний маг
            if char:
                known = set(char.get("known_spells", []))
                dot_col = ACCENT if name in known else "#3a3c52"
                ctk.CTkLabel(frame, text="●", text_color=dot_col,
                             font=ctk.CTkFont(size=9)).pack(side="left", padx=(6, 2))

            ctk.CTkLabel(frame,
                         text=f"✨ {name}  [{data['game_formula']}]  — {data['A_total']} ед.",
                         font=ctk.CTkFont(family=FONT_MONO, size=11)).pack(side="left", padx=6, pady=6)

            # Кнопка "Завантажити у калькулятор"
            if self._load_cb:
                ctk.CTkButton(frame, text="👁️", width=30, height=24, fg_color="#3d4466",
                              command=lambda d=data: self._load_cb(d)).pack(side="right", padx=2)

            # Кнопка "Кастанути"
            ctk.CTkButton(frame, text="КАСТАНУТИ", width=90, height=24,
                          fg_color=PINK, font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                          command=lambda n=name, d=data: self._action_activate_spell(n, d)
                          ).pack(side="right", padx=2)

    def _spellbook_empty(self, msg: str):
        ctk.CTkLabel(self.spellbook_container, text=msg,
                     font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#5f647d",
                     wraplength=320, justify="left").pack(pady=15, padx=10)

    def refresh_templates(self):
        """Аліас для зворотної сумісності — викликається після збереження шаблона."""
        self.refresh_spellbook()

    def refresh_active_spells(self):
        for w in self.active_container.winfo_children():
            w.destroy()
        char = self._active_char()
        spells = char.get("active_spells", []) if char else self.dm.active_spells
        if not spells:
            ctk.CTkLabel(self.active_container, text="// Немає активних підтримуваних рун",
                         font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#5f647d").pack(pady=20)
            return
        for idx, spell in enumerate(spells):
            frame = ctk.CTkFrame(self.active_container, fg_color="#1d2d3d",
                                 border_width=1, border_color=ACCENT, corner_radius=6)
            frame.pack(fill="x", pady=3, padx=5)
            desc = (f"🔷 {spell['name'].upper()} | [{spell.get('battery','?')}]\n"
                    f"   {spell.get('formula','?')} | -{spell.get('maintenance','?')} ед./раунд")
            ctk.CTkLabel(frame, text=desc,
                         font=ctk.CTkFont(family=FONT_MONO, size=11), justify="left").pack(side="left", padx=10, pady=6)

            def _deact(i=idx, c=char):
                if c:
                    c["active_spells"].pop(i)
                    self.cm.save_characters()
                else:
                    self.dm.active_spells.pop(i)
                    self.dm.save_to_json()
                self.refresh_active_spells()

            ctk.CTkButton(frame, text="ВІДКЛЮЧИТИ", width=90, height=25,
                          fg_color="#2b3047", hover_color="#ff5555", text_color="#ff5555",
                          font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                          command=_deact).pack(side="right", padx=10)

    # ── bind ──
    def bind_load_template_callback(self, callback):
        self._load_cb = callback
        self.refresh_spellbook()

    def set_char_manager(self, cm):
        self.cm = cm
        self.refresh_all()

    # ── actions ──
    def _action_activate_spell(self, spell_name, data):
        char = self._active_char()
        if char:
            bats = char.get("batteries", {})
            if not bats:
                messagebox.showerror("Помилка", f"У {char['name']} немає батарейок!")
                return
            self._show_cast_dialog(spell_name, data, bats,
                                   on_cast=lambda b, c2, m: self._cast_from_char(char, b, c2, m, spell_name, data))
        else:
            bats = self.dm.batteries
            if not bats:
                messagebox.showerror("Помилка", "Немає доступних батарейок!")
                return
            self._show_cast_dialog(spell_name, data, bats,
                                   on_cast=lambda b, c2, m: self._cast_from_dm(b, c2, m, spell_name, data))

    def _show_cast_dialog(self, spell_name, data, batteries, on_cast):
        char = self._active_char()
        int_mod    = char.get("stats", {}).get("Інтелект", {}).get("value", 10) if char else 10
        arcana_bonus = self.cm.skill_total(char, "Аркани") if (char and self.cm) else 0
        int_modifier = self.cm.modifier(char, "Інтелект") if (char and self.cm) else 0

        base_cost   = data["A_total"]
        actual_cost = max(1, base_cost - int_modifier)
        orig_formula = data.get("game_formula", "?")

        # Формула урону з бонусом Аркани (пункт 1 ТЗ)
        if arcana_bonus != 0:
            sign = "+" if arcana_bonus > 0 else "-"
            display_formula = f"{orig_formula} {sign} {abs(arcana_bonus)} (Аркани)"
        elif int_modifier != 0:
            sign = "+" if int_modifier > 0 else "-"
            display_formula = f"{orig_formula} {sign} {abs(int_modifier)} (INT)"
        else:
            display_formula = orig_formula

        win = ctk.CTkToplevel()
        win.title("ВИБІР ДЖЕРЕЛА")
        win.geometry("420x270")
        win.grab_set()
        win.configure(fg_color="#0d0e15")
        info = (f"Активація: {spell_name}\n"
                f"Базова вартість: {base_cost} Аркани\n"
                f"Мод. Інтелекту: {int_modifier:+}\n"
                f"Фактична вартість: {actual_cost} Аркани\n"
                f"Бонус навички Аркани: {arcana_bonus:+}\n"
                f"Дамаг: {display_formula}")
        ctk.CTkLabel(win, text=info,
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     justify="left").pack(pady=10, padx=15, anchor="w")
        cb = ctk.CTkComboBox(win, values=list(batteries.keys()), width=280,
                              fg_color="#1e2030", border_color="#2f334d", text_color="#c0caf5")
        cb.pack(pady=5)

        def confirm():
            bat = cb.get()
            maint = max(1, math.ceil(actual_cost * 0.10))
            on_cast(bat, actual_cost, maint)
            win.destroy()

        ctk.CTkButton(win, text="КАСТАНУТИ", fg_color=ACCENT, text_color="#000000",
                      command=confirm).pack(pady=10)

    def _cast_from_char(self, char, bat, cost, maint, spell_name, data):
        if char["batteries"][bat]["current"] < cost:
            messagebox.showerror("Відмова", "Недостатньо заряду!")
            return
        char["batteries"][bat]["current"] -= cost
        char.setdefault("active_spells", []).append({
            "name": spell_name, "cost": cost, "battery": bat,
            "maintenance": maint, "formula": data["game_formula"]
        })
        self.cm.save_characters()
        self._update_arcana_label()
        self.refresh_active_spells()

    def _cast_from_dm(self, bat, cost, maint, spell_name, data):
        if self.dm.batteries[bat]["current"] < cost:
            messagebox.showerror("Відмова", "Недостатньо заряду!")
            return
        self.dm.batteries[bat]["current"] -= cost
        self.dm.active_spells.append({
            "name": spell_name, "cost": cost, "battery": bat,
            "maintenance": maint, "formula": data["game_formula"]
        })
        self.dm.save_to_json()
        self.refresh_active_spells()

    def _action_next_round(self):
        char = self._active_char()
        if char:
            logs = self.cm.next_round_for_char(char["id"])
        else:
            logs = []
            for spell in list(self.dm.active_spells):
                bat = spell["battery"]
                maint = spell["maintenance"]
                if bat in self.dm.batteries:
                    if self.dm.batteries[bat]["current"] >= maint:
                        self.dm.batteries[bat]["current"] -= maint
                        logs.append(f"• '{spell['name']}' утримано. -{maint}")
                    else:
                        logs.append(f"• !!! '{spell['name']}' розсіялась!")
                        self.dm.active_spells.remove(spell)
            self.dm.save_to_json()
        self._update_arcana_label()
        self.refresh_active_spells()
        if logs:
            messagebox.showinfo("ФАЗА ЗАВЕРШЕНА", "\n".join(logs))
