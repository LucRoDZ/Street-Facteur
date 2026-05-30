from ursina import *
from .config import LEVEL_TIME, GROUND_Y
from . import core
from .fx import update_camera, reset_camera
from .world import build_world
from .entities.player import Player
from .entities.dog import Dog
from .entities.granny import Granny
from .entities.neighbor import Neighbor
from .entities.mailbox import Mailbox


def build_level():
    core.player = Player()

    for x in (10, 26, 44):
        core.enemies.append(Dog(Vec3(x, GROUND_Y + 0.4, 0)))
    for x in (16, 38):
        core.enemies.append(Granny(Vec3(x, GROUND_Y + 0.65, 0)))
    for x in (22, 50):
        core.enemies.append(Neighbor(Vec3(x, 0, 8)))

    for x in (8, 20, 32, 46, 56):
        core.mailboxes.append(Mailbox(Vec3(x, GROUND_Y, -1.2)))


def update():
    if core.gs['over'] or core.player is None:
        return
    core.gs['timer'] -= time.dt
    if core.gs['timer'] <= 0:
        core.gs['timer'] = 0
        core.end_game(victory=False)
        return
    update_camera()
    core.hud.update()


def input(key):
    if key == 'escape':
        application.quit()
        return
    if core.gs['over']:
        if key in ('r', 'R'):
            restart()
        return
    if core.player is None:
        return
    if key == 'space':
        core.player.want_jump = True
    elif key == 'f':
        if core.player.stunned:
            core.player.mash()
        else:
            core.player.want_attack = True
    elif key in ('v', 'left shift', 'right shift'):
        core.player.want_dash = True


def restart():
    for e in scene.entities[:]:
        if e is core.sun:
            continue
        destroy(e)
    core.enemies.clear()
    core.mailboxes.clear()
    core.projectiles.clear()
    core.player = None

    core.gs.update({'timer': float(LEVEL_TIME), 'mails': 0, 'over': False, 'win': False})
    reset_camera()

    build_world()
    build_level()
    core.hud.reset()
