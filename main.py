# =============================================================================
#  STREET FACTEUR — main.py
#  Jeu d'action 3D solo (Ursina). Le facteur doit livrer 5 boîtes aux lettres
#  avant la fin du chrono, en survivant aux chiens, voisins et mamies du quartier.
#
#  Architecture (un seul fichier + config.py) :
#    - Setup moteur / lumière / shaders / caméra 2.5D
#    - Helpers FX  : particules, camera shake
#    - Environnement procédural : route, immeubles, lampadaires
#    - Entités     : Player, Dog, Granny, Neighbor, Projectile, Mailbox
#    - HUD         : chrono, compteur courrier, barre de vie, écrans de fin
#    - Boucle      : update() + input() + restart()
#
#  Commandes : Q/D ou Flèches = déplacement · Espace = saut
#              F = attaque · Maj/V = dash · R = recommencer · Échap = quitter
# =============================================================================

import math, random

from ursina import *
from config import *

# ─── MOTEUR ──────────────────────────────────────────────────────────────────
app = Ursina(title='Street Facteur', borderless=False, vsync=True,
             development_mode=False)
window.color           = color.rgb(247, 188, 120)   # ciel chaud de fin de journée
window.fps_counter.enabled = True
window.exit_button.visible = False

# ─── RENDU ────────────────────────────────────────────────────────────────────
# Note : le shader d'ombres temps réel (lit_with_shadows_shader) compile mais ne
# s'affiche pas correctement sur le contexte OpenGL de macOS (scène invisible).
# On rend donc les entités en couleurs « flat » (toujours visibles partout) ; la
# profondeur 3D vient de la caméra perspective et des décors étagés en Z.
GAME_SHADER = None
SHADOWS_ON  = False

# Lumière douce d'ambiance (sans effet sur le rendu flat, mais prête si l'on
# réactive un shader d'éclairage compatible plus tard).
sun = DirectionalLight()
sun.color = color.rgb(255, 246, 220)
try:
    sun.look_at(Vec3(1.5, -2.0, 1.0))
except Exception:
    sun.rotation = Vec3(45, -30, 0)
AmbientLight(color=color.rgba(150, 160, 190, 255))

# ─── CAMÉRA 2.5D ──────────────────────────────────────────────────────────────
CAM_HEIGHT = 5.0      # hauteur de la caméra
CAM_DIST   = -19.0    # recul sur Z
CAM_TILT   = 9.0      # inclinaison vers le bas (accentue la profondeur 3D)
CAM_FOV    = 45
CAM_MARGIN = 4.0      # marge avant les bords de scène
CAM_SMOOTH = 5.0

camera.fov        = CAM_FOV
camera.rotation_x = CAM_TILT
camera.position   = Vec3(0, CAM_HEIGHT, CAM_DIST)

# ─── ÉTAT GLOBAL ──────────────────────────────────────────────────────────────
gs = {'timer': float(LEVEL_TIME), 'mails': 0, 'over': False, 'win': False}

enemies      = []
mailboxes    = []
projectiles  = []
player       = None
hud          = None

PLAYER_HALF = 0.9     # demi-hauteur du joueur (pour le contact au sol)

# ─── FX : CAMERA SHAKE ────────────────────────────────────────────────────────
_cam   = {'x': 0.0}
_shake = {'t': 0.0, 'dur': 0.0, 'mag': 0.0}

def shake_camera(intensity=0.3, duration=0.25):
    # On garde le shake le plus fort en cours (un gros impact ne doit pas être
    # écrasé par un petit qui suit).
    if intensity >= _shake['mag'] or _shake['t'] <= 0:
        _shake['mag'] = intensity
        _shake['dur'] = duration
        _shake['t']   = duration

