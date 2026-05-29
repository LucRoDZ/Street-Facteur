# =============================================================================#  STREET FACTEUR — main.py (version autonome, zéro dépendance sur game/)
#  Tout le code dans un seul fichier pour éviter les erreurs d'import.
#  Compatible Ursina 0.9+ / Python 3.10-3.11
# =============================================================================

from ursina import *
from config import *
import math, sys

# ─── INIT APPLICATION ────────────────────────────────────────────────────────
app = Ursina(title='Street Facteur', borderless=False, vsync=True,
             development_mode=False)
window.size            = (1280, 720)
window.fps_counter.enabled = True
window.color           = color.rgb(20, 20, 50)   # fond bleu nuit

# Caméra orthographique (DOIT être après Ursina())
camera.orthographic    = True
camera.fov             = CAM_BASE_FOV
camera.position        = Vec3(12, 3, -20)
camera.rotation        = Vec3(0, 0, 0)

# ─── ÉTAT GLOBAL DU JEU ──────────────────────────────────────────────────────
gs = {
    'timer'      : float(LEVEL_TIME),
    'mails_done' : 0,
    'game_over'  : False,
    'victory'    : False,
}

players_list    = []
enemies_list    = []
mailboxes_list  = []
projectiles_list = []

# ─── DÉCOR DE LA RUE ─────────────────────────────────────────────────────────
# Ciel (quad très en arrière sur Z)
Entity(model='quad', scale=(150, 50), position=(25, 8, 80),
       color=color.rgb(100, 149, 237))
# Immeubles
Entity(model='quad', scale=(150, 20), position=(25, 0, 60),
       color=color.rgb(55, 55, 90))
Entity(model='quad', scale=(150, 10), position=(25, -2, 50),
       color=color.rgb(70, 50, 50))
# Sol
Entity(model='cube', scale=(65, 0.5, 4), position=(25, -0.25, 0),
       color=color.rgb(45, 45, 45))
# Lignes de trottoir
for i in range(8):
    Entity(model='cube', scale=(0.12, 0.06, 4),
           position=(4 + i * 6.5, 0.03, 0), color=color.rgb(85, 85, 85))
# Lampadaires décoratifs
for lx in [6, 16, 26, 36, 44]:
    Entity(model='cube', scale=(0.15, 3.0, 0.15),
           position=(lx, 1.5, -0.5), color=color.rgb(80, 80, 80))
    Entity(model='cube', scale=(0.5, 0.15, 0.15),
           position=(lx + 0.2, 3.1, -0.5), color=color.rgb(80, 80, 80))
    Entity(model='cube', scale=(0.25, 0.25, 0.25),
           position=(lx + 0.3, 3.0, -0.5), color=color.rgb(255, 255, 200))

