from ursina import *
from ..config import NEIGHBOR_HP, NEIGHBOR_COOLDOWN, GAME_SHADER
from .. import core
from .base_enemy import BaseEnemy
from .projectile import Projectile


class Neighbor(BaseEnemy):
    def __init__(self, pos):
        super().__init__(Vec3(pos.x, 2.5, pos.z), NEIGHBOR_HP, color.rgb(170, 75, 75), half=0.5)
        Entity(parent=self, model='cube', scale=(1.8, 0.25, 1.4),
               position=(0, -0.6, 0.2), color=color.rgb(95, 95, 105), shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(1.8, 0.5, 0.1),
               position=(0, -0.3, 0.85), color=color.rgb(70, 70, 80), shader=GAME_SHADER)
        self.body = Entity(parent=self, model='cube', scale=(0.6, 0.8, 0.4),
                           color=self.base_col, shader=GAME_SHADER)
        Entity(parent=self, model='sphere', scale=0.38,
               position=(0, 0.6, 0), color=color.rgb(230, 195, 170), shader=GAME_SHADER)
        self.arm = Entity(parent=self, model='cube', scale=(0.18, 0.5, 0.18),
                          position=(0.4, 0.2, 0), rotation_z=-35,
                          color=color.rgb(200, 150, 110), shader=GAME_SHADER)
        self.cd = NEIGHBOR_COOLDOWN * 0.5

    def update(self):
        if not self.alive or core.gs['over']:
            return
        dt = time.dt
        self.cd = max(0, self.cd - dt)
        self._flash_update()

        if core.player.stunned:
            return
        self.facing = 1 if core.player.x > self.x else -1
        if self.cd <= 0 and abs(core.player.x - self.x) < 16:
            self.arm.rotation_z = -35
            invoke(setattr, self.arm, 'rotation_z', 55, delay=0.18)
            core.projectiles.append(
                Projectile(self.world_position + Vec3(self.facing * 0.5, 0.1, 0)))
            self.cd = NEIGHBOR_COOLDOWN
