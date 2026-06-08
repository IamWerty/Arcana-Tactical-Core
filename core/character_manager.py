"""
core/character_manager.py
=========================
Система управління персонажами. data/characters.json + data/spellbook.json.

СТРУКТУРА ХАРАКТЕРИСТИК (пункт 5+6 ТЗ):
  char["stats"] = {
      "Сила":       {"value": 10, "bonus": 0},   # value = базове значення,
      "Ловкість":   {"value": 10, "bonus": 0},   # bonus = додатковий бонус кампанії
      ...                                         # modifier = авторозрахунок
  }
  char["skills"] = {
      "Атлетика": 0,   # зберігається як різниця відносно базового модифікатора
      ...
  }

  modifier(value) — стандартна D&D таблиця:
      1→-5, 2-3→-4, 4-5→-3, 6-7→-2, 8-9→-1, 10-11→0, 12-13→+1, 14-15→+2,
      16-17→+3, 18-19→+4, 20-21→+5 ...

  Підсумкове значення навички = modifier(stat.value) + stat.bonus + skill_bonus
  Ініціатива = modifier(Ловкість.value) + Ловкість.bonus  (авто)
"""
import json
import math
import os
import uuid

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR        = os.path.normpath(os.path.join(_HERE, "..", "data"))
CHARACTERS_FILE = os.path.join(DATA_DIR, "characters.json")
SPELLBOOK_FILE  = os.path.join(DATA_DIR, "spellbook.json")

# ── Раси ──
ALL_RACES = [
    "Людина", "Ельф", "Дворф", "Гафлінг", "Гном", "Напівельф",
    "Напіворк", "Тіфлінг", "Драконороджений", "Аасімар",
    "Генасі (Вогонь)", "Генасі (Вода)", "Генасі (Земля)", "Генасі (Повітря)",
    "Табаксі", "Кенку", "Ящерослюди", "Тортл", "Гобл", "Бугбер",
    "Хобгоблін", "Орк", "Тривожний ельф", "Морський ельф", "Дроу"
]

CLASSES = ["Маг", "Мечник"]

STAT_NAMES = ["Сила", "Ловкість", "Статура", "Інтелект", "Мудрість", "Харизма"]

SKILLS = {
    "Сила":     ["Атлетика"],
    "Ловкість": ["Акробатика", "Ловкість рук", "Скритність"],
    "Інтелект": ["Аркани", "Історія", "Дослідження", "Природа", "Релігія"],
    "Мудрість": ["Догляд за тваринами", "Проникливість", "Медицина", "Сприйняття", "Виживання"],
    "Харизма":  ["Обман", "Залякування", "Виступ", "Переконання"],
    "Статура":  []
}

# Зворотня карта: навичка → характеристика
SKILL_TO_STAT: dict[str, str] = {
    skill: stat
    for stat, skills in SKILLS.items()
    for skill in skills
}

# pool_limit за замовчуванням при створенні
POOL_LIMIT_DEFAULT = {"Маг": 5.0, "Мечник": 10.0}


# ── Модифікатор (стандартна D&D прогресія) ──
def stat_modifier(value: int) -> int:
    """Стандартний D&D модифікатор: floor((value - 10) / 2)."""
    return math.floor((int(value) - 10) / 2)


def _default_stats() -> dict:
    return {s: {"value": 10, "bonus": 0} for s in STAT_NAMES}


def _default_skills() -> dict:
    return {
        skill: 0
        for skills in SKILLS.values()
        for skill in skills
    }


