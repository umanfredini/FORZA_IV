import pygame
import math

import math

class GameController:
    def __init__(self, engine, view):
        self.engine = engine
        self.view = view
        self.turn = 0

    def process_turn(self, posx):
        # Assicurati che sq_size esista in view (es. 100 per una finestra da 700px)
        col = int(math.floor(posx / self.view.sq_size))

        if self.engine.is_valid_location(col):
            # Prima di giocare, salviamo lo stato binario per l'Adaptive Learning
            # Qui catturiamo l'interezza del "problema" che l'avversario deve risolvere
            state_before = self.engine.get_state()

            self.engine.drop_piece(col, self.turn)
            win = self.engine.check_victory(self.turn)

            last_turn = self.turn
            self.turn = (self.turn + 1) % 2

            return col, state_before, win, last_turn
        return None, None, False, None