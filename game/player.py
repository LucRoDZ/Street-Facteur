import config
from ursina import Entity, Vec3, color, time, sin, clamp, lerp
from game.states import PlayerState, EnemyState
from game.input_manager import InputManager

_P1_BODY_COLOR = color.rgb(30, 100, 200)
_P1_CAP_COLOR  = color.rgb(20, 60, 140)
_P2_BODY_COLOR = color.rgb(200, 100, 20)
_P2_CAP_COLOR  = color.rgb(140, 60, 10)
_BAG_COLOR     = color.rgb(180, 140, 50)

_BASE_SCALE = Vec3(0.7, 1.1, 0.5)

class Player(Entity):
    def __init__(self, player_id, position, color_val, **kwargs):
        self.player_id = player_id
        body_color = _P1_BODY_COLOR if player_id == 1 else _P2_BODY_COLOR
        self.base_color = body_color
        self.game_state = None

        super().__init__(
            model='cube',
            scale=_BASE_SCALE,
            position=position,
            color=body_color,
            **kwargs
        )

        # Cap
        cap_color = _P1_CAP_COLOR if player_id == 1 else _P2_CAP_COLOR
        self.cap = Entity(
            parent=self,
            model='cube',
            scale=(0.85, 0.2, 0.6),
            color=cap_color,
            position=(0, 0.65, 0)
        )
        # Bag
        self.bag = Entity(
            parent=self,
            model='cube',
            scale=(0.35, 0.3, 0.3),
            color=_BAG_COLOR,
            position=(0.45, -0.1, 0)
        )
        # Attack indicator
        self.attack_indicator = Entity(
            parent=self,
            model='cube',
            scale=0.3,
            color=color.Color(1.0, 1.0, 1.0, 0.5),
            enabled=False
        )

        self.hp = config.PLAYER_HP
        self.max_hp = config.PLAYER_HP
        self.state = PlayerState.IDLE

        self.velocity_y = 0.0
        self.velocity_x = 0.0
        self.on_ground = False

        self.attack_timer = 0.0
        self.attack_cooldown_timer = 0.0
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        self.ko_timer = 0.0
        self.flash_timer = 0.0

        self.facing = 1
        self.input_manager = InputManager(player_id)
        self.granny_hits = 0

    def update(self):
        self._handle_physics()
        self._handle_input()
        self._handle_timers()
        self._handle_animation()
        self._clamp_to_stage()

    def _handle_physics(self):
        if not self.on_ground:
            self.velocity_y -= config.GRAVITY * time.dt
        self.position.y += self.velocity_y * time.dt

        if self.position.y <= config.GROUND_Y + config.PLAYER_HEIGHT / 2:
            self.position.y = config.GROUND_Y + config.PLAYER_HEIGHT / 2
            self.velocity_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        if self.velocity_x != 0:
            self.position.x += self.velocity_x * time.dt
            self.velocity_x = lerp(self.velocity_x, 0.0, 10.0 * time.dt)
            if abs(self.velocity_x) < 0.01:
                self.velocity_x = 0.0

    def _handle_input(self):
        from ursina import held_keys

        if self.state == PlayerState.GRABBED:
            actions = self.input_manager.get_actions(held_keys)
            if actions['attack']:
                if self.game_state and self.game_state.level:
                    for enemy in self.game_state.level.enemies:
                        if hasattr(enemy, 'currently_grabbing') and enemy.currently_grabbing == self:
                            enemy.take_damage(0, self)
            return

        if self.state == PlayerState.KO:
            return

        actions = self.input_manager.get_actions(held_keys)

        moved = False
        if actions['left'] and self.state != PlayerState.DASH:
            self.position.x -= config.MOVE_SPEED * time.dt
            self.facing = -1
            if self.on_ground and self.state != PlayerState.ATTACK:
                self.state = PlayerState.WALK
            moved = True
        elif actions['right'] and self.state != PlayerState.DASH:
            self.position.x += config.MOVE_SPEED * time.dt
            self.facing = 1
            if self.on_ground and self.state != PlayerState.ATTACK:
                self.state = PlayerState.WALK
            moved = True

        if not moved and self.on_ground and self.state == PlayerState.WALK:
            self.state = PlayerState.IDLE

        if actions['jump'] and self.on_ground and self.state != PlayerState.DASH:
            self.velocity_y = config.JUMP_FORCE
            self.on_ground = False
            self.state = PlayerState.JUMP

        if actions['attack'] and self.attack_cooldown_timer <= 0 and self.state != PlayerState.DASH:
            self.state = PlayerState.ATTACK
            self.attack_timer = config.ATTACK_DURATION
            self.attack_cooldown_timer = config.ATTACK_COOLDOWN
            self.attack_indicator.x = self.facing * 1.0
            self.attack_indicator.enabled = True
            self.trigger_attack()

        if actions['dash'] and self.dash_cooldown_timer <= 0:
            self.state = PlayerState.DASH
            self.dash_timer = config.DASH_DURATION
            self.dash_cooldown_timer = config.DASH_COOLDOWN
            self.velocity_x = self.facing * config.DASH_SPEED

    def trigger_attack(self):
        from game.combat import check_melee_hit
        if self.game_state and self.game_state.level:
            targets = [e for e in self.game_state.level.enemies if hasattr(e, 'state') and e.state != EnemyState.KO]
            hits = check_melee_hit(self, targets)
            for hit in hits:
                hit.take_damage(config.ATTACK_DAMAGE, self)

    def _handle_timers(self):
        if self.attack_timer > 0:
            self.attack_timer -= time.dt
            if self.attack_timer <= 0 and self.state == PlayerState.ATTACK:
                self.state = PlayerState.IDLE
                self.attack_indicator.enabled = False

        if self.attack_cooldown_timer > 0:
            self.attack_cooldown_timer -= time.dt

        if self.dash_timer > 0:
            self.dash_timer -= time.dt
            if self.dash_timer <= 0 and self.state == PlayerState.DASH:
                self.state = PlayerState.IDLE

        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= time.dt

        if self.ko_timer > 0:
            self.ko_timer -= time.dt
            if self.ko_timer <= 0 and self.state == PlayerState.KO:
                self.state = PlayerState.IDLE
                self.hp = self.max_hp
                self.rotation_z = 0
                self.scale = _BASE_SCALE

    def _handle_animation(self):
        if self.state != PlayerState.KO:
            self.rotation_z = 0

        if self.state == PlayerState.IDLE:
            self.scale = _BASE_SCALE
        elif self.state == PlayerState.WALK:
            self.scale = _BASE_SCALE
            if self.on_ground:
                self.y = (config.GROUND_Y + config.PLAYER_HEIGHT / 2) + sin(time.time() * 10) * 0.03
        elif self.state == PlayerState.JUMP:
            self.scale = Vec3(0.7, 1.15, 0.5)
        elif self.state == PlayerState.ATTACK:
            self.scale = _BASE_SCALE
            self.rotation_z = self.facing * -20
        elif self.state == PlayerState.DASH:
            self.scale = Vec3(1.4, 1.1, 0.5)
        elif self.state == PlayerState.KO:
            self.rotation_z = 90
            self.scale = Vec3(1.1, 0.7, 0.5)

        if self.flash_timer > 0:
            self.flash_timer -= time.dt
            self.color = color.white
            if self.flash_timer <= 0:
                self.color = self.base_color

    def take_damage(self, amount, attacker=None):
        if self.state == PlayerState.DASH or self.state == PlayerState.KO:
            return
        self.hp -= amount
        self.flash_timer = 0.08
        if attacker:
            from game.combat import apply_knockback
            apply_knockback(self, attacker, config.KNOCKBACK_FORCE)
        if self.hp <= 0:
            self.enter_ko()

    def enter_ko(self):
        self.hp = 0
        self.state = PlayerState.KO
        self.ko_timer = config.KO_DURATION
        if self.game_state:
            self.game_state.on_ko()

    def try_break_grab(self):
        self.granny_hits += 1
        if self.granny_hits >= config.GRANNY_BREAK_HITS:
            self.state = PlayerState.IDLE
            self.granny_hits = 0

    def _clamp_to_stage(self):
        self.position.x = clamp(self.position.x, config.STAGE_LEFT + 0.5, config.STAGE_RIGHT - 0.5)
