# =============================================================================
#  STREET FACTEUR — config.py
#  Toutes les constantes de gameplay, regroupées et nommées de façon canonique.
# =============================================================================

# ── Physique & Monde ─────────────────────────────────────
GRAVITY      = 22.0
JUMP_FORCE   = 9.5
MOVE_SPEED   = 6.5
GROUND_Y     = 0.0
STAGE_LEFT   = -5.0
STAGE_RIGHT  = 60.0

# ── Joueur ───────────────────────────────────────────────
PLAYER_HP        = 100
ATTACK_DAMAGE    = 34
ATTACK_RANGE     = 2.0
ATTACK_COOLDOWN  = 0.4
DASH_SPEED       = 20.0
DASH_DURATION    = 0.18
DASH_COOLDOWN    = 0.8
KO_DURATION      = 2.5

# ── Ennemis ──────────────────────────────────────────────
DOG_HP            = 35
DOG_SPEED         = 4.5
DOG_ATTACK_DAMAGE = 15
DOG_DETECT_RANGE  = 8.0

GRANNY_RANGE         = 2.2
GRANNY_STUN_DURATION = 2.5
GRANNY_MASH_REQUIRED = 4

NEIGHBOR_HP       = 50
NEIGHBOR_COOLDOWN = 2.5
PROJECTILE_SPEED  = 9.0

# ── Objectifs & Score ────────────────────────────────────
TOTAL_MAILBOXES    = 5
DELIVERY_HOLD_TIME = 1.2
TIME_BONUS         = 15.0
LEVEL_TIME         = 90.0
