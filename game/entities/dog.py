import math, random
from ursina import *
from ..config import DOG_HP, DOG_SPEED, DOG_ATTACK_DAMAGE, DOG_DETECT_RANGE, GAME_SHADER
from .. import core
from ..fx import burst
from .base_enemy import BaseEnemy


class Dog(BaseEnemy):
    def __init__(self, pos):
        super().__init__(pos, DOG_HP, color.rgb(190, 110, 45), half=0.4)
        self.body = Entity(parent=self, model='sphere', scale=(1.1, 0.55, 0.55),
                           color=self.base_col, shader=GAME_SHADER)
        Entity(parent=self, model='sphere', scale=0.5,
               position=(0.55, 0.18, 0), color=color.rgb(205, 130, 60), shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(0.12, 0.2, 0.12),
               position=(0.62, 0.45, 0.13), color=color.rgb(150, 85, 30), shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(0.12, 0.2, 0.12),
               position=(0.62, 0.45, -0.13), color=color.rgb(150, 85, 30), shader=GAME_SHADER)
        for lx in (-0.35, 0.35):
            for lz in (-0.18, 0.18):
                Entity(parent=self, model='cube', scale=(0.13, 0.4, 0.13),
                       position=(lx, -0.42, lz), color=color.rgb(150, 85, 30), shader=GAME_SHADER)
        self.tail = Entity(parent=self, model='cube', scale=(0.12, 0.32, 0.12),
                           position=(-0.6, 0.2, 0), rotation_z=40,
                           color=self.base_col, shader=GAME_SHADER)
        self.center   = pos.x
        self.atk_cd   = 0.0
        self.growl_cd = random.uniform(0.5, 1.5)

    def update(self):
        if not self.alive or core.gs['over']:
            return
        dt = time.dt
        self.atk_cd   = max(0, self.atk_cd - dt)
        self.growl_cd -= dt
        self._physics()
        self._flash_update()
        self.tail.rotation_z = 40 + math.sin(time.time() * 12) * 25

        dist = abs(core.player.x - self.x)
        if dist < DOG_DETECT_RANGE and not core.player.stunned:
            self.facing = 1 if core.player.x > self.x else -1
            self.rotation_y = 0 if self.facing > 0 else 180
            self.x += self.facing * DOG_SPEED * dt
            if self.growl_cd <= 0:
                burst(self.world_position + Vec3(self.facing * 0.6, 0.2, 0),
                      color.rgb(220, 220, 220), count=4, spread=0.6, life=0.25, up=0.2)
                self.growl_cd = random.uniform(0.4, 0.9)
            if dist < 1.1 and self.atk_cd <= 0:
                core.player.take_damage(DOG_ATTACK_DAMAGE, self.x)
                self.atk_cd = 1.0
        else:
            self.x += self.facing * DOG_SPEED * 0.4 * dt
            if abs(self.x - self.center) > 3.0:
                self.facing *= -1
                self.rotation_y = 0 if self.facing > 0 else 180
