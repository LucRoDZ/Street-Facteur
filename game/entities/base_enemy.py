from ursina import *
from ..config import GRAVITY, STAGE_LEFT, STAGE_RIGHT, GROUND_Y
from .. import core
from ..fx import burst


class BaseEnemy(Entity):
    damageable = True

    def __init__(self, pos, hp, base_col, half=0.5):
        super().__init__(position=pos)
        self.hp        = hp
        self.base_col  = base_col
        self.half      = half
        self.facing    = -1
        self.vel_x     = 0.0
        self.vel_y     = 0.0
        self.on_ground = True
        self.alive     = True
        self._flash    = 0.0
        self.body      = None

    def _physics(self):
        dt = time.dt
        self.vel_y -= GRAVITY * dt
        self.y     += self.vel_y * dt
        floor = GROUND_Y + self.half
        if self.y <= floor:
            self.y, self.vel_y, self.on_ground = floor, 0, True
        else:
            self.on_ground = False
        if abs(self.vel_x) > 0.05:
            self.x    += self.vel_x * dt
            self.vel_x = lerp(self.vel_x, 0, 8 * dt)
        self.x = clamp(self.x, STAGE_LEFT, STAGE_RIGHT)

    def _flash_update(self):
        if not self.body:
            return
        if self._flash > 0:
            self._flash -= time.dt
            self.body.color = color.white
        else:
            self.body.color = self.base_col

    def hit(self, amount, source_x):
        if not self.alive:
            return
        self.hp    -= amount
        self._flash = 0.12
        self.vel_x  = (1 if self.x > source_x else -1) * 4.0
        burst(self.world_position + Vec3(0, 0.3, 0), self.base_col,
              count=8, spread=1.2, life=0.3)
        if self.hp <= 0:
            self._die()

    def _die(self):
        self.alive = False
        if self in core.enemies:
            core.enemies.remove(self)
        burst(self.world_position + Vec3(0, 0.3, 0), self.base_col,
              count=18, spread=2.2, life=0.5)
        self.animate_scale(0.001, duration=0.35, curve=curve.in_back)
        destroy(self, delay=0.4)
