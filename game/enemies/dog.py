from ursina import Entity, color, time
import config
from game.states import EnemyState, PlayerState
from game.enemies.base_enemy import BaseEnemy

class Dog(BaseEnemy):
    def __init__(self, position):
        self.patrol_center = position.x
        self.patrol_range = 3.0
        self.attack_cooldown = 0.0

        super().__init__(
            position=position,
            hp=config.DOG_HP,
            color_val=color.rgb(180, 120, 40),
            model='cube',
            scale=(0.9, 0.5, 0.5)
        )

        self.enemy_height = 0.5

        # Head
        Entity(
            parent=self,
            model='cube',
            scale=(0.45, 0.45, 0.45),
            color=color.rgb(200, 140, 50),
            position=(0.55, 0.2, 0)
        )
        # Tail
        Entity(
            parent=self,
            model='cube',
            scale=(0.15, 0.4, 0.15),
            color=color.rgb(180, 120, 40),
            position=(-0.55, 0.3, 0),
            rotation_z=30
        )

    def update(self):
        super().update()
        if self.state == EnemyState.KO:
            return

        active_players = [p for p in getattr(self, 'players', []) if p.state != PlayerState.KO]

        player_proche = None
        dist = float('inf')
        if active_players:
            player_proche = min(active_players, key=lambda p: abs(p.x - self.x))
            dist = abs(player_proche.x - self.x)

        if player_proche and dist < config.DOG_DETECT_RANGE:
            self.state = EnemyState.CHASE
        else:
            if self.state in (EnemyState.CHASE, EnemyState.ATTACK):
                self.state = EnemyState.PATROL
                self.patrol_center = self.x

        if self.state == EnemyState.PATROL or not player_proche:
            if self.x > self.patrol_center + self.patrol_range:
                self.facing = -1
            elif self.x < self.patrol_center - self.patrol_range:
                self.facing = 1
            self.position.x += self.facing * config.DOG_SPEED * time.dt

        elif self.state == EnemyState.CHASE:
            self.facing = 1 if player_proche.x > self.x else -1
            self.position.x += self.facing * config.DOG_SPEED * time.dt

            if dist < config.DOG_ATTACK_RANGE and self.attack_cooldown <= 0:
                self.state = EnemyState.ATTACK
                player_proche.take_damage(config.DOG_ATTACK_DAMAGE, self)
                self.attack_cooldown = config.DOG_ATTACK_COOLDOWN

        if self.attack_cooldown > 0:
            self.attack_cooldown -= time.dt
