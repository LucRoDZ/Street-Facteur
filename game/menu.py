from ursina import *
from . import core
from .level import build_level


class Menu:
    def __init__(self):
        self._elements = []

        def _e(**kw):
            e = Entity(parent=camera.ui, **kw)
            self._elements.append(e)
            return e

        def _t(text, **kw):
            t = Text(text, parent=camera.ui, **kw)
            self._elements.append(t)
            return t

        def _btn(label, pos, col, hi_col, cb):
            w, h = 0.26, 0.08
            hw, hh = w / 2, h / 2

            e = Entity(parent=camera.ui, model='quad', color=col,
                       position=pos, scale=(w, h))

            def _over():
                ar = window.aspect_ratio
                return abs(mouse.x * ar - e.x) < hw and abs(mouse.y - e.y) < hh

            # No collider — avoids singular-matrix crash from orthographic UI camera
            e.update = lambda: setattr(e, 'color', hi_col if _over() else col)
            e.input  = lambda key: cb() if key == 'left mouse down' and _over() else None

            self._elements.append(e)
            # Label sits slightly in front of the quad
            _t(label, position=(pos[0], pos[1], -0.01),
               origin=(0, 0), scale=1.5, color=color.white)

        _e(model='quad', scale=(2, 2), color=color.rgba(15, 10, 5, 210))

        _t("STREET FACTEUR",
           position=(0, 0.30), origin=(0, 0), scale=3.2,
           color=color.rgb(255, 200, 70))

        _t("Livrez le courrier avant la fin du chrono !",
           position=(0, 0.13), origin=(0, 0), scale=1.05,
           color=color.rgb(210, 210, 210))

        _btn("JOUER",
             pos=(0, -0.03),
             col=color.rgb(45, 155, 65),
             hi_col=color.rgb(65, 200, 90),
             cb=self._start)

        _btn("QUITTER",
             pos=(0, -0.16),
             col=color.rgb(155, 45, 45),
             hi_col=color.rgb(200, 65, 65),
             cb=application.quit)

        _t("Q / D : déplacer  ·  Espace : sauter  ·  F : attaquer  ·  V : dash",
           position=(0, -0.36), origin=(0, 0), scale=0.78,
           color=color.rgb(155, 155, 155))

    def _start(self):
        for e in self._elements:
            e.enabled = False
        core.hud.show()
        build_level()
