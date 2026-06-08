"""
core/data_manager.py
====================
Централізована система зберігання БОЙОВОГО стану сесії.
Файли зберігаються у ./data/ поруч із точкою входу (main.py).

saved_spells більше НЕ зберігається тут — єдине джерело заклинань
тепер data/spellbook.json, яким керує CharacterManager.
DataManager зберігає лише:
  - batteries        (legacy-батарейки без персонажа)
  - active_spells    (активні закли без персонажа)
  - clash_state      (стан Clash, тільки в пам'яті)
"""
import json
import os

# data/ лежить поруч із main.py (на один рівень вище core/)
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(_HERE, "..", "data"))
SAVE_FILE = os.path.join(DATA_DIR, "battle_save.json")


class DataManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)

        self.batteries: dict = {}
        self.active_spells: list = []

        # Стан Clash (не зберігається між сесіями)
        self.clash_state: dict = {
            "active": False,
            "scale": 0,
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
