import logging
import typing
import pygame as pg


class KeyBinding:
    def __init__(
        self, keycode: int, group: str, func: typing.Callable, on_pressed=False
    ):
        self.keycode = keycode
        self.group = group
        self.func = func
        self.on_pressed = on_pressed
        logging.debug(f"Keybinding created: {str(self)}")

    def __str__(self):
        return f"(keycode={pg.key.name(self.keycode)}, group={self.group})"
