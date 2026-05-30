import math
from ursina import *
from ..config import *
from .. import core
from ..fx import burst, shake_camera


class Player(Entity):
    def __init__(self):
        super().__init__(position=Vec3(0, GROUND_Y + PLAYER_HALF, 0))
        self.visual = Entity(parent=self)
        Entity(parent=self.visual, model='cube', scale=(0.6, 0.85, 0.42),
               position=(0, 0.08, 0), color=color.rgb(40, 95, 200), shader=GAME_SHADER)
        Entity(parent=self.visual, model='cube', scale=(0.24, 0.55, 0.26),
               position=(-0.16, -0.62, 0), color=color.rgb(35, 40, 60), shader=GAME_SHADER)
        Entity(parent=self.visual, model='cube', scale=(0.24, 0.55, 0.26),
               position=(0.16, -0.62, 0), color=color.rgb(35, 40, 60), shader=GAME_SHADER)
        Entity(parent=self.visual, model='sphere', scale=0.42,
               position=(0, 0.72, 0), color=color.rgb(235, 195, 165), shader=GAME_SHADER)
        Entity(parent=self.visual, model='cube', scale=(0.5, 0.18, 0.5),
               position=(0, 0.92, 0), color=color.rgb(20, 55, 130), shader=GAME_SHADER)
        Entity(parent=self.visual, model='cube', scale=(0.55, 0.06, 0.18),
               position=(0, 0.9, 0.28), color=color.rgb(20, 55, 130), shader=GAME_SHADER)
        self.bag = Entity(parent=self.visual, model='cube', scale=(0.32, 0.38, 0.26),
                          position=(-0.42, 0.0, 0), color=color.rgb(235, 200, 60),
                          shader=GAME_SHADER)

        self.hp        = PLAYER_HP
        self.facing    = 1
        self.vel_x     = 0.0
        self.vel_y     = 0.0
        self.on_ground = True

        self.atk_cd    = 0.0
        self.dash_cd   = 0.0
        self.dash_t    = 0.0
        self.dashing   = False
        self.hit_flash = 0.0

        self.stunned = False
        self.stun_t  = 0.0
        self.captor  = None
        self._mash   = 0

        self.want_jump   = False
        self.want_attack = False
        self.want_dash   = False

        self.delivery_hold = {}

    def grab(self, captor):
        self.stunned = True
        self.stun_t  = GRANNY_STUN_DURATION
        self.captor  = captor
        self._mash   = 0

    def mash(self):
        self._mash += 1

    def _free(self):
        self.stunned = False
        self.stun_t  = 0.0
        self._mash   = 0
        if self.captor:
            self.captor.release()
            self.captor = None

    def take_damage(self, amount, source_x=None):
        if self.dashing or core.gs['over']:
            return
        self.hp = max(0, self.hp - amount)
        self.hit_flash = 0.12
        if source_x is not None:
            self.vel_x = (1 if self.x > source_x else -1) * 5.0
        shake_camera(0.35, 0.3)
        burst(self.world_position + Vec3(0, 0.4, 0), color.rgb(255, 90, 90),
              count=10, spread=1.4, life=0.35)
        if self.hp <= 0:
            core.end_game(victory=False)

    def update(self):
        if core.gs['over']:
            return
        dt = time.dt

        if self.stunned:
            self.stun_t -= dt
            self.visual.rotation_z = math.sin(time.time() * 30) * 8
            if self._mash >= GRANNY_MASH_REQUIRED or self.stun_t <= 0:
                self.visual.rotation_z = 0
                self._free()
            self.want_attack = self.want_jump = self.want_dash = False
            return

        self.atk_cd  = max(0.0, self.atk_cd - dt)
        self.dash_cd = max(0.0, self.dash_cd - dt)
        if self.dash_t > 0:
            self.dash_t -= dt
            if self.dash_t <= 0:
                self.dashing = False

        self.vel_y -= GRAVITY * dt
        self.y     += self.vel_y * dt
        floor = GROUND_Y + PLAYER_HALF
        if self.y <= floor:
            self.y = floor
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        if abs(self.vel_x) > 0.05:
            self.x    += self.vel_x * dt
            self.vel_x = lerp(self.vel_x, 0, 8 * dt)

        move = 0
        if held_keys['q'] or held_keys['a'] or held_keys['left arrow']:
            move -= 1
        if held_keys['d'] or held_keys['right arrow']:
            move += 1
        if move != 0 and not self.dashing:
            self.x     += move * MOVE_SPEED * dt
            self.facing = move
            self.visual.rotation_y = lerp(self.visual.rotation_y, 25 * move, 12 * dt)
            self.bag.x  = -0.42 * move
            if self.on_ground:
                self.visual.y = abs(math.sin(time.time() * 11)) * 0.07
        else:
            self.visual.y = lerp(self.visual.y, 0, 10 * dt)

        if self.want_jump and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False
        self.want_jump = False

        if self.want_attack and self.atk_cd <= 0 and not self.dashing:
            self._attack()
        self.want_attack = False

        if self.want_dash and self.dash_cd <= 0:
            self.dashing = True
            self.dash_t  = DASH_DURATION
            self.dash_cd = DASH_COOLDOWN
            self.vel_x   = self.facing * DASH_SPEED
            burst(self.world_position, color.rgb(200, 220, 255),
                  count=8, spread=1.0, life=0.25, up=0.0)
        self.want_dash = False

        if self.hit_flash > 0:
            self.hit_flash -= dt

        self.x = clamp(self.x, STAGE_LEFT + 0.5, STAGE_RIGHT - 0.5)
        self._check_delivery()

    def _attack(self):
        self.atk_cd = ATTACK_COOLDOWN
        self.visual.rotation_z = self.facing * -25
        invoke(setattr, self.visual, 'rotation_z', 0, delay=0.12)

        fx = Entity(model='sphere',
                    position=self.world_position + Vec3(self.facing * 0.9, 0.3, 0),
                    scale=0.3, color=color.white, double_sided=True)
        fx.alpha = 0.4
        fx.animate_scale(ATTACK_RANGE * 1.3, duration=0.12, curve=curve.out_expo)
        fx.animate('alpha', 0, duration=0.12)
        destroy(fx, delay=0.16)

        for e in list(core.enemies):
            if not getattr(e, 'alive', True) or not getattr(e, 'damageable', True):
                continue
            dx = e.x - self.x
            if dx * self.facing >= -0.4 and abs(dx) < ATTACK_RANGE and abs(e.y - self.y) < 2.2:
                e.hit(ATTACK_DAMAGE, self.x)

    def _check_delivery(self):
        for mb in core.mailboxes:
            if mb.delivered:
                continue
            mid = id(mb)
            if abs(mb.x - self.x) < 1.8 and abs(self.y - (GROUND_Y + PLAYER_HALF)) < 1.2:
                self.delivery_hold[mid] = self.delivery_hold.get(mid, 0) + time.dt
                mb.set_progress(self.delivery_hold[mid] / DELIVERY_HOLD_TIME)
                if self.delivery_hold[mid] >= DELIVERY_HOLD_TIME:
                    mb.deliver()
            elif mid in self.delivery_hold:
                del self.delivery_hold[mid]
                mb.set_progress(0)
