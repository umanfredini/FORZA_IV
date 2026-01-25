class GameController:
    def __init__(self, engine, view):
        self.engine = engine
        self.view = view
        self.turn = 0
        self.stats = {
            "wins_p1": 0, "wins_p2": 0,
            "moves_p1": 0, "moves_p2": 0
        }

    def process_turn(self, posx):
        # Calcoliamo la colonna considerando che la larghezza è divisa in 7
        col = int(posx // self.view.sq_size)

        if self.engine.is_valid_location(col):
            state_before = self.engine.bitboards[:]  # Copia stato attuale

            # Incremento contatore mosse
            if self.turn == 0:
                self.stats["moves_p1"] += 1
            else:
                self.stats["moves_p2"] += 1

            self.engine.drop_piece(col, self.turn)
            win = self.engine.check_victory(self.turn)

            if win:
                if self.turn == 0:
                    self.stats["wins_p1"] += 1
                else:
                    self.stats["wins_p2"] += 1

            last_turn = self.turn
            self.turn = (self.turn + 1) % 2

            return col, state_before, win, last_turn
        return None, None, False, None

    def reset_game(self):
        """ Resetta i contatori mosse ma tiene i record vittorie """
        self.stats["moves_p1"] = 0
        self.stats["moves_p2"] = 0
        self.engine.reset()  # Assicurati che l'engine abbia un metodo reset