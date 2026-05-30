import random
from ursina import *
from . import core
from .config import (SHADOWS_ON, GAME_SHADER, CAM_HEIGHT, CAM_DIST,
                     CAM_MARGIN, CAM_SMOOTH, STAGE_LEFT, STAGE_RIGHT)

_cam   = {'x': 0.0}
_shake = {'t': 0.0, 'dur': 0.0, 'mag': 0.0}


def shake_camera(intensity=0.3, duration=0.25):
    if intensity >= _shake['mag'] or _shake['t'] <= 0:
        _shake['mag'] = intensity
        _shake['dur'] = duration
        _shake['t']   = duration


def update_camera():
    target = clamp(core.player.x, STAGE_LEFT + CAM_MARGIN, STAGE_RIGHT - CAM_MARGIN)
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
    if SHADOWS_ON:
        core.sun.position = Vec3(core.player.x, 14, -6)


def reset_camera():
    _cam['x'] = 0.0


def burst(pos, base_color, count=14, spread=2.0, life=0.5, scale=0.18, up=0.6):
    for _ in range(count):
        p = Entity(model='cube', color=base_color,
                   scale=random.uniform(scale * 0.5, scale),
                   position=pos, shader=GAME_SHADER)
        d = Vec3(random.uniform(-1, 1),
                 random.uniform(up, up + 1.2),
                 random.uniform(-0.6, 0.6)).normalized() * spread * random.uniform(0.5, 1.2)
        p.animate_position(Vec3(pos) + d, duration=life, curve=curve.out_expo)
        p.animate_scale(0.001, duration=life, curve=curve.in_quad)
        destroy(p, delay=life + 0.02)
