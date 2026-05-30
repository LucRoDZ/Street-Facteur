import random
from ursina import *
from .config import GAME_SHADER, STAGE_LEFT, STAGE_RIGHT, GROUND_Y

BRICK   = color.rgb(150, 70, 55)
BEIGE   = color.rgb(205, 185, 150)
GREY    = color.rgb(120, 120, 130)
PALETTE = [BRICK, BEIGE, GREY, color.rgb(95, 110, 130), color.rgb(170, 140, 110)]


def build_world():
    span   = STAGE_RIGHT - STAGE_LEFT
    center = (STAGE_LEFT + STAGE_RIGHT) / 2

    Entity(model='cube', texture='white_cube',
           texture_scale=(span / 2, 7),
           scale=(span + 10, 1.0, 14),
           position=(center, GROUND_Y - 0.5, 2),
           color=color.rgb(55, 55, 62), shader=GAME_SHADER)

    Entity(model='cube', scale=(span + 10, 0.2, 2.4),
           position=(center, GROUND_Y - 0.4, -3.0),
           color=color.rgb(140, 140, 145), shader=GAME_SHADER)

    for i in range(int(span // 3)):
        Entity(model='cube', scale=(1.1, 0.05, 0.22),
               position=(STAGE_LEFT + 1 + i * 3, GROUND_Y + 0.01, 4.5),
               color=color.rgb(225, 215, 160), shader=GAME_SHADER)

    bx = STAGE_LEFT - 2
    while bx < STAGE_RIGHT + 4:
        w   = random.uniform(3.5, 5.5)
        h   = random.uniform(7, 15)
        d   = random.uniform(3.5, 5.0)
        col = random.choice(PALETTE)
        Entity(model='cube', texture='brick', texture_scale=(w, h),
               scale=(w, h, d),
               position=(bx + w / 2, GROUND_Y + h / 2 - 0.5, 9 + d / 2),
               color=col, shader=GAME_SHADER)
        rows = int(h // 2)
        for r in range(1, rows):
            if random.random() < 0.55:
                Entity(model='cube', scale=(0.6, 0.7, 0.1),
                       position=(bx + w / 2 + random.uniform(-w / 3, w / 3),
                                 GROUND_Y - 0.5 + r * 2, 9 - 0.05),
                       color=color.rgb(255, 225, 140))
        bx += w + random.uniform(0.2, 0.8)

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
