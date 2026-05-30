from ursina import *
from .config import LEVEL_TIME, CAM_HEIGHT, CAM_DIST, CAM_TILT, CAM_FOV

app = Ursina(title='Street Facteur', borderless=False, vsync=True, development_mode=False)
window.color               = color.rgb(247, 188, 120)
window.fps_counter.enabled = True
window.exit_button.visible = False

sun = DirectionalLight()
sun.color = color.rgb(255, 246, 220)
try:
    sun.look_at(Vec3(1.5, -2.0, 1.0))
except Exception:
    sun.rotation = Vec3(45, -30, 0)
AmbientLight(color=color.rgba(150, 160, 190, 255))

camera.fov        = CAM_FOV
camera.rotation_x = CAM_TILT
camera.position   = Vec3(0, CAM_HEIGHT, CAM_DIST)

gs          = {'timer': float(LEVEL_TIME), 'mails': 0, 'over': False, 'win': False}
enemies     = []
mailboxes   = []
projectiles = []
player      = None
hud         = None


def end_game(victory):
    if gs['over']:
        return
    gs['over'] = True
    gs['win']  = victory
    if hud is None:
        return
    if victory:
        hud.show_end(
            "LE COURRIER EST ARRIVÉ À L'HEURE !\n\nFélicitations, Facteur.\n\n[ R ] pour recommencer",
            color.rgb(120, 255, 140))
    else:
        hud.show_end(
            "TOURNÉE RATÉE !\n\nLe quartier a eu raison de vous.\n\n[ R ] pour recommencer",
            color.rgb(255, 110, 110))
