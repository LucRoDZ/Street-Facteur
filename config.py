# ── PHYSIQUE ──────────────────────────────────────────
GRAVITY         = 25.0    # accélération vers le bas (unités/s²)
JUMP_FORCE      = 10.0    # impulsion verticale au saut
MOVE_SPEED      = 6.0     # vitesse de déplacement horizontal
GROUND_Y        = 0.0     # hauteur du sol

# ── JOUEUR ────────────────────────────────────────────
PLAYER_HP           = 100
PLAYER_HEIGHT       = 1.0
ATTACK_DAMAGE       = 25
ATTACK_RANGE        = 1.8    # distance max pour toucher (unités)
ATTACK_DURATION     = 0.25   # secondes pendant lesquelles la hitbox est active
ATTACK_COOLDOWN     = 0.5
DASH_SPEED          = 18.0
DASH_DURATION       = 0.2
DASH_COOLDOWN       = 1.0
KNOCKBACK_FORCE     = 4.0
KO_DURATION         = 3.0    # secondes au sol après KO
KO_TIME_PENALTY     = 10.0   # secondes retirées au chrono quand KO

# ── ENNEMIS ───────────────────────────────────────────
DOG_HP              = 30
DOG_SPEED           = 4.0
DOG_ATTACK_RANGE    = 0.9
DOG_ATTACK_DAMAGE   = 20
DOG_ATTACK_COOLDOWN = 1.0
DOG_DETECT_RANGE    = 6.0
DOG_KNOCKBACK       = 3.0

GRANNY_GRAB_RANGE   = 2.0
GRANNY_GRAB_DURATION= 3.0    # secondes d'immobilisation
GRANNY_GRAB_COOLDOWN= 5.0
GRANNY_BREAK_HITS   = 3      # coups pour se libérer

NEIGHBOR_HP         = 40
NEIGHBOR_THROW_COOLDOWN = 3.0
NEIGHBOR_PROJECTILE_SPEED = 8.0
NEIGHBOR_PROJECTILE_DAMAGE = 15
NEIGHBOR_KNOCKBACK  = 2.0

# ── LIVRAISON ─────────────────────────────────────────
DELIVERY_RANGE      = 1.8    # distance pour déclencher la livraison
DELIVERY_HOLD_TIME  = 1.5    # secondes à rester près de la boîte
DELIVERY_TIME_BONUS = 10.0   # secondes gagnées par livraison réussie

# ── NIVEAU ────────────────────────────────────────────
LEVEL_TIME          = 90.0   # chrono de départ (secondes)
STAGE_LEFT          = -3.0
STAGE_RIGHT         = 48.0
TOTAL_MAILBOXES     = 4

# ── CAMÉRA ────────────────────────────────────────────
CAM_BASE_FOV        = 8.0
CAM_MIN_FOV         = 6.0
CAM_MAX_FOV         = 14.0
CAM_LERP_SPEED      = 5.0
CAM_LEFT_CLAMP      = 2.0    # marge gauche
CAM_RIGHT_CLAMP     = 2.0    # marge droite

# ── COMMANDES (clavier AZERTY) ────────────────────────
P1_LEFT     = 'q'
P1_RIGHT    = 'd'
P1_JUMP     = 'z'
P1_ATTACK   = 'f'
P1_DASH     = 'v'

P2_LEFT     = 'left arrow'
P2_RIGHT    = 'right arrow'
P2_JUMP     = 'up arrow'
P2_ATTACK   = 'k'
P2_DASH     = 'l'

KEY_RESTART = 'r'
KEY_QUIT    = 'escape'
