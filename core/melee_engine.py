"""
core/melee_engine.py
====================
Математичне ядро фізичної бойової системи. Не містить UI залежностей.
"""
import math


def calculate(A: float, V: float, W: float, dk_sides: int,
              weapon_type: str, pool_limit: float) -> dict:
    """
    Повертає повний результат розрахунку фізичного удару.
    """
    dynamic_flat_limit = math.floor(pool_limit / 2)

    # --- Кубики від Амплітуди ---
    base_cubes = 1
    if "Колюча" in weapon_type:
        extra_cubes = 1 if A >= 9.0 else 0
        max_possible_cubes = "2dK (Ліміт колючої геометрії)"
    elif "Рубяща" in weapon_type:
        extra_cubes = math.floor(A / 5.0)
        max_possible_cubes = "3dK"
    else:
        extra_cubes = math.floor(A / 8.0)
        max_possible_cubes = "3dK"
    total_cubes = base_cubes + extra_cubes

    # --- Плоский бонус ---
    if "Дробяща" in weapon_type:
        flat_bonus = min(dynamic_flat_limit, math.floor(W))
        modifier_name = f"Модифікатор сили (W)   : +{flat_bonus} (Макс: +{dynamic_flat_limit})"
    elif "Рубяща" in weapon_type:
        flat_bonus = min(dynamic_flat_limit, math.floor(V))
        modifier_name = f"Модифікатор швидкості : +{flat_bonus} (Макс: +{dynamic_flat_limit})"
    else:
        flat_bonus = math.floor(V / 1.5)
        modifier_name = f"Модифікатор швидкості : +{flat_bonus}"

    # --- Бонус до КБ від Важкості ---
    ac_bonus = math.floor(W / 2) if "Дробяща" in weapon_type else math.floor(W / 5)

    avg_damage = (total_cubes * (1 + dk_sides) / 2) + flat_bonus
    game_formula = f"{total_cubes}d{dk_sides} + {flat_bonus}"

    # --- Ультра-ефекти ---
    special_effects = []
    if "Колюча" in weapon_type and V >= 9.5:
        special_effects.append("УЛЬТРА-ЕФЕКТ [ТОЧКОВИЙ ПРОКОЛ]: Ігнорує КБ від важких обладунків та щитів.")
    elif "Рубяща" in weapon_type and A >= 9.5:
        special_effects.append("УЛЬТРА-ЕФЕКТ [ГЛИБОКИЙ РОЗТИН]: Критичний урон на 19-20.")
    elif "Дробяща" in weapon_type and W >= 9.5:
        special_effects.append("УЛЬТРА-ЕФЕКТ [ЧЕРЕПОЛОМ]: Збиває з ніг, ломає щити або приголомшує ціль.")

    if not special_effects:
        special_effects.append("Активні пасивні бойові ефекти відсутні.")

    return {
        "total_cubes": total_cubes,
        "flat_bonus": flat_bonus,
        "ac_bonus": ac_bonus,
        "avg_damage": avg_damage,
        "game_formula": game_formula,
        "modifier_name": modifier_name,
        "max_possible_cubes": max_possible_cubes,
        "special_effects": special_effects,
        "weapon_short": weapon_type.split(" (")[0].upper(),
        "percentages": (
            A / pool_limit * 100 if pool_limit > 0 else 0,
            V / pool_limit * 100 if pool_limit > 0 else 0,
            W / pool_limit * 100 if pool_limit > 0 else 0
        )
    }


def calculate_clash_round(player_roll: int, enemy_roll: int) -> dict:
    """
    Один раунд Clash.
    Повертає delta (зміну шкали), опис події та ім'я переможця раунду.
    """
    diff = player_roll - enemy_roll

    if diff >= 5:
        return {"delta": +2, "winner": "player", "desc": "Потужний удар! Зброя ворога майже вилітає з рук."}
    elif 1 <= diff <= 4:
        return {"delta": +1, "winner": "player", "desc": "Випад! Ворог змушений відступити на крок."}
    elif diff == 0:
        return {"delta": 0, "winner": "tie", "desc": "Клинки скрегочуть. Іскри летять. Нічия."}
    elif -4 <= diff <= -1:
        return {"delta": -1, "winner": "enemy", "desc": "Бос перехоплює ініціативу, давить масою."}
    else:
        return {"delta": -2, "winner": "enemy", "desc": "Ворог б'є з розвороту! Гравець ледь тримає рівновагу."}
