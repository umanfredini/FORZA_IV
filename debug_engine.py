import random
import time


class BitboardEngine:
    """
    Motore ottimizzato per Forza 4 utilizzando Bitboards.
    Struttura: 7 colonne x 7 righe (6 effettive + 1 bit di guardia).
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Resetta completamente lo stato della scacchiera."""
        self.position = 0  # Bitboard del giocatore di turno
        self.mask = 0  # Tutte le pedine sulla scacchiera
        self.counter = 0  # Contatore mosse REALI della partita

    def can_play(self, col):
        """Verifica se la colonna non è piena (controlla il bit di riga 5)."""
        return (self.mask & (1 << (5 + col * 7))) == 0

    def play(self, col):
        """Esegue una mossa aggiornando la bitboard."""
        # Trova la prima cella libera nella colonna e crea la maschera della mossa
        move = (self.mask + (1 << (col * 7))) & (0b1111111 << (col * 7))
        self.position ^= self.mask
        self.mask |= move
        self.counter += 1

    def is_win(self, pos):
        """Rilevamento vittoria tramite bitwise shifts."""
        # Orizzontale
        m = pos & (pos >> 7)
        if m & (m >> 14): return True
        # Diagonale \
        m = pos & (pos >> 6)
        if m & (m >> 12): return True
        # Diagonale /
        m = pos & (pos >> 8)
        if m & (m >> 16): return True
        # Verticale
        m = pos & (pos >> 1)
        if m & (m >> 2): return True
        return False

    def get_current_player_idx(self):
        return self.counter % 2

    def get_board_state(self):
        """Restituisce le bitboard di entrambi i giocatori (P1, P2)."""
        p2 = self.position
        p1 = self.position ^ self.mask
        if self.counter % 2 == 0:
            return p1, p2
        return p2, p1


class ImprovedMinimaxBot:
    """
    Bot Minimax con gestione separata del contatore di ricerca.
    """

    def __init__(self, depth=2, error_rate=0.0):
        self.depth = depth
        self.error_rate = error_rate
        self.nodes_explored = 0  # Contatore separato per il log della ricerca

    def evaluate(self, engine):
        p1, p2 = engine.get_board_state()
        curr_idx = engine.get_current_player_idx()

        last_pos = engine.position ^ engine.mask
        if engine.is_win(last_pos):
            return -1000000

        center_mask = 0b1111111 << (3 * 7)
        score = bin(p1 & center_mask).count('1') * 10
        score -= bin(p2 & center_mask).count('1') * 10

        return score if curr_idx == 0 else -score

    def solve(self, engine, depth):
        self.nodes_explored += 1
        if depth == 0:
            return self.evaluate(engine)

        last_pos = engine.position ^ engine.mask
        if engine.is_win(last_pos):
            return -1000000

        valid_moves = [c for c in range(7) if engine.can_play(c)]
        if not valid_moves: return 0

        best_score = -2000000
        for col in valid_moves:
            prev_pos, prev_mask = engine.position, engine.mask
            # Salviamo il counter per evitare drift durante la ricorsione
            prev_counter = engine.counter

            engine.play(col)
            score = -self.solve(engine, depth - 1)

            # Backtrack manuale e sicuro
            engine.position, engine.mask = prev_pos, prev_mask
            engine.counter = prev_counter

            best_score = max(best_score, score)
        return best_score

    def get_move(self, engine):
        self.nodes_explored = 0  # Resetta il log di ricerca per questa mossa
        valid_moves = [c for c in range(7) if engine.can_play(c)]

        if random.random() < self.error_rate:
            return random.choice(valid_moves)

        best_move = valid_moves[0]
        max_score = -2000000
        random.shuffle(valid_moves)

        for col in valid_moves:
            prev_pos, prev_mask = engine.position, engine.mask
            prev_counter = engine.counter

            engine.play(col)
            score = -self.solve(engine, self.depth - 1)

            engine.position, engine.mask = prev_pos, prev_mask
            engine.counter = prev_counter

            if score > max_score:
                max_score = score
                best_move = col

        # Debug opzionale: print(f"Nodi esplorati: {self.nodes_explored}")
        return best_move


def run_simulation(games=100, d1=4, e1=0.0, d2=2, e2=0.2):
    engine = BitboardEngine()
    bot1 = ImprovedMinimaxBot(depth=d1, error_rate=e1)
    bot2 = ImprovedMinimaxBot(depth=d2, error_rate=e2)

    stats = {"P1_Wins": 0, "P2_Wins": 0, "Draws": 0}

    print(f"Simulazione: Bot1(D{d1}) vs Bot2(D{d2}, Error:{e2})")

    for i in range(games):
        engine.reset()  # Reset pulito del motore
        while engine.counter < 42:
            bot = bot1 if engine.counter % 2 == 0 else bot2
            move = bot.get_move(engine)
            engine.play(move)

            last_pos = engine.position ^ engine.mask
            if engine.is_win(last_pos):
                if engine.counter % 2 != 0:
                    stats["P1_Wins"] += 1
                else:
                    stats["P2_Wins"] += 1
                break
        else:
            stats["Draws"] += 1

        if (i + 1) % 20 == 0:
            print(f"Partite completate: {i + 1}/{games}...")

    print("\n--- RISULTATI FINALI ---")
    print(f"Vittorie P1: {stats['P1_Wins']}")
    print(f"Vittorie P2: {stats['P2_Wins']}")
    print(f"Pareggi: {stats['Draws']} (Max mosse raggiunte: 42)")


if __name__ == "__main__":
    run_simulation(games=100)