def update_camera():
    target = clamp(player.x, STAGE_LEFT + CAM_MARGIN, STAGE_RIGHT - CAM_MARGIN)
    _cam['x'] = lerp(_cam['x'], target, CAM_SMOOTH * time.dt)
    ox = oy = 0.0
    if _shake['t'] > 0:
        _shake['t'] -= time.dt
        falloff = max(0.0, _shake['t'] / _shake['dur'])
        m = _shake['mag'] * falloff
        ox = random.uniform(-m, m)
        oy = random.uniform(-m, m)
    camera.x = _cam['x'] + ox
    camera.y = CAM_HEIGHT + oy
    camera.z = CAM_DIST
    # La lumière suit le joueur pour garder les ombres dans le champ utile.
    if SHADOWS_ON:
        sun.position = Vec3(player.x, 14, -6)

# ─── FX : PARTICULES ──────────────────────────────────────────────────────────
def burst(pos, base_color, count=14, spread=2.0, life=0.5, scale=0.18, up=0.6):
    """Petite explosion de cubes éphémères qui s'envolent et disparaissent."""
    for _ in range(count):
        p = Entity(model='cube', color=base_color,
                   scale=random.uniform(scale * 0.5, scale),
                   position=pos, shader=GAME_SHADER)
        d = Vec3(random.uniform(-1, 1),
                 random.uniform(up, up + 1.2),
                 random.uniform(-0.6, 0.6)).normalized() * spread * random.uniform(0.5, 1.2)
        p.animate_position(Vec3(pos) + d, duration=life, curve=curve.out_expo)
        p.animate_scale(0, duration=life, curve=curve.in_quad)
        destroy(p, delay=life + 0.02)

# ─── ENVIRONNEMENT PROCÉDURAL ─────────────────────────────────────────────────
BRICK  = color.rgb(150, 70, 55)
BEIGE  = color.rgb(205, 185, 150)
GREY   = color.rgb(120, 120, 130)
PALETTE = [BRICK, BEIGE, GREY, color.rgb(95, 110, 130), color.rgb(170, 140, 110)]

