"""
ai/opening_manager.py
Gestisce l'apprendimento delle aperture con Reward Shaping anti-pareggio.
"""
import random

class OpeningManager:
    # --- CONFIGURAZIONE RICOMPENSE ---
    REWARD_WIN = 100
    REWARD_LOSS = -100
    # Penalità per il pareggio: scoraggia le linee morte
    REWARD_DRAW = -20

    def __init__(self, persistence):
        self.persistence = persistence
        self.game_history = []
        self.MAX_BOOK_DEPTH = 10

    def record_move(self, engine, move, player_who_moved):
        if engine.counter > self.MAX_BOOK_DEPTH: return

        p1 = engine.bitboards[0]
        p2 = engine.bitboards[1]
        state_hash = f"{p1}_{p2}"

        self.game_history.append({
            "state": state_hash, "move": move, "player": player_who_moved
        })

    def finalize_game(self, winner_player_idx):
        if not self.game_history: return

        print(f"[BOOK] Backpropagation su {len(self.game_history)} mosse...")

        for record in self.game_history:
            state = record["state"]
            move = record["move"]
            mover = record["player"]

            # Calcolo del Punteggio (Reward)
            score = 0

            if winner_player_idx == "draw":
                # ENTRAMBI ricevono la penalità per il pareggio
                score = self.REWARD_DRAW
            elif mover == winner_player_idx:
                score = self.REWARD_WIN
            else:
                score = self.REWARD_LOSS

            # Scriviamo nel DB
            self.persistence.update_opening_move(state, move, score)

        self.game_history.clear()

    def get_best_move(self, engine):
        p1, p2 = engine.bitboards[0], engine.bitboards[1]
        state_hash = f"{p1}_{p2}"

        stats = self.persistence.get_opening_stats(state_hash)
        if not stats: return None, False

        best_move = None
        best_avg_score = float('-inf')

        candidates = []

        # Analisi delle mosse salvate
        for move, visits, total_score in stats:
            # Ignoriamo mosse provate troppo poco (rumore statistico)
            if visits < 3: continue

            # Calcoliamo il punteggio medio
            avg_score = total_score / visits

            candidates.append((move, avg_score, visits))

            if avg_score > best_avg_score:
                best_avg_score = avg_score
                best_move = move

        # Logica di Selezione
        # Accettiamo la mossa solo se ha un punteggio "decente" (es. > -10)
        # Se il punteggio è molto negativo (es. -50), significa che porta spesso
        # a sconfitte o pareggi. Meglio lasciar provare il Minimax.
        if best_move is not None and best_avg_score > -10:
            # 10% di probabilità di esplorare altro (Epsilon-Greedy)
            if random.random() > 0.1:
                print(f"[BOOK] Mossa Book! Col: {best_move+1} (Score: {best_avg_score:.1f})")
                return best_move, True

        return None, False