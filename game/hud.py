from ursina import camera, Text, Entity, color
import config

class HUD:
    def __init__(self, nb_players):
        self.nb_players = nb_players

        # Chrono (centre haut)
        self.timer_text = Text(
            text=str(int(config.LEVEL_TIME)),
            parent=camera.ui,
            position=(0, 0.44),
            origin=(0, 0),
            scale=3,
            color=color.white
        )

        # Compteur de lettres (haut gauche)
        self.mail_text = Text(
            text=f"[{0}/{config.TOTAL_MAILBOXES}] lettres",
            parent=camera.ui,
            position=(-0.85, 0.44),
            scale=1.5,
            origin=(-0.5, 0),
            color=color.white
        )

        # Barre de vie P1 (bas gauche)
        self.hp_bar_p1_bg = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.3, 0.03),
            position=(-0.6, -0.44),
            color=color.dark_gray,
            origin=(-0.5, 0)
        )
        self.hp_bar_p1 = Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.3, 0.03),
            position=(-0.6, -0.44),
            color=color.green,
            origin=(-0.5, 0)
        )
        self.label_p1 = Text(
            text="Facteur 1",
            parent=camera.ui,
            position=(-0.85, -0.42),
            scale=1.2,
            origin=(-0.5, 0),
            color=color.white
        )

        if nb_players == 2:
            self.hp_bar_p2_bg = Entity(
                parent=camera.ui,
                model='quad',
                scale=(0.3, 0.03),
                position=(0.6, -0.44),
                color=color.dark_gray,
                origin=(0.5, 0)
            )
            self.hp_bar_p2 = Entity(
                parent=camera.ui,
                model='quad',
                scale=(0.3, 0.03),
                position=(0.6, -0.44),
                color=color.green,
                origin=(0.5, 0)
            )
            self.label_p2 = Text(
                text="Facteur 2",
                parent=camera.ui,
                position=(0.85, -0.42),
                scale=1.2,
                origin=(0.5, 0),
                color=color.white
            )

        # Texte d'état (KO, victoire, défaite)
        self.status_text = Text(
            text="",
            parent=camera.ui,
            position=(0, 0.1),
            scale=4,
            origin=(0, 0),
            color=color.yellow,
            enabled=False
        )

    def _hp_color(self, pct):
        if pct <= 0.25:
            return color.rgb(255, 50, 50)
        elif pct <= 0.50:
            return color.orange
        return color.green

    def update(self, remaining_time, mails_done, players):
        # Chrono
        secs = max(0, int(remaining_time))
        self.timer_text.text = str(secs)

        if remaining_time < 10:
            self.timer_text.color = color.orange
            self.timer_text.enabled = (int(remaining_time * 2) % 2 == 0)
        elif remaining_time < 15:
            self.timer_text.color = color.orange
            self.timer_text.enabled = True
        else:
            self.timer_text.color = color.white
            self.timer_text.enabled = True

        # Lettres
        self.mail_text.text = f"[{mails_done}/{config.TOTAL_MAILBOXES}] lettres"

        # Barres de vie
        for joueur in players:
            pct = max(0.0, min(1.0, joueur.hp / joueur.max_hp))
            if joueur.player_id == 1:
                self.hp_bar_p1.scale_x = pct * 0.3
                self.hp_bar_p1.color = self._hp_color(pct)
            elif joueur.player_id == 2 and self.nb_players == 2:
                self.hp_bar_p2.scale_x = pct * 0.3
                self.hp_bar_p2.color = self._hp_color(pct)

    def show_status(self, message, color_=color.yellow):
        self.status_text.text = message
        self.status_text.color = color_
        self.status_text.enabled = True

    def hide_status(self):
        self.status_text.enabled = False
