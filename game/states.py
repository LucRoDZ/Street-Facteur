from enum import Enum, auto

class PlayerState(Enum):
    IDLE = auto()
    WALK = auto()
    JUMP = auto()
    ATTACK = auto()
    DASH = auto()
    GRABBED = auto()
    KO = auto()

class EnemyState(Enum):
    IDLE = auto()
    PATROL = auto()
    CHASE = auto()
    ATTACK = auto()
    KO = auto()
