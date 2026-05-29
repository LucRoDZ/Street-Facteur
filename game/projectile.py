from ursina import Entity, color, time, destroy, distance
import config
from game.states import PlayerState

class Projectile(Entity):
    def __init__(self, position, direction, **kwargs):
        super().__init__(
            model='cube',
            scale=(0.4, 0.3, 0.1),
            color=color.rgb(220, 200, 150),
            position=position,
            **kwargs
        )
        self.direction = direction
        self.travel = 0.0
        self.players = []

    def update(self):
        self.rotation_z += 200 * time.dt

        dx = self.direction * config.NEIGHBOR_PROJECTILE_SPEED * time.dt
        self.position.x += dx
        self.travel += abs(dx)

        if self.travel > 10.0:
            destroy(self)
            return

        for player in self.players:
            if distance(self.position, player.position) < 0.8 and player.state not in (PlayerState.DASH, PlayerState.KO):
                player.take_damage(config.NEIGHBOR_PROJECTILE_DAMAGE, self)
                destroy(self)
                return