def _default_character(name: str, race: str, char_class: str,
                        weapon_name: str = "", weapon_dk: int = 8,
                        is_player: bool = True) -> dict:
    char = {
        "id":               str(uuid.uuid4()),
        "name":             name,
        "race":             race,
        "char_class":       char_class,
        "level":            1,
        "is_player":        is_player,
        "hp_max":           10,
        "hp_current":       10,
        "ac":               10,
        "speed":            30,
        "gold":             0,
        "pool_limit":       POOL_LIMIT_DEFAULT.get(char_class, 10.0),
        # Нова структура характеристик (пункт 5)
        "stats":            _default_stats(),
        # Навички — різниця відносно базового модифікатора
        "skills":           _default_skills(),
        "inventory":        [],
        "class_data":       {},
        # weapon — тепер є у всіх (необов'язкова для мага)
        "weapon_name":      weapon_name or "",
        "weapon_dk":        weapon_dk,
    }

    if char_class == "Маг":
        char["batteries"]    = {f"Сувій Ліори ({name})": {"max": 1000, "current": 1000}}
        char["known_spells"] = []
        char["active_spells"] = []
    else:
        char["batteries"] = {}

    return char


def migrate_old_char(char: dict) -> dict:
    """
    Підтягує старі персонажі до нової структури без втрати даних.
    Викликається автоматично при завантаженні.
    """
    # saving_throws → stats (якщо ще не мігровано)
    if "stats" not in char:
        old_st = char.pop("saving_throws", {})
        # Перейменування: Тілобудова → Статура
        rename = {"Тілобудова": "Статура"}
        stats = {}
        for s in STAT_NAMES:
            old_name = {v: k for k, v in rename.items()}.get(s, s)
            old_val = old_st.get(old_name, old_st.get(s, 0))
            stats[s] = {"value": 10, "bonus": old_val}
        char["stats"] = stats

    # Переконуємось що всі характеристики є
    for s in STAT_NAMES:
        if s not in char["stats"]:
            char["stats"][s] = {"value": 10, "bonus": 0}
        if not isinstance(char["stats"][s], dict):
            old = char["stats"][s]
            char["stats"][s] = {"value": 10, "bonus": int(old)}

    # Навички — якщо відсутні деякі, додаємо
    char.setdefault("skills", {})
    for skills in SKILLS.values():
        for sk in skills:
            char["skills"].setdefault(sk, 0)

    # weapon — тепер у всіх
    char.setdefault("weapon_name", "")
    char.setdefault("weapon_dk", 6)

    # pool_limit — якщо маг мав 10.0 (старий дефолт), не міняємо (майстер міг вже змінити)
    char.setdefault("pool_limit", POOL_LIMIT_DEFAULT.get(char.get("char_class", "Мечник"), 10.0))

    # initiative_bonus — видаляємо зайве поле (тепер авто від Ловкості)
    char.pop("initiative_bonus", None)

    return char


class CharacterManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.characters: list[dict] = []
        self.global_spellbook: dict = {}
        self._load_spellbook()
        self._load_characters()

    # =========================================================================
    # STAT HELPERS
    # =========================================================================
    @staticmethod
    def modifier(char: dict, stat: str) -> int:
        """Підсумковий модифікатор характеристики = mod(value) + bonus."""
        s = char.get("stats", {}).get(stat, {"value": 10, "bonus": 0})
        return stat_modifier(s["value"]) + s["bonus"]

    @staticmethod
    def skill_total(char: dict, skill: str) -> int:
        """Підсумкове значення навички = mod(stat) + skill_bonus."""
        stat = SKILL_TO_STAT.get(skill)
        base = CharacterManager.modifier(char, stat) if stat else 0
        bonus = char.get("skills", {}).get(skill, 0)
        return base + bonus

    @staticmethod
    def initiative(char: dict) -> int:
        """Ініціатива = модифікатор Ловкості (авто)."""
        return CharacterManager.modifier(char, "Ловкість")

    # =========================================================================
    # SPELLBOOK
    # =========================================================================
    def _load_spellbook(self):
        if os.path.exists(SPELLBOOK_FILE):
            try:
                with open(SPELLBOOK_FILE, "r", encoding="utf-8") as f:
                    self.global_spellbook = json.load(f)
            except Exception as e:
                print(f"[CM] Спеллбук: {e}")
                self.global_spellbook = {}
        else:
            self.global_spellbook = {}

    def save_spellbook(self):
        try:
            with open(SPELLBOOK_FILE, "w", encoding="utf-8") as f:
                json.dump(self.global_spellbook, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[CM] Збереження спеллбука: {e}")

    def add_spell(self, name: str, data: dict):
        self.global_spellbook[name] = data
        self.save_spellbook()

    def delete_spell(self, name: str):
        if name in self.global_spellbook:
            del self.global_spellbook[name]
            for char in self.characters:
                if char.get("char_class") == "Маг":
                    known = set(char.get("known_spells", []))
                    known.discard(name)
                    char["known_spells"] = list(known)
            self.save_spellbook()
            self.save_characters()

    def get_all_spells(self) -> dict:
        return dict(self.global_spellbook)

    def get_spells_for_char(self, char_id: str) -> dict:
        char = self.get_by_id(char_id)
        if not char or char.get("char_class") != "Маг":
            return {}
        known = set(char.get("known_spells", []))
        return {k: v for k, v in self.global_spellbook.items() if k in known}

    # =========================================================================
    # CHARACTERS CRUD
    # =========================================================================
    def create_character(self, name: str, race: str, char_class: str,
                         weapon_name: str = "", weapon_dk: int = 8,
                         is_player: bool = True) -> dict:
        char = _default_character(name, race, char_class, weapon_name, weapon_dk, is_player)
        self.characters.append(char)
        self.save_characters()
        return char

    def update_character(self, char_id: str, updates: dict):
        char = self.get_by_id(char_id)
        if char:
            char.update(updates)
            self.save_characters()

    def delete_character(self, char_id: str):
        self.characters = [c for c in self.characters if c["id"] != char_id]
        self.save_characters()

    def get_by_id(self, char_id: str) -> dict | None:
        for c in self.characters:
            if c["id"] == char_id:
                return c
        return None

    def get_sorted(self) -> list[dict]:
        players = [c for c in self.characters if c.get("is_player")]
        npcs    = [c for c in self.characters if not c.get("is_player")]
        return players + npcs

    def get_names_list(self, class_filter: str = None) -> list[str]:
        chars = self.get_sorted()
        if class_filter:
            chars = [c for c in chars if c.get("char_class") == class_filter]
        return [c["name"] for c in chars]

    def get_by_name(self, name: str) -> dict | None:
        for c in self.characters:
            if c["name"] == name:
                return c
        return None

    # =========================================================================
    # BATTERY HELPERS
    # =========================================================================
    def drain_battery(self, char_id: str, bat_name: str, amount: int) -> bool:
        char = self.get_by_id(char_id)
        if char and bat_name in char.get("batteries", {}):
            bat = char["batteries"][bat_name]
            if bat["current"] >= amount:
                bat["current"] -= amount
                self.save_characters()
                return True
        return False

    def total_arcana(self, char_id: str) -> int:
        char = self.get_by_id(char_id)
        if not char:
            return 0
        return sum(b["current"] for b in char.get("batteries", {}).values())

    # =========================================================================
    # ACTIVE SPELLS
    # =========================================================================
    def next_round_for_char(self, char_id: str) -> list[str]:
        char = self.get_by_id(char_id)
        if not char or char.get("char_class") != "Маг":
            return []
        logs, to_remove = [], []
        for spell in list(char.get("active_spells", [])):
            bat, maint = spell["battery"], spell["maintenance"]
            if bat in char.get("batteries", {}):
                if char["batteries"][bat]["current"] >= maint:
                    char["batteries"][bat]["current"] -= maint
                    logs.append(f"• '{spell['name']}' утримано. -{maint} з [{bat}]")
                else:
                    logs.append(f"• !!! '{spell['name']}' розсіялась!")
                    to_remove.append(spell)
            else:
                to_remove.append(spell)
        for s in to_remove:
            char["active_spells"].remove(s)
        self.save_characters()
        return logs

    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    def save_characters(self):
        try:
            with open(CHARACTERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.characters, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[CM] Збереження: {e}")

    def _load_characters(self):
        if os.path.exists(CHARACTERS_FILE):
            try:
                with open(CHARACTERS_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.characters = [migrate_old_char(c) for c in raw]
                self.save_characters()   # одразу зберігаємо мігровані дані
            except Exception as e:
                print(f"[CM] Завантаження: {e}")
