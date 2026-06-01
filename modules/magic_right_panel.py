"""
modules/magic_right_panel.py
============================
Права панель для режиму МАГІЧНИЙ ДАМАГ.
Вміст: Слоти батарейок / Банк спелів / Активні підтримувані руни / Next Round.

Отримує посилання на DataManager і батьківський CTkFrame.
"""
import math
from tkinter import messagebox
import customtkinter as ctk
from ui.widgets import make_section_title, FONT_MONO


class MagicRightPanel:
    def __init__(self, parent_frame: ctk.CTkFrame, data_manager):
        self.dm = data_manager

        self.scroll = ctk.CTkScrollableFrame(parent_frame, fg_color="transparent", corner_radius=0)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self._build()

    # =========================================================================
    # ПОБУДОВА СЕКЦІЙ
    # =========================================================================
    def _build(self):
        self._build_batteries_section()
        self._build_spell_bank_section()
        self._build_active_spells_section()
        self._build_next_round_button()

        self.refresh_all()

    def _build_batteries_section(self):
        # --- Заголовок + поля для додавання ---
        title_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(title_frame, text="02 // СЛОТИ БАТАРЕЙОК",
                     font=ctk.CTkFont(family=FONT_MONO, size=14, weight="bold"),
                     text_color="#00f0ff").pack(side="left")

        self.ent_bat_name = ctk.CTkEntry(title_frame, placeholder_text="Ім'я...", width=100,
                                          font=ctk.CTkFont(size=11))
        self.ent_bat_name.pack(side="left", padx=5)
        self.ent_bat_cap = ctk.CTkEntry(title_frame, placeholder_text="Місткість", width=60,
                                         font=ctk.CTkFont(size=11))
        self.ent_bat_cap.pack(side="left", padx=2)
        ctk.CTkButton(title_frame, text="+", width=30, fg_color="#2f334d", hover_color="#444a73",
                      command=self._action_add_battery).pack(side="left", padx=5)

        self.bat_container = ctk.CTkFrame(self.scroll, fg_color="#1a1c2e", corner_radius=6)
        self.bat_container.pack(fill="x", padx=10, pady=5)

    def _build_spell_bank_section(self):
        make_section_title(self.scroll, "03 // SPELL CONFIG BANK (ШАБЛОНИ)")
        self.templates_container = ctk.CTkFrame(self.scroll, fg_color="#1a1c2e", corner_radius=6)
        self.templates_container.pack(fill="x", padx=10, pady=5)

    def _build_active_spells_section(self):
        make_section_title(self.scroll, "04 // ACTIVE SUSTAINED SPELLS (ПІДТРИМУВАННЯ)", color="#ff007f")
        self.active_container = ctk.CTkFrame(self.scroll, fg_color="#1a1c2e", corner_radius=6)
        self.active_container.pack(fill="x", padx=10, pady=5)

    def _build_next_round_button(self):
        self.btn_next_round = ctk.CTkButton(
            self.scroll,
            text="Н Е К С Т  -  Р А У Н Д  (Списання 10% для підтримки заклинань)",
            font=ctk.CTkFont(family=FONT_MONO, size=13, weight="bold"),
            fg_color="#00f0ff", text_color="#000000", hover_color="#00b8c4",
            height=48, corner_radius=8,
            command=self._action_next_round
        )
        self.btn_next_round.pack(fill="x", padx=10, pady=25)

    # =========================================================================
    # ОНОВЛЕННЯ ДИСПЛЕЇВ
    # =========================================================================
    def refresh_all(self):
        self.refresh_batteries()
        self.refresh_templates()
        self.refresh_active_spells()

    def refresh_batteries(self):
        for w in self.bat_container.winfo_children():
            w.destroy()

        if not self.dm.batteries:
            ctk.CTkLabel(self.bat_container, text="// БАТАРЕЇ НЕ ПІДКЛЮЧЕНІ",
                         font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#5f647d").pack(pady=10)
            return

        for name, info in self.dm.batteries.items():
            frame = ctk.CTkFrame(self.bat_container, fg_color="#222538", height=38, corner_radius=4)
            frame.pack(fill="x", pady=2, padx=5)
            pct = info["current"] / info["max"] if info["max"] > 0 else 0
            color = "#00f0ff" if pct > 0.4 else "#ffaa00" if pct > 0.15 else "#ff0055"
            ctk.CTkLabel(frame, text=f"🔋 {name}: ",
                         font=ctk.CTkFont(family=FONT_MONO, size=12, weight="bold")).pack(side="left", padx=10)
            ctk.CTkLabel(frame, text=f"{info['current']} / {info['max']} Аркани",
                         font=ctk.CTkFont(family=FONT_MONO, size=12), text_color=color).pack(side="left")

            def _del(b=name):
                del self.dm.batteries[b]
                self.dm.save_to_json()
                self.refresh_batteries()

            ctk.CTkButton(frame, text="Видалити", width=60, height=22,
                          fg_color="#44475a", text_color="#ff5555",
                          font=ctk.CTkFont(size=10), command=_del).pack(side="right", padx=10)

    def refresh_templates(self):
        for w in self.templates_container.winfo_children():
            w.destroy()

        if not self.dm.saved_spells:
            ctk.CTkLabel(self.templates_container,
                         text="// БАНК ПУСТ. ЗБЕРЕЖІТЬ КОНФИГУРАЦІЮ ЗЛІВА",
                         font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#5f647d").pack(pady=15)
            return

        for name, data in self.dm.saved_spells.items():
            frame = ctk.CTkFrame(self.templates_container, fg_color="#222538", corner_radius=4)
            frame.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(frame, text=f"✨ {name} [{data['game_formula']}] — {data['A_total']} Ед.",
                         font=ctk.CTkFont(family=FONT_MONO, size=11)).pack(side="left", padx=10, pady=6)

            def _del_tmpl(t=name):
                del self.dm.saved_spells[t]
                self.dm.save_to_json()
                self.refresh_templates()

            ctk.CTkButton(frame, text="✖", width=25, height=24,
                          fg_color="transparent", text_color="#ff5555",
                          hover_color="#342230", command=_del_tmpl).pack(side="right", padx=5)
            ctk.CTkButton(frame, text="АКТИВИРОВАТЬ", width=90, height=24,
                          fg_color="#ff007f",
                          font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                          command=lambda n=name, d=data: self._action_activate_spell(n, d)).pack(side="right", padx=2)

            # Зберігаємо on_load_callback ззовні через bind_load_callback
            if hasattr(self, "_on_load_template") and self._on_load_template:
                ctk.CTkButton(frame, text="👁️", width=30, height=24,
                              fg_color="#3d4466",
                              command=lambda d=data: self._on_load_template(d)).pack(side="right", padx=2)

    def bind_load_template_callback(self, callback):
        """Прив'язує callback для кнопки 👁️ (завантажити шаблон у ліву панель)."""
        self._on_load_template = callback
        self.refresh_templates()

    def refresh_active_spells(self):
        for w in self.active_container.winfo_children():
            w.destroy()

        if not self.dm.active_spells:
            ctk.CTkLabel(self.active_container, text="// НЕМАЄ АКТИВНИХ ПІДТРИМУВАНИХ РУН",
                         font=ctk.CTkFont(family=FONT_MONO, size=11), text_color="#5f647d").pack(pady=20)
            return

        for idx, spell in enumerate(self.dm.active_spells):
            frame = ctk.CTkFrame(self.active_container, fg_color="#1d2d3d",
                                 border_width=1, border_color="#00f0ff", corner_radius=6)
            frame.pack(fill="x", pady=3, padx=5)
            desc = (f"🔷 {spell['name'].upper()} | Лінк: [{spell['battery']}]\n"
                    f"   Дамаг: {spell['formula']} | Списання: {spell['maintenance']} од./раунд")
            ctk.CTkLabel(frame, text=desc,
                         font=ctk.CTkFont(family=FONT_MONO, size=11), justify="left").pack(side="left", padx=10, pady=6)
            ctk.CTkButton(frame, text="ОТКЛЮЧИТЬ", width=85, height=25,
                          fg_color="#2b3047", hover_color="#ff5555", text_color="#ff5555",
                          font=ctk.CTkFont(family=FONT_MONO, size=10, weight="bold"),
                          command=lambda i=idx: self._action_deactivate(i)).pack(side="right", padx=10)

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def _action_add_battery(self):
        name = self.ent_bat_name.get().strip()
        cap_str = self.ent_bat_cap.get().strip()
        if not name or not cap_str:
            return
        try:
            cap = int(cap_str)
            self.dm.batteries[name] = {"max": cap, "current": cap}
            self.dm.save_to_json()
            self.refresh_batteries()
            self.ent_bat_name.delete(0, ctk.END)
            self.ent_bat_cap.delete(0, ctk.END)
        except ValueError:
            pass

    def _action_activate_spell(self, spell_name: str, data: dict):
        available = list(self.dm.batteries.keys())
        if not available:
            messagebox.showerror("Помилка", "Немає доступних батарейок!")
            return

        win = ctk.CTkToplevel()
        win.title("ВИБІР ДЖЕРЕЛА")
        win.geometry("350x180")
        win.grab_set()

        ctk.CTkLabel(win, text=f"Активація: {spell_name}\nВартість: {data['A_total']} Аркани\nВиберіть джерело:",
                     font=ctk.CTkFont(family=FONT_MONO, size=12)).pack(pady=10)
        cb = ctk.CTkComboBox(win, values=available, width=200)
        cb.pack(pady=5)

        def confirm():
            bat = cb.get()
            cost = data["A_total"]
            if self.dm.batteries[bat]["current"] < cost:
                messagebox.showerror("Відмова", "Недостатньо заряду в вибраній батарейці!")
                return
            self.dm.batteries[bat]["current"] -= cost
            maintenance = max(1, math.ceil(cost * 0.10))
            self.dm.active_spells.append({
                "name": spell_name, "cost": cost, "battery": bat,
                "maintenance": maintenance, "formula": data["game_formula"]
            })
            self.dm.save_to_json()
            self.refresh_batteries()
            self.refresh_active_spells()
            win.destroy()

        ctk.CTkButton(win, text="ПІДКЛЮЧИТИ І КАСТАНУТИ",
                      fg_color="#00f0ff", text_color="#000000", command=confirm).pack(pady=15)

    def _action_deactivate(self, idx: int):
        if idx < len(self.dm.active_spells):
            self.dm.active_spells.pop(idx)
            self.dm.save_to_json()
            self.refresh_active_spells()

    def _action_next_round(self):
        logs = []
        for spell in list(self.dm.active_spells):
            bat = spell["battery"]
            maint = spell["maintenance"]
            if bat in self.dm.batteries:
                if self.dm.batteries[bat]["current"] >= maint:
                    self.dm.batteries[bat]["current"] -= maint
                    logs.append(f"• [Підтримка] '{spell['name']}' удержано. Знято {maint} ед. з [{bat}]")
                else:
                    logs.append(f"• !!! '{spell['name']}' розсіялась! Заряд [{bat}] вичерпано.")
                    self.dm.active_spells.remove(spell)
            else:
                self.dm.active_spells.remove(spell)

        self.dm.save_to_json()
        self.refresh_batteries()
        self.refresh_active_spells()
        if logs:
            messagebox.showinfo("ФАЗА ЗАВЕРШЕНА", "Звіт по підтриманню заклинань:\n\n" + "\n".join(logs))
