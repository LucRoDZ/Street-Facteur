import config

class InputManager:
    def __init__(self, player_id):
        self.player_id = player_id
        if player_id == 1:
            self.key_left   = config.P1_LEFT
            self.key_right  = config.P1_RIGHT
            self.key_jump   = config.P1_JUMP
            self.key_attack = config.P1_ATTACK
            self.key_dash   = config.P1_DASH
        else:
            self.key_left   = config.P2_LEFT
            self.key_right  = config.P2_RIGHT
            self.key_jump   = config.P2_JUMP
            self.key_attack = config.P2_ATTACK
            self.key_dash   = config.P2_DASH

        # Previous-frame held state for edge detection
        self._prev = {'jump': False, 'attack': False, 'dash': False}

    def get_actions(self, held_keys):
        left  = bool(held_keys.get(self.key_left,   False))
        right = bool(held_keys.get(self.key_right,  False))

        # Rising-edge detection: true only on the first frame a key is held.
        # Works for all keys because held_keys is populated by the low-level
        # Panda3D event system, bypassing Ursina's single-char input filter.
        curr_jump   = bool(held_keys.get(self.key_jump,   False))
        curr_attack = bool(held_keys.get(self.key_attack, False))
        curr_dash   = bool(held_keys.get(self.key_dash,   False))

        jump   = curr_jump   and not self._prev['jump']
        attack = curr_attack and not self._prev['attack']
        dash   = curr_dash   and not self._prev['dash']

        self._prev['jump']   = curr_jump
        self._prev['attack'] = curr_attack
        self._prev['dash']   = curr_dash

        return {
            'left': left, 'right': right,
            'jump': jump, 'attack': attack, 'dash': dash
        }
