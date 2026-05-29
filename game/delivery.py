import math
from ursina import Entity, color, Text, Vec3, invoke, time, destroy
import config
from game.states import PlayerState

_BODY_SCALE   = Vec3(0.5, 0.8, 0.4)
_BODY_SCALE13 = Vec3(0.65, 1.04, 0.52)   # * 1.3 for deliver tween

class Mailbox(Entity):
    def __init__(self, position):
        super().__init__(
            model='cube',
            scale=_BODY_SCALE,
            color=color.rgb(30, 80, 180),
            position=position
        )
        self.delivered = False
        self.hold_timers = {}
        self.game_state = None

        # Roof
        Entity(
            parent=self,
            model='cube',
            scale=(0.55, 0.2, 0.45),
            color=color.rgb(20, 50, 140),
            position=(0, 0.5, 0)
        )
        # Mail slot
        Entity(
            parent=self,
            model='cube',
            scale=(0.3, 0.05, 0.05),
            color=color.black,
            position=(0, 0.15, 0.21)
        )

        # Label above mailbox
        self.emoji = Text(text="MB", parent=self, y=1.0, scale=3, billboard=True)

        # Progress bar
        self.progress_bar = Entity(
            parent=self,
            model='quad',
            scale=(0.0, 0.1, 0.1),
            position=(0, 0.8, 0),
            color=color.yellow
        )

    def update(self, players=None):
        if self.delivered:
            return

        if players is None:
            if self.game_state and hasattr(self.game_state, 'players'):
                players = self.game_state.players
            else:
                return

        if isinstance(players, list):
            players_dict = {i + 1: p for i, p in enumerate(players)}
        elif isinstance(players, dict):
            players_dict = players
        else:
            return

        any_delivering = False
        for pid, player in players_dict.items():
            dist = math.sqrt((self.x - player.x) ** 2 + (self.y - player.y) ** 2)
            if dist < config.DELIVERY_RANGE and player.state not in (PlayerState.KO, PlayerState.GRABBED):
                self.hold_timers[pid] = self.hold_timers.get(pid, 0.0) + time.dt
                progress = self.hold_timers[pid] / config.DELIVERY_HOLD_TIME
                self.progress_bar.scale_x = progress * 0.8
                any_delivering = True

                if self.hold_timers[pid] >= config.DELIVERY_HOLD_TIME:
                    self.deliver()
                    return
            else:
                self.hold_timers[pid] = 0.0

        if not any_delivering:
            self.progress_bar.scale_x = 0.0

    def deliver(self):
        self.delivered = True
        self.color = color.rgb(50, 180, 80)
        self.progress_bar.enabled = False

        # Pulse scale tween
        self.animate_scale(_BODY_SCALE13, duration=0.2)
        invoke(self.animate_scale, _BODY_SCALE, duration=0.2, delay=0.2)

        # Floating "+10s" text
        self._spawn_floating_text()

        if self.game_state:
            self.game_state.on_delivery()

    def _spawn_floating_text(self):
        txt = Text(
            text="+10s",
            position=self.position + Vec3(0, 1.5, -0.1),
            scale=200,
            color=color.lime,
            billboard=True
        )
        txt.animate_position(txt.position + Vec3(0, 1.0, 0), duration=1.5)
        invoke(destroy, txt, delay=1.5)