# ─── CLASSE JOUEUR ───────────────────────────────────────────────────────────
class Player(Entity):
    def __init__(self, pid, pos, body_col, hat_col):
        super().__init__(position=pos)
        self.pid       = pid
        self.body_col  = body_col

        # — Visuel —
        self.body = Entity(parent=self, model='cube',
                           scale=(0.7, 1.1, 0.5), color=body_col)
        self.hat  = Entity(parent=self, model='cube',
                           scale=(0.85, 0.22, 0.6), color=hat_col,
                           position=(0, 0.67, 0))
        self.bag  = Entity(parent=self, model='cube',
                           scale=(0.28, 0.28, 0.28),
                           color=color.rgb(180, 140, 50),
                           position=(0.45, -0.05, 0))

        # — Stats —
        self.hp        = PLAYER_HP
        self.max_hp    = PLAYER_HP
        self.facing    = 1

        # — Physique —
        self.vel_y     = 0.0
        self.vel_x     = 0.0
        self.on_ground = False

        # — Timers —
        self.atk_cd    = 0.0
        self.atk_timer = 0.0
        self.dash_cd   = 0.0
        self.dash_timer= 0.0
        self.ko_timer  = 0.0
        self.hit_flash = 0.0
        self.grab_hits = 0
        self.delivery_hold = {}   # {mailbox_id: float}

        # — États —
        self.is_attacking = False
        self.is_dashing   = False
        self.is_grabbed   = False
        self.is_ko        = False

        # — One-shot inputs —
        self._jump  = False
        self._atk   = False
        self._dash  = False

    # Raccourcis touches
    @property
    def lk(self): return P1_LEFT  if self.pid == 1 else P2_LEFT
    @property
    def rk(self): return P1_RIGHT if self.pid == 1 else P2_RIGHT
    @property
    def jk(self): return P1_JUMP  if self.pid == 1 else P2_JUMP
    @property
    def ak(self): return P1_ATTACK   if self.pid == 1 else P2_ATTACK
    @property
    def dk(self): return P1_DASH  if self.pid == 1 else P2_DASH

    def on_key(self, key):
        if key == self.jk: self._jump = True
        if key == self.ak: self._atk  = True
        if key == self.dk: self._dash = True

    def update(self):
        if gs['game_over']:
            return
        dt = time.dt

        # — KO —
        if self.is_ko:
            self.ko_timer -= dt
            self.body.rotation_z = lerp(self.body.rotation_z, 90, 10 * dt)
            if self.ko_timer <= 0:
                self.is_ko          = False
                self.hp             = self.max_hp
                self.body.rotation_z = 0
                self.body.color     = self.body_col
            return

        # — Grabbed par mamie —
        if self.is_grabbed:
            self._atk = False
            return

        # — Timers —
        self.atk_cd    = max(0.0, self.atk_cd    - dt)
        self.dash_cd   = max(0.0, self.dash_cd   - dt)
        if self.atk_timer > 0:
            self.atk_timer -= dt
            if self.atk_timer <= 0:
                self.is_attacking     = False
                self.body.rotation_z  = 0
        if self.dash_timer > 0:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.is_dashing   = False
                self.vel_x        = 0
                self.body.scale_x = 0.7

        # — Hit flash —
        if self.hit_flash > 0:
            self.hit_flash -= dt
            self.body.color = color.white
        else:
            self.body.color = self.body_col

        # — Physique verticale —
        if not self.on_ground:
            self.vel_y -= GRAVITY * dt
        self.y += self.vel_y * dt
        gy = GROUND_Y + 0.56
        if self.y <= gy:
            self.y         = gy
            self.vel_y     = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # — Knockback horizontal —
        if abs(self.vel_x) > 0.05:
            self.x    += self.vel_x * dt
            self.vel_x = lerp(self.vel_x, 0, 10 * dt)

        # — Déplacement clavier —
        if not self.is_dashing:
            if held_keys[self.lk]:
                self.x      -= MOVE_SPEED * dt
                self.facing  = -1
                self.bag.x   = -0.45
                if self.on_ground:
                    self.body.y = math.sin(time.time() * 10) * 0.04
            elif held_keys[self.rk]:
                self.x      += MOVE_SPEED * dt
                self.facing  = 1
                self.bag.x   = 0.45
                if self.on_ground:
                    self.body.y = math.sin(time.time() * 10) * 0.04
            else:
                self.body.y = lerp(self.body.y, 0, 10 * dt)

        # — Saut —
        if self._jump and self.on_ground:
            self.vel_y     = JUMP_FORCE
            self.on_ground = False
            self.body.scale_y = 1.4
            invoke(setattr, self.body, 'scale_y', 1.1, delay=0.15)
        self._jump = False

        # — Attaque —
        if self._atk and self.atk_cd <= 0 and not self.is_dashing:
            self.is_attacking  = True
            self.atk_timer     = ATTACK_DURATION
            self.atk_cd        = ATTACK_COOLDOWN
            self.body.rotation_z = self.facing * -30
            self._do_melee()
        self._atk = False

        # — Dash —
        if self._dash and self.dash_cd <= 0:
            self.is_dashing   = True
            self.dash_timer   = DASH_DURATION
            self.dash_cd      = DASH_COOLDOWN
            self.vel_x        = self.facing * DASH_SPEED
            self.body.scale_x = 1.5
        self._dash = False

        # — Regard automatique vers les ennemis proches —
        nearby = [e for e in enemies_list if not e.is_ko]
        if nearby:
            closest = min(nearby, key=lambda e: abs(e.x - self.x))
            self.facing = 1 if closest.x > self.x else -1

        # — Clamp scène —
        self.x = clamp(self.x, STAGE_LEFT + 0.5, STAGE_RIGHT - 0.5)

        # — Livraison automatique par proximité —
        self._check_delivery()

    def _do_melee(self):
        for e in enemies_list:
            if e.is_ko: continue
            dx = e.x - self.x
            if dx * self.facing > 0 and abs(dx) < ATTACK_RANGE:
                if abs(e.y - self.y) < 1.5:
                    e.take_damage(ATTACK_DAMAGE, self)

    def _check_delivery(self):
        for mb in mailboxes_list:
            if mb.delivered: continue
            mid = id(mb)
            dist = abs(mb.x - self.x) + abs(mb.y - self.y)
            if dist < DELIVERY_RANGE:
                self.delivery_hold[mid] = self.delivery_hold.get(mid, 0) + time.dt
                mb.set_progress(self.delivery_hold[mid] / DELIVERY_HOLD_TIME)
                if self.delivery_hold[mid] >= DELIVERY_HOLD_TIME:
                    mb.deliver()
            else:
                if mid in self.delivery_hold:
                    del self.delivery_hold[mid]
                    mb.set_progress(0)

    def take_damage(self, amount, attacker=None):
        if self.is_dashing or self.is_ko: return
        self.hp        = max(0, self.hp - amount)
        self.hit_flash = 0.12
        if attacker:
            d         = 1 if self.x > attacker.x else -1
            self.vel_x = d * KNOCKBACK_FORCE
        if self.hp <= 0:
            self.is_ko    = True
            self.ko_timer = KO_DURATION
            self.hp       = 0
            gs['timer']  -= KO_TIME_PENALTY

    def try_break_grab(self):
        self.grab_hits += 1
        if self.grab_hits >= GRANNY_BREAK_HITS:
            self.is_grabbed = False
            self.grab_hits  = 0


