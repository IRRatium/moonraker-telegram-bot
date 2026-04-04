"""
LED controller — хранит состояние подсветки и отдаёт его в API.
ESP8266/ESP32 опрашивают /ledstatus и применяют настройки локально.
"""
from datetime import datetime
from typing import Dict, Tuple


COLOR_PRESETS: Dict[str, Tuple[int, int, int]] = {
    "white":      (255, 255, 255),
    "warm_white": (255, 200, 100),
    "red":        (255,   0,   0),
    "green":      (  0, 255,   0),
    "blue":       (  0,   0, 255),
    "cyan":       (  0, 255, 255),
    "purple":     (128,   0, 255),
    "orange":     (255, 128,   0),
}

EFFECTS = ["solid", "blink", "breathe", "rainbow", "strobe", "fade"]

COLOR_EMOJI: Dict[str, str] = {
    "white":      "⚪",
    "warm_white": "🟡",
    "red":        "🔴",
    "green":      "🟢",
    "blue":       "🔵",
    "cyan":       "🩵",
    "purple":     "🟣",
    "orange":     "🟠",
}

EFFECT_EMOJI: Dict[str, str] = {
    "solid":   "💡",
    "blink":   "💫",
    "breathe": "🌊",
    "rainbow": "🌈",
    "strobe":  "⚡",
    "fade":    "🌅",
}

COLOR_RU: Dict[str, str] = {
    "white":      "Белый",
    "warm_white": "Тёплый",
    "red":        "Красный",
    "green":      "Зелёный",
    "blue":       "Синий",
    "cyan":       "Голубой",
    "purple":     "Пурпурный",
    "orange":     "Оранжевый",
}

EFFECT_RU: Dict[str, str] = {
    "solid":   "Статика",
    "blink":   "Мигание",
    "breathe": "Дыхание",
    "rainbow": "Радуга",
    "strobe":  "Строб",
    "fade":    "Плавное",
}


class LedController:
    """Holds the current LED state. Thread-safe reads, single-writer (bot thread)."""

    def __init__(self) -> None:
        self.on: bool = True
        self.r: int = 255
        self.g: int = 255
        self.b: int = 255
        self.brightness: int = 100   # 0-100 %
        self.effect: str = "solid"
        self.color_name: str = "white"
        self.updated_at: str = datetime.now().isoformat()

    # ------------------------------------------------------------------ #
    #  Mutators                                                            #
    # ------------------------------------------------------------------ #

    def set_color(self, name: str) -> None:
        if name in COLOR_PRESETS:
            self.r, self.g, self.b = COLOR_PRESETS[name]
            self.color_name = name
            self._touch()

    def set_brightness(self, value: int) -> None:
        self.brightness = max(0, min(100, value))
        self._touch()

    def set_effect(self, effect: str) -> None:
        if effect in EFFECTS:
            self.effect = effect
            self._touch()

    def toggle(self) -> None:
        self.on = not self.on
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now().isoformat()

    # ------------------------------------------------------------------ #
    #  Serialisation                                                       #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "on": self.on,
            "color": {
                "name":  self.color_name,
                "r":     self.r,
                "g":     self.g,
                "b":     self.b,
                "hex":   f"#{self.r:02x}{self.g:02x}{self.b:02x}",
            },
            "brightness": self.brightness,
            "effect":     self.effect,
            "updated_at": self.updated_at,
        }

    # ------------------------------------------------------------------ #
    #  UI helpers                                                          #
    # ------------------------------------------------------------------ #

    def status_text(self) -> str:
        state = "🟢 ВКЛ" if self.on else "🔴 ВЫКЛ"
        c_icon = COLOR_EMOJI.get(self.color_name, "🎨")
        e_icon = EFFECT_EMOJI.get(self.effect, "✨")
        c_name = COLOR_RU.get(self.color_name, self.color_name)
        e_name = EFFECT_RU.get(self.effect, self.effect)
        return (
            f"💡 *Подсветка принтера*\n"
            f"Состояние: {state}\n"
            f"Цвет: {c_icon} {c_name}\n"
            f"Яркость: {self.brightness}%\n"
            f"Эффект: {e_icon} {e_name}"
        )
