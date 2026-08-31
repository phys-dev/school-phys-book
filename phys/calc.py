"""Физические постоянные и расчёты, которые встречаются в курсе 8 класса.

Все величины — в СИ. Значения округлены до точности, принятой в школьном курсе.
"""

from dataclasses import dataclass

# --- Постоянные -----------------------------------------------------------
N_A = 6.02e23            # постоянная Авогадро, 1/моль
U = 1.66e-27             # атомная единица массы, кг
M_H = 1.66e-27           # масса атома водорода, кг (самый лёгкий атом)
D_ATOM = 1e-10           # характерный размер атома, м

# --- Молярные массы часто встречающихся веществ, кг/моль ------------------
MOLAR_MASS = {
    "водород (H₂)": 0.002,
    "гелий (He)": 0.004,
    "вода (H₂O)": 0.018,
    "азот (N₂)": 0.028,
    "воздух": 0.029,
    "кислород (O₂)": 0.032,
    "углекислый газ (CO₂)": 0.044,
    "медь (Cu)": 0.064,
}

# --- Плотности, кг/м³ -----------------------------------------------------
DENSITY = {
    "вода": 1000,
    "лёд": 900,
    "спирт": 800,
    "воздух": 1.29,
    "алюминий": 2700,
    "железо": 7800,
    "медь": 8900,
    "свинец": 11350,
}


@dataclass
class Substance:
    """Вещество: название, молярная масса (кг/моль) и плотность (кг/м³)."""

    name: str
    molar_mass: float
    density: float

    @property
    def molecule_mass(self) -> float:
        """Масса одной молекулы, кг: m₀ = M / N_A."""
        return self.molar_mass / N_A

    @property
    def molecule_size(self) -> float:
        """Оценка размера молекулы, м.

        Считаем, что молекулы упакованы вплотную: на каждую приходится
        кубик объёмом V₀ = m₀ / ρ, ребро которого и есть размер молекулы.
        """
        return (self.molecule_mass / self.density) ** (1 / 3)


WATER = Substance("вода", 0.018, 1000)
COPPER = Substance("медь", 0.064, 8900)
AIR = Substance("воздух", 0.029, 1.29)


def molecule_count(mass: float, molar_mass: float) -> float:
    """Число молекул в теле массой ``mass`` (кг): N = m / M · N_A."""
    return mass / molar_mass * N_A


def molecule_mass(molar_mass: float) -> float:
    """Масса одной молекулы, кг: m₀ = M / N_A."""
    return molar_mass / N_A


def volume_to_mass(volume: float, density: float) -> float:
    """Масса тела, кг: m = ρ·V, где объём ``volume`` в м³."""
    return density * volume


def fmt(value: float, digits: int = 2, unit: str = "") -> str:
    """Записать число в стандартном виде a·10ⁿ для вывода в тексте урока.

    >>> fmt(6.02e23, unit='1/моль')
    '6,02 · 10²³ 1/моль'
    """
    if value == 0:
        return "0" + (f" {unit}" if unit else "")
    exponent = 0
    mantissa = abs(value)
    while mantissa >= 10:
        mantissa /= 10
        exponent += 1
    while mantissa < 1:
        mantissa *= 10
        exponent -= 1
    sign = "−" if value < 0 else ""
    superscripts = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    mantissa_text = f"{mantissa:.{digits}f}".replace(".", ",")
    tail = f" {unit}" if unit else ""
    if exponent == 0:
        return f"{sign}{mantissa_text}{tail}"
    return f"{sign}{mantissa_text} · 10{str(exponent).translate(superscripts)}{tail}"