# ─── ENNEMI BASE ─────────────────────────────────────────────────────────────
class BaseEnemy(Entity):
    def __init__(self, pos, hp, col):
        super().__init__(position=pos)
        self.hp     = hp
        self.max_hp = hp
        self.facing = 1
        self.vel_x  = 0.0
        self.vel_y  = 0.0
        self.on_ground = False
        self.is_ko  = False
        self._flash = 0.0
        self._base_col = col
        self.body_entity = None   # sous-entité visuelle principale

    def _physics(self):
        dt = time.dt
        if not self.on_ground:
            self.vel_y -= GRAVITY * dt
        self.y += self.vel_y * dt
        gy = GROUND_Y + 0.31
        if self.y <= gy:
            self.y, self.vel_y, self.on_ground = gy, 0, True
        else:
            self.on_ground = False
        if abs(self.vel_x) > 0.05:
            self.x    += self.vel_x * dt
            self.vel_x = lerp(self.vel_x, 0, 10 * dt)
        self.x = clamp(self.x, STAGE_LEFT, STAGE_RIGHT)

    def take_damage(self, amount, attacker=None):
        if self.is_ko: return
        self.hp    = max(0, self.hp - amount)
        self._flash = 0.15
        if attacker:
            d = 1 if self.x > attacker.x else -1
            self.vel_x = d * 3.0
        if self.hp <= 0:
            self._enter_ko()

    def _enter_ko(self):
        self.is_ko = True
        self.rotation_z = 90
        invoke(destroy, self, delay=1.5)
        if self in enemies_list:
            invoke(enemies_list.remove, self, delay=0)

    def _flash_update(self):
        if self._flash > 0:
            self._flash -= time.dt
            if self.body_entity:
                self.body_entity.color = color.white
        else:
            if self.body_entity:
                self.body_entity.color = self._base_col


