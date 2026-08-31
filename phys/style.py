"""Единое оформление графиков: одинаковые шрифты, цвета и сетка во всём пособии."""

import matplotlib as mpl
import matplotlib.pyplot as plt

# Палитра пособия. Цвета подобраны так, чтобы различаться и на экране,
# и при печати в оттенках серого.
COLORS = {
    "solid": "#2f6690",     # твёрдое тело
    "liquid": "#3a8fb7",    # жидкость
    "gas": "#d1495b",       # газ
    "accent": "#e07a5f",    # выделение
    "neutral": "#5b6570",   # вспомогательные линии
    "grid": "#c9ced6",
}


def use() -> None:
    """Включить оформление пособия для всех последующих графиков."""
    mpl.rcParams.update({
        "figure.figsize": (7.2, 4.2),
        "figure.dpi": 110,
        "savefig.dpi": 110,
        "font.size": 12,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "axes.grid": True,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": COLORS["grid"],
        "grid.linewidth": 0.8,
        "grid.alpha": 0.7,
        "lines.linewidth": 2.0,
        "legend.frameon": False,
        "axes.prop_cycle": mpl.cycler(color=[
            COLORS["solid"], COLORS["gas"], COLORS["liquid"],
            COLORS["accent"], COLORS["neutral"],
        ]),
    })


def axes(xlabel: str = "", ylabel: str = "", title: str = "", **kwargs):
    """Создать фигуру с подписанными осями — короткая замена plt.subplots."""
    fig, ax = plt.subplots(**kwargs)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    return fig, ax
