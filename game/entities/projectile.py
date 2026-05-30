from ursina import *
from ..config import GRAVITY, PROJECTILE_SPEED, GROUND_Y, STAGE_LEFT, STAGE_RIGHT, GAME_SHADER
from .. import core
from ..fx import burst


class Projectile(Entity):
    def __init__(self, pos):
        super().__init__(model='sphere', scale=0.34,
                         color=color.rgb(150, 95, 60), position=pos, shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(1.05, 0.4, 1.05),
               position=(0, 0.32, 0), color=color.rgb(90, 160, 90), shader=GAME_SHADER)
        dx = core.player.x - self.x
        t  = max(0.45, abs(dx) / PROJECTILE_SPEED)
        self.vel_x = dx / t
        self.vel_y = (GRAVITY * t) / 2.0

    def update(self):
        if core.gs['over']:
            self._kill()
            return
        dt = time.dt
        self.vel_y -= GRAVITY * dt
        self.x     += self.vel_x * dt
        self.y     += self.vel_y * dt
        self.rotation += Vec3(300, 200, 0) * dt

        if abs(self.x - core.player.x) < 0.8 and abs(self.y - core.player.y) < 1.0:
            core.player.take_damage(12, self.x)
            burst(self.world_position, color.rgb(150, 95, 60), count=12, spread=1.5, life=0.4)
            self._kill()
            return

        if self.y <= GROUND_Y - 0.3 or not (STAGE_LEFT - 4 < self.x < STAGE_RIGHT + 4):
            burst(self.world_position, color.rgb(150, 95, 60), count=10, spread=1.2, life=0.4)
            self._kill()

    def _kill(self):
        if self in core.projectiles:
            core.projectiles.remove(self)
        destroy(self)
