from ursina import *
from ..config import GRANNY_RANGE, GRANNY_STUN_DURATION, GROUND_Y, PLAYER_HALF, GAME_SHADER
from .. import core
from .base_enemy import BaseEnemy


class Granny(BaseEnemy):
    damageable = False

    def __init__(self, pos):
        super().__init__(pos, 9999, color.rgb(170, 95, 185), half=0.65)
        self.body = Entity(parent=self, model='cube', scale=(0.65, 1.0, 0.5),
                           color=self.base_col, shader=GAME_SHADER)
        Entity(parent=self, model='sphere', scale=0.42,
               position=(0, 0.72, 0), color=color.rgb(235, 205, 195), shader=GAME_SHADER)
        Entity(parent=self, model='sphere', scale=0.34,
               position=(0, 0.95, -0.05), color=color.rgb(220, 220, 225), shader=GAME_SHADER)
        self.bubble = Text("Mon petit,\nà mon époque...",
                           parent=self, position=(0.7, 1.5, 0), scale=10,
                           color=color.black, background=True,
                           enabled=False)
        self.cd       = 0.0
        self.grabbing = None

    def update(self):
        if core.gs['over']:
            return
        dt = time.dt
        self.cd = max(0, self.cd - dt)

        if self.grabbing:
            core.player.x = self.x + 1.1
            core.player.y = GROUND_Y + PLAYER_HALF
            if not core.player.stunned:
                self.release()
        elif self.cd <= 0 and not core.player.stunned:
            if abs(core.player.x - self.x) < GRANNY_RANGE and core.player.on_ground:
                self.grabbing = core.player
                self.bubble.enabled = True
                core.player.grab(self)

    def release(self):
        self.grabbing = None
        self.bubble.enabled = False
        self.cd = 3.0
