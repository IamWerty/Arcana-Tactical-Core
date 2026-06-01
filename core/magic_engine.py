"""
core/magic_engine.py
====================
Математичне ядро магічної системи. Не містить жодної залежності від UI.
Приймає словник параметрів, повертає словник результатів.
"""
import math


DK_PRICE_MULTIPLIER = {"d4": 0.75, "d6": 1.0, "d8": 1.25, "d10": 1.625, "d12": 2.0}

SIZE_MAP = {"До 10 см": 1.0, "10-30 см": 1.2, "30-100 см": 1.5, "1-3 м": 2.0}
SHAPE_MAP = {"Проста / Аморфна": 5, "Середня / Гостра": 15, "Складна / Анатомічна": 40}
VECTOR_MAP = {"Напрям": 0.0, "Швидкість": 0.2, "Цикл": 0.5, "Повторення": 0.8}
SM_MAP = {"0.5": 0.5, "1.0": 1.0, "1.5": 1.5}


def _get_mass_d6(n: int) -> float:
    """Нелінійна маса снаряду (апроксимована крива по таблиці дамагу)."""
    if n <= 0:
        return 0.0
    elif n <= 4:
        return 3.0244 * (n ** 1.8646)
    else:
        return 40.0 + 98.13 * math.log2((n - 4) * 0.0329 + 1)


def calculate(params: dict) -> dict:
    """
    params: {
        size, shape, vector, sm, km, kq, ndice, dk, arcs, is_far
    }
    Повертає dict з ключами success, і або результати, або error.
    """
    try:
        K_l = SIZE_MAP[params["size"].split(" (")[0]]
        A_shape = SHAPE_MAP[params["shape"].split(" = ")[0]]
        K_vector = 1.0 + VECTOR_MAP[params["vector"].split(" = ")[0]]
        S_m = SM_MAP[params["sm"].split(" (")[0]]
        K_m = float(params["km"])
        K_q = float(params["kq"])
        N_dice = int(params["ndice"])
        dK = params["dk"]
        n_arcs = int(params["arcs"])
        is_far = params["is_far"]

        m = round(_get_mass_d6(N_dice) * DK_PRICE_MULTIPLIER[dK], 2)

        v0 = 10
        harmonic_sum = sum(v0 / i for i in range(1, n_arcs + 1)) if n_arcs > 0 else 0
        v = v0 + harmonic_sum

        A_total = math.ceil(K_l * (((m * K_m * K_q) + A_shape) + (m * K_vector * v)))
        speed_mod = n_arcs * 2

        dk_sides = int(dK[1:])
        avg_damage = (((N_dice * (1 + dk_sides) / 2) * S_m) + speed_mod) / (2 if is_far else 1)
        game_formula = f"({N_dice}{dK}{f' * {S_m}' if S_m != 1.0 else ''}) + {speed_mod}{' / 2' if is_far else ''}"

        return {
            "success": True,
            "A_total": A_total,
            "m": m,
            "v": v,
            "S_m": S_m,
            "speed_mod": speed_mod,
            "avg_damage": avg_damage,
            "game_formula": game_formula,
            "raw_params": dict(params)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