# ─── CHIEN ENRAGÉ ────────────────────────────────────────────────────────────
class Dog(BaseEnemy):
    def __init__(self, pos):
        super().__init__(pos, DOG_HP, color.rgb(180, 120, 40))
        self._base_col = color.rgb(180, 120, 40)
        # Corps
        self.body_entity = Entity(parent=self, model='cube',
                                   scale=(0.9, 0.5, 0.5),
                                   color=self._base_col)
        # Tête
        Entity(parent=self, model='cube', scale=(0.45, 0.45, 0.45),
               color=color.rgb(200, 140, 55), position=(0.55, 0.22, 0))
        # Oreilles
        Entity(parent=self, model='cube', scale=(0.15, 0.2, 0.15),
               color=color.rgb(160, 100, 30), position=(0.6, 0.55, 0.15))
        Entity(parent=self, model='cube', scale=(0.15, 0.2, 0.15),
               color=color.rgb(160, 100, 30), position=(0.6, 0.55, -0.15))
        # Queue
        self.tail = Entity(parent=self, model='cube', scale=(0.14, 0.35, 0.14),
                           color=color.rgb(180, 120, 40),
                           position=(-0.55, 0.28, 0), rotation_z=30)

        self._patrol_center = pos.x
        self._patrol_range  = 3.0
        self._atk_cd        = 0.0

    def update(self):
        if self.is_ko or gs['game_over']: return
        dt = time.dt
        self._atk_cd = max(0, self._atk_cd - dt)
        self._physics()
        self._flash_update()

        # Queue qui remue
        self.tail.rotation_z = 30 + math.sin(time.time() * 8) * 25

        # IA
        active = [p for p in players_list if not p.is_ko and not p.is_grabbed]
        if not active: return
        target = min(active, key=lambda p: abs(p.x - self.x))
        dist   = abs(target.x - self.x)

        if dist < DOG_DETECT_RANGE:
            self.facing = 1 if target.x > self.x else -1
            self.x += self.facing * DOG_SPEED * dt
            if dist < DOG_ATTACK_RANGE and self._atk_cd <= 0:
                target.take_damage(DOG_ATTACK_DAMAGE, self)
                self._atk_cd = DOG_ATTACK_COOLDOWN
        else:
            # Patrouille
            self.x += self.facing * (DOG_SPEED * 0.5) * dt
            if abs(self.x - self._patrol_center) > self._patrol_range:
                self.facing *= -1


# ─── MAMIE BAVARDE ───────────────────────────────────────────────────────────
class Granny(BaseEnemy):
    def __init__(self, pos):
        super().__init__(pos, 999, color.rgb(160, 100, 180))
        self._base_col = color.rgb(160, 100, 180)
        # Corps
        self.body_entity = Entity(parent=self, model='cube',
                                   scale=(0.6, 0.9, 0.5),
                                   color=self._base_col)
        # Tête
        Entity(parent=self, model='cube', scale=(0.4, 0.4, 0.4),
               color=color.rgb(230, 200, 200), position=(0, 0.65, 0))
        # Chignon
        Entity(parent=self, model='cube', scale=(0.35, 0.25, 0.35),
               color=color.rgb(215, 215, 215), position=(0, 0.92, 0))

        # Bulle de dialogue (cachée par défaut)
        self.bubble = Text("Ah mon petit...\ntu sais en 1965...",
                           parent=self, position=(0.8, 1.4),
                           scale=8, color=color.white,
                           background=True, enabled=False)

        self._grab_cd  = 0.0
        self._grabbed  = None
        self._grab_timer = 0.0

    def update(self):
        if self.is_ko or gs['game_over']: return
        dt = time.dt
        self._grab_cd = max(0, self._grab_cd - dt)

        # Tentative de grab
        if self._grab_cd <= 0 and self._grabbed is None:
            active = [p for p in players_list if not p.is_ko and not p.is_grabbed]
            for p in active:
                if abs(p.x - self.x) < GRANNY_GRAB_RANGE:
                    self._grabbed       = p
                    p.is_grabbed        = True
                    self._grab_timer    = GRANNY_GRAB_DURATION
                    self.bubble.enabled = True
                    break

        # Maintien du grab
        if self._grabbed:
            self._grab_timer -= dt
            # Coller le joueur
            self._grabbed.x = self.x + 1.0
            self._grabbed.y = GROUND_Y + 0.56
            if self._grab_timer <= 0 or not self._grabbed.is_grabbed:
                self._release()

    def _release(self):
        if self._grabbed:
            self._grabbed.is_grabbed = False
            self._grabbed.grab_hits  = 0
            self._grabbed            = None
        self.bubble.enabled = False
        self._grab_cd = GRANNY_GRAB_COOLDOWN

    def take_damage(self, amount, attacker=None):
        # Immortelle — mais si c'est le joueur grabé qui frappe, compte comme tentative de libération
        if self._grabbed and attacker == self._grabbed:
            self._grabbed.try_break_grab()


