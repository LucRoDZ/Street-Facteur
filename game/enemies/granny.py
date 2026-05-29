from ursina import Entity, color, time, Text, Vec3, destroy
import config
from game.states import PlayerState
from game.enemies.base_enemy import BaseEnemy

class Granny(BaseEnemy):
    def __init__(self, position):
        self.grab_cooldown = 0.0
        self.currently_grabbing = None
        self.grab_timer = 0.0
        self.dialogue = None

        super().__init__(
            position=position,
            hp=999,
            color_val=color.rgb(160, 100, 160),
            model='cube',
            scale=(0.6, 0.9, 0.5)
        )

        # Head
        Entity(
            parent=self,
            model='cube',
            scale=(0.4, 0.4, 0.4),
            color=color.rgb(230, 200, 200),
            position=(0, 0.65, 0)
        )
        # Bun (chignon)
        Entity(
            parent=self,
            model='cube',
            scale=(0.35, 0.25, 0.35),
            color=color.rgb(220, 220, 220),
            position=(0, 0.95, 0)
        )

    def update(self):
        super().update()
        self.grab_cooldown -= time.dt

        if not self.currently_grabbing and self.grab_cooldown <= 0:
            active_players = [p for p in getattr(self, 'players', []) if p.state != PlayerState.KO]
            for player in active_players:
                if player.state not in (PlayerState.GRABBED, PlayerState.KO, PlayerState.DASH):
                    dist = abs(player.x - self.x)
                    if dist < config.GRANNY_GRAB_RANGE:
                        player.state = PlayerState.GRABBED
                        player.granny_hits = 0
                        self.currently_grabbing = player
                        self.grab_timer = config.GRANNY_GRAB_DURATION
                        self.grab_cooldown = config.GRANNY_GRAB_COOLDOWN

                        self.dialogue = Text(
                            text="Ah ! Mon petit, tu sais, en 1965...",
                            parent=self,
                            y=1.8,
                            scale=1.2,
                            color=color.white
                        )
                        break

        if self.currently_grabbing:
            self.grab_timer -= time.dt
            self.facing = 1 if self.currently_grabbing.x > self.x else -1
            self.currently_grabbing.position = self.position + Vec3(self.facing * 1.0, 0, 0)

            if self.grab_timer <= 0 or self.currently_grabbing.state != PlayerState.GRABBED:
                if self.currently_grabbing.state == PlayerState.GRABBED:
                    self.currently_grabbing.state = PlayerState.IDLE
                self.currently_grabbing = None
                if self.dialogue:
                    destroy(self.dialogue)
                    self.dialogue = None

    def take_damage(self, amount, attacker=None):
        if self.currently_grabbing == attacker and attacker:
            attacker.try_break_grab()
        # Granny is immortal
