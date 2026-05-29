from ursina import Entity, color, time, invoke
import config
from game.states import EnemyState, PlayerState
from game.enemies.base_enemy import BaseEnemy
from game.projectile import Projectile

class Neighbor(BaseEnemy):
    def __init__(self, position):
        super().__init__(
            position=position,
            hp=config.NEIGHBOR_HP,
            color_val=color.rgb(150, 80, 80),
            model='cube',
            scale=(0.6, 0.7, 0.4)
        )

        self.gravity_enabled = False
        self.position.y = 1.5
        self.throw_cooldown = config.NEIGHBOR_THROW_COOLDOWN

        # Window frame behind the neighbor
        Entity(
            parent=self,
            model='cube',
            scale=(1.2, 1.4, 0.2),
            color=color.rgb(80, 120, 160),
            position=(0, 0, 0.2)
        )
        # Raised arm (throw pose)
        Entity(
            parent=self,
            model='cube',
            scale=(0.2, 0.6, 0.2),
            color=color.rgb(200, 150, 100),
            position=(0.45, 0.2, 0),
            rotation_z=-45
        )

    def update(self):
        super().update()
        if self.state == EnemyState.KO:
            return

        self.throw_cooldown -= time.dt

        active_players = [p for p in getattr(self, 'players', []) if p.state != PlayerState.KO]
        if self.throw_cooldown <= 0 and active_players:
            player_proche = min(active_players, key=lambda p: abs(p.x - self.x))
            self.facing = 1 if player_proche.x > self.x else -1

            proj = Projectile(position=self.position, direction=self.facing)
            proj.players = active_players

            self.throw_cooldown = config.NEIGHBOR_THROW_COOLDOWN

            self.rotation_z = self.facing * 30
            invoke(self.reset_throw_rotation, delay=0.3)

    def reset_throw_rotation(self):
        if self.state != EnemyState.KO:
            self.rotation_z = 0