# ─── VOISIN GRINCHEUX ────────────────────────────────────────────────────────
class Neighbor(BaseEnemy):
    def __init__(self, pos):
        super().__init__(Vec3(pos.x, pos.y + 1.4, pos.z), NEIGHBOR_HP,
                         color.rgb(160, 70, 70))
        self._base_col = color.rgb(160, 70, 70)
        # Fenêtre
        Entity(parent=self, model='cube', scale=(1.3, 1.5, 0.15),
               color=color.rgb(80, 120, 170), position=(0, 0, 0.12))
        Entity(parent=self, model='cube', scale=(1.35, 1.55, 0.1),
               color=color.rgb(55, 55, 55), position=(0, 0, 0.17))
        # Corps
        self.body_entity = Entity(parent=self, model='cube',
                                   scale=(0.6, 0.8, 0.4),
                                   color=self._base_col)
        # Bras levé
        self.arm = Entity(parent=self, model='cube', scale=(0.2, 0.55, 0.2),
                          color=color.rgb(200, 150, 100),
                          position=(0.45, 0.2, 0), rotation_z=-40)

        self._throw_cd = NEIGHBOR_THROW_COOLDOWN * 0.5  # premier lancer rapide

    def update(self):
        if self.is_ko or gs['game_over']: return
        dt = time.dt
        self._throw_cd = max(0, self._throw_cd - dt)
        self._flash_update()

        active = [p for p in players_list if not p.is_ko]
        if not active: return
        target = min(active, key=lambda p: abs(p.x - self.x))
        self.facing = 1 if target.x > self.x else -1

        if self._throw_cd <= 0:
            # Animation bras
            self.arm.rotation_z = -40
            invoke(setattr, self.arm, 'rotation_z', 60, delay=0.2)
            # Projectile
            proj = Projectile(Vec3(self.x + self.facing * 0.6, self.y + 0.1, 0),
                              self.facing)
            projectiles_list.append(proj)
            self._throw_cd = NEIGHBOR_THROW_COOLDOWN


# ─── PROJECTILE ──────────────────────────────────────────────────────────────
class Projectile(Entity):
    def __init__(self, pos, direction):
        super().__init__(
            model='cube', scale=(0.38, 0.28, 0.1),
            color=color.rgb(220, 200, 150), position=pos
        )
        self.direction = direction
        self._travel   = 0.0
        self._rot      = 0.0

    def update(self):
        if gs['game_over']: return
        dt = time.dt
        dx = self.direction * NEIGHBOR_PROJECTILE_SPEED * dt
        self.x      += dx
        self._travel += abs(dx)
        self._rot    += 200 * dt
        self.rotation_z = self._rot

        if self._travel > 12:
            self._remove(); return

        for p in players_list:
            if p.is_dashing or p.is_ko: continue
            if abs(self.x - p.x) < 0.7 and abs(self.y - p.y) < 0.8:
                p.take_damage(NEIGHBOR_PROJECTILE_DAMAGE, self)
                self._remove(); return

    def _remove(self):
        if self in projectiles_list:
            projectiles_list.remove(self)
        destroy(self)


# ─── BOÎTE AUX LETTRES ───────────────────────────────────────────────────────
class Mailbox(Entity):
    def __init__(self, pos):
        super().__init__(position=pos)
        self.delivered = False

        # Corps
        self.body = Entity(parent=self, model='cube',
                           scale=(0.5, 0.8, 0.4),
                           color=color.rgb(30, 80, 200))
        # Toit
        Entity(parent=self, model='cube', scale=(0.58, 0.18, 0.48),
               color=color.rgb(20, 55, 160), position=(0, 0.49, 0))
        # Fente
        Entity(parent=self, model='cube', scale=(0.28, 0.05, 0.05),
               color=color.black, position=(0, 0.1, 0.21))
        # Icône
        self.icon = Text("📬", parent=self, position=(0, 1.0),
                          scale=5, billboard=True)
        # Barre de progression
        self.prog_bg = Entity(parent=self, model='quad',
                               scale=(0.6, 0.08), color=color.dark_gray,
                               position=(0, 0.85, -0.1))
        self.prog_bar = Entity(parent=self, model='quad',
                                scale=(0, 0.06), color=color.lime,
                                position=(-0.3, 0.85, -0.2),
                                origin=(-0.5, 0))

    def set_progress(self, ratio):
        self.prog_bar.scale_x = clamp(ratio, 0, 1) * 0.6

    def deliver(self):
        self.delivered      = True
        self.body.color     = color.rgb(50, 200, 80)
        self.prog_bg.enabled = False
        self.prog_bar.enabled = False
        self.icon.text      = "✅"
        self.body.scale     = (0.5, 0.8, 0.4)
        # Anim de livraison
        self.body.animate_scale((0.65, 1.1, 0.52), duration=0.15)
        invoke(self.body.animate_scale, (0.5, 0.8, 0.4), delay=0.15, duration=0.15)
        # Texte flottant +temps
        bonus_txt = Text(f"+{int(DELIVERY_TIME_BONUS)}s",
                         position=(self.x, self.y + 1.5, -1),
                         scale=2.5, color=color.lime, billboard=True)
        bonus_txt.animate_position(
            Vec3(self.x, self.y + 2.5, -1), duration=1.2
        )
        invoke(destroy, bonus_txt, delay=1.2)
        # Mettre à jour le score
        gs['mails_done'] += 1
        gs['timer']      += DELIVERY_TIME_BONUS
        if gs['mails_done'] >= TOTAL_MAILBOXES:
            gs['game_over'] = True
            gs['victory']   = True