def build_world():
    """Route, immeubles en profondeur, lampadaires."""
    span   = STAGE_RIGHT - STAGE_LEFT
    center = (STAGE_LEFT + STAGE_RIGHT) / 2

    # Route bitumée (cube épais texturé en damier sombre)
    Entity(model='cube', texture='white_cube',
           texture_scale=(span / 2, 7),
           scale=(span + 10, 1.0, 14),
           position=(center, GROUND_Y - 0.5, 2),
           color=color.rgb(55, 55, 62), shader=GAME_SHADER)

    # Trottoir clair en bord de route (côté joueur)
    Entity(model='cube', scale=(span + 10, 0.2, 2.4),
           position=(center, GROUND_Y - 0.4, -3.0),
           color=color.rgb(140, 140, 145), shader=GAME_SHADER)

    # Marquage central de la chaussée
    for i in range(int(span // 3)):
        Entity(model='cube', scale=(1.1, 0.05, 0.22),
               position=(STAGE_LEFT + 1 + i * 3, GROUND_Y + 0.01, 4.5),
               color=color.rgb(225, 215, 160), shader=GAME_SHADER)

    # Rangée d'immeubles en arrière-plan (profondeur 3D)
    bx = STAGE_LEFT - 2
    while bx < STAGE_RIGHT + 4:
        w  = random.uniform(3.5, 5.5)
        h  = random.uniform(7, 15)
        d  = random.uniform(3.5, 5.0)
        col = random.choice(PALETTE)
        Entity(model='cube', texture='brick', texture_scale=(w, h),
               scale=(w, h, d),
               position=(bx + w / 2, GROUND_Y + h / 2 - 0.5, 9 + d / 2),
               color=col, shader=GAME_SHADER)
        # Quelques fenêtres éclairées
        rows = int(h // 2)
        for r in range(1, rows):
            if random.random() < 0.55:
                Entity(model='cube', scale=(0.6, 0.7, 0.1),
                       position=(bx + w / 2 + random.uniform(-w / 3, w / 3),
                                 GROUND_Y - 0.5 + r * 2, 9 - 0.05),
                       color=color.rgb(255, 225, 140))
        bx += w + random.uniform(0.2, 0.8)

    # Lampadaires décoratifs côté trottoir
    for lx in range(int(STAGE_LEFT) + 3, int(STAGE_RIGHT), 9):
        Entity(model='cube', scale=(0.18, 3.4, 0.18),
               position=(lx, GROUND_Y + 1.2, -2.0),
               color=color.rgb(60, 60, 70), shader=GAME_SHADER)
        Entity(model='cube', scale=(0.9, 0.16, 0.16),
               position=(lx + 0.3, GROUND_Y + 2.85, -2.0),
               color=color.rgb(60, 60, 70), shader=GAME_SHADER)
        Entity(model='sphere', scale=0.35,
               position=(lx + 0.7, GROUND_Y + 2.8, -2.0),
               color=color.rgb(255, 240, 170))


# ─── JOUEUR ───────────────────────────────────────────────────────────────────
class Player(Entity):
    def __init__(self):
        super().__init__(position=Vec3(0, GROUND_Y + PLAYER_HALF, 0))
        self.visual = Entity(parent=self)
        # Torse / jambes / tête / casquette / sacoche
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

        self.atk_cd  = 0.0
        self.dash_cd = 0.0
        self.dash_t  = 0.0
        self.dashing = False
        self.hit_flash = 0.0

        # Stun "mamie"
        self.stunned = False
        self.stun_t  = 0.0
        self.captor  = None
        self._mash   = 0

        # Intentions one-shot (remplies par input())
        self.want_jump   = False
        self.want_attack = False
        self.want_dash   = False

        self.delivery_hold = {}

    # — Stun infligé par la mamie —
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
        if self.dashing or gs['over']:
            return
        self.hp = max(0, self.hp - amount)
        self.hit_flash = 0.12
        if source_x is not None:
            self.vel_x = (1 if self.x > source_x else -1) * 5.0
        shake_camera(0.35, 0.3)
        burst(self.world_position + Vec3(0, 0.4, 0), color.rgb(255, 90, 90),
              count=10, spread=1.4, life=0.35)
        if self.hp <= 0:
            end_game(victory=False)

    def update(self):
        if gs['over']:
            return
        dt = time.dt

        # — Stun mamie : il faut marteler F —
        if self.stunned:
            self.stun_t -= dt
            self.visual.rotation_z = math.sin(time.time() * 30) * 8   # gigote
            if self._mash >= GRANNY_MASH_REQUIRED or self.stun_t <= 0:
                self.visual.rotation_z = 0
                self._free()
            self.want_attack = self.want_jump = self.want_dash = False
            return

        # — Timers —
        self.atk_cd  = max(0.0, self.atk_cd - dt)
        self.dash_cd = max(0.0, self.dash_cd - dt)
        if self.dash_t > 0:
            self.dash_t -= dt
            if self.dash_t <= 0:
                self.dashing = False

        # — Gravité —
        self.vel_y -= GRAVITY * dt
        self.y     += self.vel_y * dt
        floor = GROUND_Y + PLAYER_HALF
        if self.y <= floor:
            self.y = floor
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # — Knockback / dash horizontal —
        if abs(self.vel_x) > 0.05:
            self.x    += self.vel_x * dt
            self.vel_x = lerp(self.vel_x, 0, 8 * dt)

        # — Déplacement clavier —
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

        # — Saut —
        if self.want_jump and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False
        self.want_jump = False

        # — Attaque —
        if self.want_attack and self.atk_cd <= 0 and not self.dashing:
            self._attack()
        self.want_attack = False

        # — Dash —
        if self.want_dash and self.dash_cd <= 0:
            self.dashing = True
            self.dash_t  = DASH_DURATION
            self.dash_cd = DASH_COOLDOWN
            self.vel_x   = self.facing * DASH_SPEED
            burst(self.world_position, color.rgb(200, 220, 255),
                  count=8, spread=1.0, life=0.25, up=0.0)
        self.want_dash = False

        # — Flash de dégâts —
        if self.hit_flash > 0:
            self.hit_flash -= dt

        # — Limites de la rue —
        self.x = clamp(self.x, STAGE_LEFT + 0.5, STAGE_RIGHT - 0.5)

        # — Livraison par proximité —
        self._check_delivery()

    def _attack(self):
        self.atk_cd = ATTACK_COOLDOWN
        self.visual.rotation_z = self.facing * -25
        invoke(setattr, self.visual, 'rotation_z', 0, delay=0.12)

        # Arc de coup : sphère blanche translucide qui grandit puis disparaît
        fx = Entity(model='sphere',
                    position=self.world_position + Vec3(self.facing * 0.9, 0.3, 0),
                    scale=0.3, color=color.white, double_sided=True)
        fx.alpha = 0.4
        fx.animate_scale(ATTACK_RANGE * 1.3, duration=0.12, curve=curve.out_expo)
        fx.animate('alpha', 0, duration=0.12)
        destroy(fx, delay=0.16)

        for e in list(enemies):
            if not getattr(e, 'alive', True) or not getattr(e, 'damageable', True):
                continue
            dx = e.x - self.x
            if dx * self.facing >= -0.4 and abs(dx) < ATTACK_RANGE and abs(e.y - self.y) < 2.2:
                e.hit(ATTACK_DAMAGE, self.x)

    def _check_delivery(self):
        for mb in mailboxes:
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


# ─── ENNEMI : BASE ────────────────────────────────────────────────────────────
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
        self.body      = None    # sous-entité dont on change la couleur au flash

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
        if self in enemies:
            enemies.remove(self)
        burst(self.world_position + Vec3(0, 0.3, 0), self.base_col,
              count=18, spread=2.2, life=0.5)
        self.animate_scale(0, duration=0.35, curve=curve.in_back)
        destroy(self, delay=0.4)


# ─── CHIEN ENRAGÉ ─────────────────────────────────────────────────────────────
class Dog(BaseEnemy):
    def __init__(self, pos):
        super().__init__(pos, DOG_HP, color.rgb(190, 110, 45), half=0.4)
        self.body = Entity(parent=self, model='sphere', scale=(1.1, 0.55, 0.55),
                           color=self.base_col, shader=GAME_SHADER)
        Entity(parent=self, model='sphere', scale=0.5,
               position=(0.55, 0.18, 0), color=color.rgb(205, 130, 60), shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(0.12, 0.2, 0.12),
               position=(0.62, 0.45, 0.13), color=color.rgb(150, 85, 30), shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(0.12, 0.2, 0.12),
               position=(0.62, 0.45, -0.13), color=color.rgb(150, 85, 30), shader=GAME_SHADER)
        for lx in (-0.35, 0.35):
            for lz in (-0.18, 0.18):
                Entity(parent=self, model='cube', scale=(0.13, 0.4, 0.13),
                       position=(lx, -0.42, lz), color=color.rgb(150, 85, 30), shader=GAME_SHADER)
        self.tail = Entity(parent=self, model='cube', scale=(0.12, 0.32, 0.12),
                           position=(-0.6, 0.2, 0), rotation_z=40,
                           color=self.base_col, shader=GAME_SHADER)
        self.center   = pos.x
        self.atk_cd   = 0.0
        self.growl_cd = random.uniform(0.5, 1.5)

    def update(self):
        if not self.alive or gs['over']:
            return
        dt = time.dt
        self.atk_cd   = max(0, self.atk_cd - dt)
        self.growl_cd -= dt
        self._physics()
        self._flash_update()
        self.tail.rotation_z = 40 + math.sin(time.time() * 12) * 25

        dist = abs(player.x - self.x)
        if dist < DOG_DETECT_RANGE and not player.stunned:
            # Charge frénétique
            self.facing = 1 if player.x > self.x else -1
            self.rotation_y = 0 if self.facing > 0 else 180
            self.x += self.facing * DOG_SPEED * dt
            if self.growl_cd <= 0:
                burst(self.world_position + Vec3(self.facing * 0.6, 0.2, 0),
                      color.rgb(220, 220, 220), count=4, spread=0.6, life=0.25, up=0.2)
                self.growl_cd = random.uniform(0.4, 0.9)
            if dist < 1.1 and self.atk_cd <= 0:
                player.take_damage(DOG_ATTACK_DAMAGE, self.x)
                self.atk_cd = 1.0
        else:
            # Patrouille tranquille autour du point de départ
            self.x += self.facing * DOG_SPEED * 0.4 * dt
            if abs(self.x - self.center) > 3.0:
                self.facing *= -1
                self.rotation_y = 0 if self.facing > 0 else 180


# ─── MAMIE BAVARDE (piège d'immobilisation) ───────────────────────────────────
class Granny(BaseEnemy):
    damageable = False    # immortelle : c'est un piège, pas une cible

    def __init__(self, pos):
        super().__init__(pos, 9999, color.rgb(170, 95, 185), half=0.65)
        self.body = Entity(parent=self, model='cube', scale=(0.65, 1.0, 0.5),
                           color=self.base_col, shader=GAME_SHADER)
        Entity(parent=self, model='sphere', scale=0.42,
               position=(0, 0.72, 0), color=color.rgb(235, 205, 195), shader=GAME_SHADER)
        Entity(parent=self, model='sphere', scale=0.34,
               position=(0, 0.95, -0.05), color=color.rgb(220, 220, 225), shader=GAME_SHADER)  # chignon
        self.bubble = Text("Mon petit,\nà mon époque...",
                           parent=self, position=(0.7, 1.5, 0), scale=10,
                           color=color.black, background=True, billboard=True,
                           enabled=False)
        self.cd       = 0.0
        self.grabbing = None

    def update(self):
        if gs['over']:
            return
        dt = time.dt
        self.cd = max(0, self.cd - dt)

        if self.grabbing:
            # Maintient le joueur collé à elle pendant le monologue
            player.x = self.x + 1.1
            player.y = GROUND_Y + PLAYER_HALF
            if not player.stunned:           # le joueur s'est libéré
                self.release()
        elif self.cd <= 0 and not player.stunned:
            if abs(player.x - self.x) < GRANNY_RANGE and player.on_ground:
                self.grabbing = player
                self.bubble.enabled = True
                player.grab(self)

    def release(self):
        self.grabbing = None
        self.bubble.enabled = False
        self.cd = 3.0


# ─── VOISIN GRINCHEUX (lanceur de pots de fleurs) ─────────────────────────────
class Neighbor(BaseEnemy):
    def __init__(self, pos):
        super().__init__(Vec3(pos.x, 2.5, pos.z), NEIGHBOR_HP, color.rgb(170, 75, 75), half=0.5)
        # Balcon sur lequel il est posté
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
        if not self.alive or gs['over']:
            return
        dt = time.dt
        self.cd = max(0, self.cd - dt)
        self._flash_update()

        if player.stunned:
            return
        self.facing = 1 if player.x > self.x else -1
        if self.cd <= 0 and abs(player.x - self.x) < 16:
            self.arm.rotation_z = -35
            invoke(setattr, self.arm, 'rotation_z', 55, delay=0.18)
            projectiles.append(Projectile(self.world_position + Vec3(self.facing * 0.5, 0.1, 0)))
            self.cd = NEIGHBOR_COOLDOWN


# ─── PROJECTILE (pot de fleurs lancé en cloche) ───────────────────────────────
class Projectile(Entity):
    def __init__(self, pos):
        super().__init__(model='sphere', scale=0.34,
                         color=color.rgb(150, 95, 60), position=pos, shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(1.05, 0.4, 1.05),
               position=(0, 0.32, 0), color=color.rgb(90, 160, 90), shader=GAME_SHADER)  # plante
        # Vitesse balistique visant la position courante du joueur (tir en cloche)
        dx = player.x - self.x
        t  = max(0.45, abs(dx) / PROJECTILE_SPEED)
        self.vel_x = dx / t
        self.vel_y = (GRAVITY * t) / 2.0          # arc qui retombe ~au niveau du joueur

    def update(self):
        if gs['over']:
            self._kill(); return
        dt = time.dt
        self.vel_y -= GRAVITY * dt
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.rotation += Vec3(300, 200, 0) * dt

        if abs(self.x - player.x) < 0.8 and abs(self.y - player.y) < 1.0:
            player.take_damage(12, self.x)
            burst(self.world_position, color.rgb(150, 95, 60), count=12, spread=1.5, life=0.4)
            self._kill(); return

        if self.y <= GROUND_Y - 0.3 or not (STAGE_LEFT - 4 < self.x < STAGE_RIGHT + 4):
            burst(self.world_position, color.rgb(150, 95, 60), count=10, spread=1.2, life=0.4)
            self._kill()

    def _kill(self):
        if self in projectiles:
            projectiles.remove(self)
        destroy(self)


# ─── BOÎTE AUX LETTRES ────────────────────────────────────────────────────────
class Mailbox(Entity):
    def __init__(self, pos):
        super().__init__(position=pos)
        self.delivered = False
        Entity(parent=self, model='cube', scale=(0.12, 1.0, 0.12),
               position=(0, 0.0, 0), color=color.rgb(60, 60, 70), shader=GAME_SHADER)  # pied
        self.box = Entity(parent=self, model='cube', scale=(0.55, 0.7, 0.45),
                          position=(0, 0.7, 0), color=color.rgb(235, 195, 50), shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(0.6, 0.12, 0.5),
               position=(0, 1.0, 0), color=color.rgb(210, 170, 40), shader=GAME_SHADER)  # toit
        Entity(parent=self, model='cube', scale=(0.3, 0.04, 0.05),
               position=(0, 0.78, 0.24), color=color.black)  # fente
        # Jauge de progression flottante
        self.prog_bg = Entity(parent=self, model='quad', scale=(0.7, 0.1),
                              position=(0, 1.5, 0), color=color.rgb(30, 30, 35),
                              billboard=True)
        self.prog = Entity(parent=self.prog_bg, model='quad', scale=(0.96, 0.7),
                           origin=(-0.5, 0), position=(-0.48, 0, -0.01), color=color.lime)
        self.prog.scale_x = 0
        self.prog_bg.enabled = False

    def set_progress(self, ratio):
        ratio = clamp(ratio, 0, 1)
        self.prog_bg.enabled = 0 < ratio < 1
        self.prog.scale_x = 0.96 * ratio

    def deliver(self):
        if self.delivered:
            return
        self.delivered = True
        self.prog_bg.enabled = False
        self.box.color = color.rgb(60, 220, 90)
        self.box.animate_scale((0.7, 0.9, 0.6), duration=0.12)
        invoke(self.box.animate_scale, (0.55, 0.7, 0.45), delay=0.12, duration=0.12)
        burst(self.world_position + Vec3(0, 1.0, 0), color.rgb(255, 230, 90),
              count=26, spread=2.6, life=0.6)
        burst(self.world_position + Vec3(0, 1.0, 0), color.lime,
              count=20, spread=2.2, life=0.6)
        t = Text(f"+{int(TIME_BONUS)}s", position=self.world_position + Vec3(0, 1.8, -0.5),
                 scale=3, color=color.lime, billboard=True)
        t.animate_position(self.world_position + Vec3(0, 2.8, -0.5), duration=1.0)
        destroy(t, delay=1.0)

        gs['mails'] += 1
        gs['timer'] += TIME_BONUS
        if gs['mails'] >= TOTAL_MAILBOXES:
            end_game(victory=True)


# ─── HUD ──────────────────────────────────────────────────────────────────────
class HUD:
    def __init__(self):
        self.timer = Text(str(int(LEVEL_TIME)), parent=camera.ui,
                          position=(0, 0.46), origin=(0, 0), scale=2.6, color=color.white)
        self.mails = Text(f"COURRIER  0 / {TOTAL_MAILBOXES}", parent=camera.ui,
                          position=(-0.86, 0.46), origin=(-0.5, 0), scale=1.3,
                          color=color.rgb(255, 230, 120))

        self.hp_bg = Entity(parent=camera.ui, model='quad', scale=(0.34, 0.04),
                            position=(-0.69, -0.45), color=color.rgb(25, 25, 30))
        self.hp_bar = Entity(parent=camera.ui, model='quad', scale=(0.33, 0.03),
                             origin=(-0.5, 0), position=(-0.855, -0.45), color=color.red)
        Text("FACTEUR", parent=camera.ui, position=(-0.855, -0.41),
             origin=(-0.5, 0), scale=0.9, color=color.white)

        # Overlay de fin (caché par défaut)
        self.overlay = Entity(parent=camera.ui, model='quad', scale=(4, 2),
                              color=color.rgba(0, 0, 0, 200), enabled=False)
        self.end_txt = Text("", parent=camera.ui, position=(0, 0.05), origin=(0, 0),
                            scale=1.8, color=color.white, enabled=False)
        self._blink = 0.0

    def update(self):
        secs = max(0, int(math.ceil(gs['timer'])))
        self.timer.text = str(secs)
        if gs['timer'] < 15:
            self._blink += time.dt
            self.timer.color   = color.red
            self.timer.enabled = int(self._blink * 4) % 2 == 0
        else:
            self.timer.color   = color.white
            self.timer.enabled = True

        self.mails.text = f"COURRIER  {gs['mails']} / {TOTAL_MAILBOXES}"

        ratio = clamp(player.hp / PLAYER_HP, 0, 1)
        self.hp_bar.scale_x = 0.33 * ratio
        self.hp_bar.color   = color.red if ratio > 0.3 else color.orange

    def show_end(self, msg, col):
        self.overlay.enabled = True
        self.end_txt.text    = msg
        self.end_txt.color   = col
        self.end_txt.enabled = True

    def reset(self):
        self.overlay.enabled = False
        self.end_txt.enabled = False
        self._blink = 0.0


# ─── CONSTRUCTION DU NIVEAU ───────────────────────────────────────────────────
def build_level():
    global player
    player = Player()

    for x in (10, 26, 44):
        enemies.append(Dog(Vec3(x, GROUND_Y + 0.4, 0)))
    for x in (16, 38):
        enemies.append(Granny(Vec3(x, GROUND_Y + 0.65, 0)))
    for x in (22, 50):
        enemies.append(Neighbor(Vec3(x, 0, 8)))

    for x in (8, 20, 32, 46, 56):
        mailboxes.append(Mailbox(Vec3(x, GROUND_Y, -1.2)))


# ─── BOUCLE PRINCIPALE ────────────────────────────────────────────────────────
def update():
    if gs['over'] or player is None:
        return
    gs['timer'] -= time.dt
    if gs['timer'] <= 0:
        gs['timer'] = 0
        end_game(victory=False)
        return
    update_camera()
    hud.update()


def end_game(victory):
    if gs['over']:
        return
    gs['over'] = True
    gs['win']  = victory
    if victory:
        hud.show_end(
            "LE COURRIER EST ARRIVÉ À L'HEURE !\n\nFélicitations, Facteur.\n\n[ R ] pour recommencer",
            color.rgb(120, 255, 140))
    else:
        hud.show_end(
            "TOURNÉE RATÉE !\n\nLe quartier a eu raison de vous.\n\n[ R ] pour recommencer",
            color.rgb(255, 110, 110))


def input(key):
    if key == 'escape':
        application.quit()
        return
    if gs['over']:
        if key in ('r', 'R'):
            restart()
        return
    if player is None:
        return
    if key == 'space':
        player.want_jump = True
    elif key == 'f':
        if player.stunned:
            player.mash()
        else:
            player.want_attack = True
    elif key in ('v', 'left shift', 'right shift'):
        player.want_dash = True


# ─── REDÉMARRAGE ──────────────────────────────────────────────────────────────
def restart():
    global player
    # On détruit toutes les entités de scène sauf la lumière directionnelle.
    for e in scene.entities[:]:
        if e is sun:
            continue
        destroy(e)
    enemies.clear()
    mailboxes.clear()
    projectiles.clear()
    player = None

    gs.update({'timer': float(LEVEL_TIME), 'mails': 0, 'over': False, 'win': False})
    _cam['x'] = 0.0

    build_world()
    build_level()
    hud.reset()


# ─── LANCEMENT ────────────────────────────────────────────────────────────────
build_world()
build_level()
hud = HUD()
app.run()
