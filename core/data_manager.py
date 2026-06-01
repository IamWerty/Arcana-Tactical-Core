"""
core/data_manager.py
====================
Централізована система зберігання стану сесії та JSON save/load.
Всі модулі звертаються до цього об'єкту за даними.
"""
import json
import os

SAVE_FILE = os.path.join(os.path.expanduser("~"), ".arcana_battle_save.json")


class DataManager:
    def __init__(self):
        self.batteries: dict = {
            "Мала сура (Альфа)": {"max": 250, "current": 250},
            "Сувій Ліори (Резерв)": {"max": 1000, "current": 1000}
        }
        self.saved_spells: dict = {}
        self.active_spells: list = []

        # Стан Clash-системи (не зберігається між сесіями, тільки на час бою)
        self.clash_state: dict = {
            "active": False,
            "scale": 0,           # від -3 до +3
            "player_mod": 0,
            "enemy_mod": 0,
            "log": []
        }

        self.load_from_json()

    # =========================================================================
    # JSON SAVE / LOAD
    # =========================================================================
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
            print(f"[DataManager] Помилка: Немає доступу до файлу {SAVE_FILE}.")
        except Exception as e:
            print(f"[DataManager] Помилка автозбереження: {e}")

    def load_from_json(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.batteries = loaded.get("batteries", self.batteries)
                    self.saved_spells = loaded.get("saved_spells", self.saved_spells)
                    self.active_spells = loaded.get("active_spells", self.active_spells)
            except Exception as e:
                print(f"[DataManager] Помилка завантаження: {e}")

    # =========================================================================
    # CLASH STATE HELPERS
    # =========================================================================
    def reset_clash(self):
        self.clash_state = {
            "active": True,
            "scale": 0,
            "player_mod": 0,
            "enemy_mod": 0,
            "log": []
        }

    def push_clash_log(self, entry: str):
        self.clash_state["log"].append(entry)
        if len(self.clash_state["log"]) > 20:
            self.clash_state["log"].pop(0)
