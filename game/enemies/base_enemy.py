from ursina import Entity, color, time, lerp, destroy, invoke, Vec3
import config
from game.states import EnemyState

class BaseEnemy(Entity):
    def __init__(self, position, hp, color_val, **kwargs):
        self.base_color = color_val
        self.hp = hp
        self.max_hp = hp
        self.state = EnemyState.IDLE
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = False
        self.facing = 1
        self.flash_timer = 0.0
        self.gravity_enabled = True
        self.enemy_height = 1.0

        super().__init__(position=position, color=color_val, **kwargs)

    def _handle_physics(self):
        if self.gravity_enabled:
            if not self.on_ground:
                self.velocity_y -= config.GRAVITY * time.dt
            self.position.y += self.velocity_y * time.dt

            if self.position.y <= config.GROUND_Y + self.enemy_height / 2:
                self.position.y = config.GROUND_Y + self.enemy_height / 2
                self.velocity_y = 0
                self.on_ground = True
            else:
                self.on_ground = False
        else:
            self.on_ground = True

        if self.velocity_x != 0:
            self.position.x += self.velocity_x * time.dt
            self.velocity_x = lerp(self.velocity_x, 0.0, 10.0 * time.dt)
            if abs(self.velocity_x) < 0.01:
                self.velocity_x = 0.0

    def update(self):
        self._handle_physics()
        if self.flash_timer > 0:
            self.flash_timer -= time.dt
            self.color = color.red
            if self.flash_timer <= 0:
                self.color = self.base_color

    def take_damage(self, amount, attacker=None):
        if self.state == EnemyState.KO:
            return
        self.hp -= amount
        self.flash_timer = 0.1
        if attacker:
            from game.combat import apply_knockback
            apply_knockback(self, attacker, 2.0)
        if self.hp <= 0:
            self.enter_ko()

    def enter_ko(self):
        self.state = EnemyState.KO
        self.rotation_z = 90
        self.animate_scale(Vec3(1.5, 0.1, 1.5), duration=0.3)
        invoke(destroy, self, delay=2.0)
