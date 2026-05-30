from ursina import *
from ..config import GAME_SHADER, TIME_BONUS, TOTAL_MAILBOXES
from .. import core
from ..fx import burst


class Mailbox(Entity):
    def __init__(self, pos):
        super().__init__(position=pos)
        self.delivered = False
        Entity(parent=self, model='cube', scale=(0.12, 1.0, 0.12),
               position=(0, 0.0, 0), color=color.rgb(60, 60, 70), shader=GAME_SHADER)
        self.box = Entity(parent=self, model='cube', scale=(0.55, 0.7, 0.45),
                          position=(0, 0.7, 0), color=color.rgb(235, 195, 50), shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(0.6, 0.12, 0.5),
               position=(0, 1.0, 0), color=color.rgb(210, 170, 40), shader=GAME_SHADER)
        Entity(parent=self, model='cube', scale=(0.3, 0.04, 0.05),
               position=(0, 0.78, 0.24), color=color.black)
        self.prog_bg = Entity(parent=self, model='quad', scale=(0.7, 0.1),
                              position=(0, 1.5, 0), color=color.rgb(30, 30, 35),
                              double_sided=True)
        self.prog = Entity(parent=self.prog_bg, model='quad', scale=(0.0001, 0.7),
                           position=(-0.48, 0, -0.01), color=color.lime, double_sided=True)
        self.prog_bg.enabled = False

    def set_progress(self, ratio):
        ratio = clamp(ratio, 0, 1)
        self.prog_bg.enabled = 0 < ratio < 1
        w = 0.96 * ratio or 0.0001
        self.prog.scale_x = w
        self.prog.x = -0.48 + w / 2

    def deliver(self):
        if self.delivered:
            return
        self.delivered = True
        self.prog_bg.enabled = False
        self.box.color = color.rgb(60, 220, 90)
        self.box.animate_scale((0.7, 0.9, 0.6), duration=0.12)
        invoke(self.box.animate_scale, (0.55, 0.7, 0.45), delay=0.12, duration=0.12)
        burst(self.world_position + Vec3(0, 1.0, 0), color.rgb(255, 230, 90),
              count=26, spread=2.6, life=0.6)
        burst(self.world_position + Vec3(0, 1.0, 0), color.lime,
              count=20, spread=2.2, life=0.6)
        t = Text(f"+{int(TIME_BONUS)}s",
                 position=self.world_position + Vec3(0, 1.8, -0.5),
                 scale=3, color=color.lime)
        t.animate_position(self.world_position + Vec3(0, 2.8, -0.5), duration=1.0)
        destroy(t, delay=1.0)

        core.gs['mails'] += 1
        core.gs['timer'] += TIME_BONUS
        if core.gs['mails'] >= TOTAL_MAILBOXES:
            core.end_game(victory=True)
