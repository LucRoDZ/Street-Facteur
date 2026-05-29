from ursina import Vec3, camera
import config
from game.stage import Stage
from game.delivery import Mailbox
from game.enemies.dog import Dog
from game.enemies.granny import Granny
from game.enemies.neighbor import Neighbor

class Level:
    def __init__(self, game_state):
        self.game_state = game_state
        self.stage = Stage()

        # Spawn mailboxes
        self.mailboxes = []
        for x in (10, 20, 30, 40):
            mb = Mailbox(position=Vec3(x, 0.5, 0))
            mb.game_state = game_state
            self.mailboxes.append(mb)

        # Spawn enemies — Ursina auto-calls their update() each frame
        self.enemies = []
        self.neighbors = []

        spawn_y = config.GROUND_Y + 0.6

        for x in (8, 16, 28):
            self.enemies.append(Dog(position=Vec3(x, spawn_y, 0)))

        for x in (12, 24, 36):
            self.enemies.append(Granny(position=Vec3(x, spawn_y, 0)))

        for x in (19, 33):
            n = Neighbor(position=Vec3(x, 1.5, 0))
            self.enemies.append(n)
            self.neighbors.append(n)

    def update(self, players):
        # Update background parallax
        self.stage.update(camera.x)

        # Mailboxes need the players list explicitly
        for mailbox in self.mailboxes:
            mailbox.update(players)

        # Enemies are Entity subclasses — Ursina calls their update() automatically.
        # We only need to pass players here (stored as enemy.players in main.py).
