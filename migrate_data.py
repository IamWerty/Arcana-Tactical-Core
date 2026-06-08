"""
migrate_data.py
===============
Одноразовий скрипт міграції старих даних із ~/.arcana_* у ./data/

Запустити ОДИН РАЗ перед першим запуском оновленої версії:
  python migrate_data.py
"""
import json
import os
import shutil

HOME = os.path.expanduser("~")
OLD_BATTLE  = os.path.join(HOME, ".arcana_battle_save.json")
OLD_CHARS   = os.path.join(HOME, ".arcana_characters.json")

HERE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
NEW_SPELLBOOK = os.path.join(DATA_DIR, "spellbook.json")
NEW_BATTLE    = os.path.join(DATA_DIR, "battle_save.json")
NEW_CHARS     = os.path.join(DATA_DIR, "characters.json")

os.makedirs(DATA_DIR, exist_ok=True)


def migrate_battle_save():
    if not os.path.exists(OLD_BATTLE):
        print(f"  [skip] {OLD_BATTLE} не знайдено")
        return

    with open(OLD_BATTLE, "r", encoding="utf-8") as f:
        old = json.load(f)

    # saved_spells → spellbook.json (merge з існуючим)
    saved_spells = old.get("saved_spells", {})
    if saved_spells:
        existing_spellbook = {}
        if os.path.exists(NEW_SPELLBOOK):
            with open(NEW_SPELLBOOK, "r", encoding="utf-8") as f:
                existing_spellbook = json.load(f)
        existing_spellbook.update(saved_spells)
        with open(NEW_SPELLBOOK, "w", encoding="utf-8") as f:
            json.dump(existing_spellbook, f, ensure_ascii=False, indent=4)
        print(f"  [OK] {len(saved_spells)} заклинань перенесено → {NEW_SPELLBOOK}")

    # batteries + active_spells → battle_save.json
    new_battle = {
        "batteries":     old.get("batteries", {}),
        "active_spells": old.get("active_spells", [])
    }
    with open(NEW_BATTLE, "w", encoding="utf-8") as f:
        json.dump(new_battle, f, ensure_ascii=False, indent=4)
    print(f"  [OK] battle_save → {NEW_BATTLE}")


def migrate_characters():
    if not os.path.exists(OLD_CHARS):
        print(f"  [skip] {OLD_CHARS} не знайдено")
        return
    shutil.copy2(OLD_CHARS, NEW_CHARS)
    print(f"  [OK] characters → {NEW_CHARS}")


if __name__ == "__main__":
    print("=== ARCANA DATA MIGRATION ===")
    migrate_battle_save()
    migrate_characters()
    print("=== ГОТОВО ===")
    print(f"Файли у: {DATA_DIR}")
