import math
from ursina import *
from .config import LEVEL_TIME, TOTAL_MAILBOXES, PLAYER_HP
from . import core

_HP_LEFT = -0.855


class HUD:
    def __init__(self):
        self.timer = Text(str(int(LEVEL_TIME)), parent=camera.ui,
                          position=(0, 0.46), origin=(0, 0), scale=2.6,
                          color=color.white, enabled=False)
        self.mails = Text(f"COURRIER  0 / {TOTAL_MAILBOXES}", parent=camera.ui,
                          position=(-0.86, 0.46), origin=(-0.5, 0), scale=1.3,
                          color=color.rgb(255, 230, 120), enabled=False)

        self.hp_bg = Entity(parent=camera.ui, model='quad', scale=(0.34, 0.04),
                            position=(-0.69, -0.45), color=color.rgb(25, 25, 30),
                            enabled=False)
        self.hp_bar = Entity(parent=camera.ui, model='quad', scale=(0.33, 0.03),
                             position=(_HP_LEFT + 0.165, -0.45), color=color.red,
                             enabled=False)
        self._facteur = Text("FACTEUR", parent=camera.ui,
                             position=(-0.855, -0.41), origin=(-0.5, 0),
                             scale=0.9, color=color.white, enabled=False)

        self.overlay = Entity(parent=camera.ui, model='quad', scale=(4, 2),
                              color=color.rgba(0, 0, 0, 200), enabled=False)
        self.end_txt = Text("", parent=camera.ui, position=(0, 0.05),
                            origin=(0, 0), scale=1.8, color=color.white,
                            enabled=False)
        self._blink = 0.0

    def show(self):
        for e in (self.timer, self.mails, self.hp_bg, self.hp_bar, self._facteur):
            e.enabled = True

    def update(self):
        secs = max(0, int(math.ceil(core.gs['timer'])))
        self.timer.text = str(secs)
        if core.gs['timer'] < 15:
            self._blink += time.dt
            self.timer.color   = color.red
            self.timer.enabled = int(self._blink * 4) % 2 == 0
        else:
            self.timer.color   = color.white
            self.timer.enabled = True

        self.mails.text = f"COURRIER  {core.gs['mails']} / {TOTAL_MAILBOXES}"

        ratio = clamp(core.player.hp / PLAYER_HP, 0, 1)
        w = max(0.001, 0.33 * ratio)
        self.hp_bar.scale_x = w
        self.hp_bar.x = _HP_LEFT + w / 2
        self.hp_bar.color = color.red if ratio > 0.3 else color.orange

    def show_end(self, msg, col):
        self.overlay.enabled = True
        self.end_txt.text    = msg
        self.end_txt.color   = col
        self.end_txt.enabled = True

    def reset(self):
        self.overlay.enabled = False
        self.end_txt.enabled = False
        self._blink = 0.0
