class GameController:
    def __init__(self, engine, view):
        self.engine = engine
        self.view = view
        self.turn = 0
        self.game_over = False  # NUOVO FLAG
        self.stats = {
            "wins_p1": 0, "wins_p2": 0,
            "moves_p1": 0, "moves_p2": 0
        }

    def process_turn(self, posx):
        if self.game_over: return False, None

        col = int(posx // self.view.sq_size)

        if 0 <= col < 7 and self.engine.is_valid_location(col):
            if self.turn == 0:
                self.stats["moves_p1"] += 1
            else:
                self.stats["moves_p2"] += 1

            self.engine.drop_piece(col, self.turn)
            win = self.engine.check_victory(self.turn)

            last_player = self.turn

            if win:
                if self.turn == 0:
                    self.stats["wins_p1"] += 1
                else:
                    self.stats["wins_p2"] += 1
                self.game_over = True  # Blocca il gioco
            else:
                self.turn = (self.turn + 1) % 2

            return win, last_player
        return False, None

    def reset_for_new_round(self):
        self.engine.reset()
        self.stats["moves_p1"] = 0
        self.stats["moves_p2"] = 0
        self.turn = 0
        self.game_over = False  # Reset flag