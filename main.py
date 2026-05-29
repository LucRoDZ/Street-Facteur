import sys
from ursina import *
from config import *
from game.player import Player
from game.level import Level
from game.camera_rig import CameraRig
from game.hud import HUD

class GameState:
    def __init__(self):
        self.timer = LEVEL_TIME
        self.mails_done = 0
        self.game_over = False
        self.victory = False
        self.level = None

    def on_delivery(self):
        self.mails_done += 1
        self.timer += DELIVERY_TIME_BONUS
        if self.mails_done >= TOTAL_MAILBOXES:
            self.trigger_victory()

    def on_ko(self):
        self.timer -= KO_TIME_PENALTY

    def trigger_victory(self):
        self.victory = True
        self.game_over = True

    def trigger_defeat(self):
        self.victory = False
        self.game_over = True

# Create Ursina app
app = Ursina(title='Street Facteur', borderless=False)
window.size = (1280, 720)
window.fps_counter.enabled = True

# Set sky blue background — setBackgroundColor is the correct Panda3D call
app.setBackgroundColor(100/255, 149/255, 237/255)

game_state = GameState()

# Players
p1 = Player(player_id=1, position=Vec3(0, 1, 0), color_val=color.rgb(30, 100, 200))
p2 = Player(player_id=2, position=Vec3(1.5, 1, 0), color_val=color.rgb(200, 100, 20))
players = {1: p1, 2: p2}

p1.game_state = game_state
p2.game_state = game_state

# Level
level = Level(game_state)
game_state.level = level

# Share player list with enemies
for enemy in level.enemies:
    enemy.players = list(players.values())
for proj_spawner in level.neighbors:
    proj_spawner.players = list(players.values())

cam_rig = CameraRig()
hud = HUD(nb_players=2)

def update():
    if game_state.game_over:
        return

    game_state.timer -= time.dt
    if game_state.timer <= 0:
        game_state.trigger_defeat()

    level.update(list(players.values()))
    cam_rig.update(list(players.values()))
    hud.update(game_state.timer, game_state.mails_done, list(players.values()))

    if game_state.game_over and game_state.victory:
        hud.show_status("COURRIER LIVRE !\nAppuie sur R pour rejouer", color.lime)
    if game_state.game_over and not game_state.victory:
        hud.show_status("EN RETARD !\nAppuie sur R pour rejouer", color.red)

def input(key):
    if key == KEY_RESTART and game_state.game_over:
        scene.clear()
        exec(open('main.py').read(), globals())

    if key == KEY_QUIT:
        application.quit()

if not hasattr(sys, '_street_facteur_started'):
    sys._street_facteur_started = True
    app.run()