# ─── HUD ─────────────────────────────────────────────────────────────────────
class HUD:
    def __init__(self):
        # Chrono
        self.timer_txt = Text(
            text=str(int(LEVEL_TIME)),
            parent=camera.ui,
            position=(0, 0.44),
            origin=(0, 0),
            scale=3.2,
            color=color.white
        )
        # Compteur lettres
        self.mail_txt = Text(
            text=f"📬 0/{TOTAL_MAILBOXES}",
            parent=camera.ui,
            position=(-0.84, 0.44),
            origin=(-0.5, 0),
            scale=1.6,
            color=color.white
        )
        # Barre de vie P1 (bas gauche)
        self.hp_bg1 = Entity(parent=camera.ui, model='quad',
                              scale=(0.32, 0.035),
                              position=(-0.62, -0.44), color=color.dark_gray)
        self.hp_bar1 = Entity(parent=camera.ui, model='quad',
                               scale=(0.32, 0.028),
                               position=(-0.78, -0.44),
                               origin=(-0.5, 0), color=color.red)
        Text("🚴 J1", parent=camera.ui,
             position=(-0.84, -0.41), scale=1.3,
             origin=(-0.5, 0), color=color.rgb(100, 180, 255))

        # Barre de vie P2 (bas droite)
        self.hp_bg2 = Entity(parent=camera.ui, model='quad',
                              scale=(0.32, 0.035),
                              position=(0.62, -0.44), color=color.dark_gray)
        self.hp_bar2 = Entity(parent=camera.ui, model='quad',
                               scale=(0.32, 0.028),
                               position=(0.46, -0.44),
                               origin=(-0.5, 0), color=color.red)
        Text("J2 🚴", parent=camera.ui,
             position=(0.84, -0.41), scale=1.3,
             origin=(0.5, 0), color=color.rgb(255, 150, 50))

        # Message de statut (victoire/défaite)
        self.status = Text(
            text="",
            parent=camera.ui,
            position=(0, 0.05),
            origin=(0, 0),
            scale=3.8,
            color=color.yellow,
            enabled=False
        )
        self._blink = 0.0

    def update(self, timer, mails, players):
        # Chrono
        secs = max(0, int(timer))
        self.timer_txt.text = str(secs)
        if timer < 10:
            self._blink += time.dt
            self.timer_txt.enabled = (int(self._blink * 3) % 2 == 0)
            self.timer_txt.color   = color.red
        elif timer < 20:
            self.timer_txt.color   = color.orange
            self.timer_txt.enabled = True
        else:
            self.timer_txt.color   = color.white
            self.timer_txt.enabled = True

        # Lettres
        self.mail_txt.text = f"📬 {mails}/{TOTAL_MAILBOXES}"

        # Barres de vie
        p1, p2 = players[0], players[1]
        ratio1 = p1.hp / p1.max_hp
        ratio2 = p2.hp / p2.max_hp
        self.hp_bar1.scale_x = ratio1 * 0.32
        self.hp_bar2.scale_x = ratio2 * 0.32
        self.hp_bar1.color = color.red if ratio1 > 0.25 else color.orange
        self.hp_bar2.color = color.red if ratio2 > 0.25 else color.orange

    def show_end(self, msg, col):
        self.status.text    = msg
        self.status.color   = col
        self.status.enabled = True


# ─── CAMÉRA DYNAMIQUE ────────────────────────────────────────────────────────
cam_target_x   = 12.0
cam_target_fov = float(CAM_BASE_FOV)

