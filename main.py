from game import core
from game.world import build_world
from game.level import update, input  # noqa: F401 — Ursina discovers via __main__
from game.hud import HUD
from game.menu import Menu

build_world()
core.hud = HUD()
Menu()

core.app.run()