def update_camera(players):
    global cam_target_x, cam_target_fov
    active = [p for p in players if not p.is_ko]
    if not active:
        return
    if len(active) == 1:
        cam_target_x   = active[0].x
        cam_target_fov = CAM_BASE_FOV
    else:
        cam_target_x   = (active[0].x + active[1].x) / 2
        spread         = abs(active[0].x - active[1].x)
        cam_target_fov = clamp(CAM_BASE_FOV + spread * 0.35,
                               CAM_MIN_FOV, CAM_MAX_FOV)

    cam_target_x = clamp(cam_target_x,
                         STAGE_LEFT  + CAM_LEFT_CLAMP,
                         STAGE_RIGHT - CAM_RIGHT_CLAMP)
    camera.x   = lerp(camera.x,   cam_target_x,   CAM_LERP_SPEED * time.dt)
    camera.fov = lerp(camera.fov, cam_target_fov, CAM_LERP_SPEED * time.dt)

    # Légère parallaxe sur les décors 3D déjà en scène
    # (les quads de fond glissent légèrement avec la caméra — effet naturel)


# ─── CRÉATION DU NIVEAU ──────────────────────────────────────────────────────
def build_level():
    # Joueurs
    p1 = Player(1, Vec3(2, 1, 0),
                color.rgb(30, 100, 200), color.rgb(20, 60, 140))
    p2 = Player(2, Vec3(4, 1, 0),
                color.rgb(200, 100, 20), color.rgb(140, 70, 10))
    players_list.extend([p1, p2])

    # Ennemis
    for dx in [8, 17, 29]:
        enemies_list.append(Dog(Vec3(dx, 0.3, 0)))
    for dx in [12, 24, 37]:
        enemies_list.append(Granny(Vec3(dx, 0.3, 0)))
    for dx in [20, 34]:
        enemies_list.append(Neighbor(Vec3(dx, 0, 0)))

    # Boîtes aux lettres
    for dx in [10, 20, 32, 42]:
        mailboxes_list.append(Mailbox(Vec3(dx, 0.4, 0)))

build_level()

# ─── HUD ─────────────────────────────────────────────────────────────────────
hud = HUD()

# ─── BOUCLE DE JEU ───────────────────────────────────────────────────────────
def update():
    if gs['game_over']:
        return

    gs['timer'] -= time.dt
    if gs['timer'] <= 0:
        gs['timer']     = 0
        gs['game_over'] = True
        gs['victory']   = False

    update_camera(players_list)
    hud.update(gs['timer'], gs['mails_done'], players_list)

    # Vérification victoire/défaite → affichage
    if gs['game_over']:
        if gs['victory']:
            hud.show_end("📬 COURRIER LIVRÉ !\n[R] pour rejouer", color.lime)
        else:
            hud.show_end("⏰ EN RETARD !\nLe facteur a raté sa tournée.\n[R] pour rejouer",
                         color.red)


# ─── GESTION DES INPUTS ──────────────────────────────────────────────────────
def input(key):
    # One-shot inputs transmis aux joueurs
    for p in players_list:
        p.on_key(key)

    # Relancer le jeu
    if key == KEY_RESTART and gs['game_over']:
        _restart()

    if key == KEY_QUIT:
        application.quit()


def _restart():
    """Vide la scène et recrée le niveau proprement."""
    # Supprimer toutes les entités du jeu (sauf caméra/UI)
    for e in scene.entities[:]:
        if e not in (camera,):
            try: destroy(e)
            except: pass

    players_list.clear()
    enemies_list.clear()
    mailboxes_list.clear()
    projectiles_list.clear()

    gs['timer']     = float(LEVEL_TIME)
    gs['mails_done'] = 0
    gs['game_over'] = False
    gs['victory']   = False

    # Recréer le décor
    Entity(model='quad', scale=(150, 50), position=(25, 8, 80),
           color=color.rgb(100, 149, 237))
    Entity(model='quad', scale=(150, 20), position=(25, 0, 60),
           color=color.rgb(55, 55, 90))
    Entity(model='cube', scale=(65, 0.5, 4), position=(25, -0.25, 0),
           color=color.rgb(45, 45, 45))

    build_level()

    # Remettre le HUD à zéro
    hud.status.enabled  = False
    hud.timer_txt.text  = str(int(LEVEL_TIME))
    hud.mail_txt.text   = f"📬 0/{TOTAL_MAILBOXES}"
    hud.hp_bar1.scale_x = 0.32
    hud.hp_bar2.scale_x = 0.32


# ─── LANCEMENT ───────────────────────────────────────────────────────────────
app.run()