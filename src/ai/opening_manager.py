"""
ai/opening_manager.py
Gestisce l'apprendimento delle aperture utilizzando UCB1 per bilanciare
sfruttamento (mosse forti) ed esplorazione (mosse poco testate).
"""
import random
import math

class OpeningManager:
    # --- CONFIGURAZIONE RICOMPENSE ---
    REWARD_WIN = 100
    REWARD_LOSS = -100
    # Penalità per il pareggio: scoraggiamo le linee morte, ma meno della sconfitta
    REWARD_DRAW = -20

    # Costante di esplorazione per UCB1 (più alta = più curiosità)
    EXPLORATION_C = 1.41

    def __init__(self, persistence):
        self.persistence = persistence
        self.game_history = []
        # Aumentiamo la profondità: ora impariamo fino a metà partita
        self.MAX_BOOK_DEPTH = 10

    def record_move(self, engine, move, player_who_moved):
        """ Registra la mossa corrente per il backpropagation a fine partita """
        if engine.counter > self.MAX_BOOK_DEPTH: return

        p1 = engine.bitboards[0]
        p2 = engine.bitboards[1]
        state_hash = f"{p1}_{p2}"

        self.game_history.append({
            "state": state_hash,
            "move": move,
            "player": player_who_moved
        })

    def finalize_game(self, winner_player_idx):
        """ Assegna i premi/punizioni a tutte le mosse registrate """
        if not self.game_history: return

        # print(f"[BOOK] Apprendimento su {len(self.game_history)} mosse...")

        for record in self.game_history:
            state = record["state"]
            move = record["move"]
            mover = record["player"]

            score = 0
            if winner_player_idx == "draw":
                score = self.REWARD_DRAW
            elif mover == winner_player_idx:
                score = self.REWARD_WIN
            else:
                score = self.REWARD_LOSS

            # Scriviamo nel DB (Update incrementale)
            self.persistence.update_opening_move(state, move, score)

        self.game_history.clear()

    def get_best_move(self, engine):
        """
        Sceglie la mossa migliore usando l'algoritmo UCB1.
        Restituisce: (move, True) se trovata, (None, False) se non ci sono dati.
        """
        p1, p2 = engine.bitboards[0], engine.bitboards[1]
        state_hash = f"{p1}_{p2}"

        # Recuperiamo stats: [(move, visits, total_score), ...]
        stats = self.persistence.get_opening_stats(state_hash)

        # Se non abbiamo mai visto questo stato, lasciamo fare al Minimax
        if not stats: return None, False

        # Calcoliamo le visite totali a questo stato (N)
        total_state_visits = sum(s[1] for s in stats)

        # Se abbiamo poche visite totali (< 5), è troppo presto per fidarsi del libro.
        # Lasciamo che il Minimax esplori un po'.
        if total_state_visits < 5: return None, False

        best_move = None
        best_ucb_score = float('-inf')

        # Logaritmo naturale delle visite totali (parte dell'esplorazione)
        log_total = math.log(total_state_visits)

        for move, visits, total_score in stats:
            # Calcolo della media (Exploitation)
            avg_score = total_score / visits

            # NORMALIZZAZIONE: UCB lavora bene tra 0 e 1.
            # Convertiamo il nostro range [-100, 100] in [0, 1]
            # -100 diventa 0.0, +100 diventa 1.0, -20 (Draw) diventa ~0.4
            normalized_score = (avg_score - self.REWARD_LOSS) / (self.REWARD_WIN - self.REWARD_LOSS)

            # Calcolo dell'esplorazione (Exploration)
            # Se visits è basso, questo termine diventa grande
            exploration = self.EXPLORATION_C * math.sqrt(log_total / visits)

            # Punteggio Finale UCB
            ucb_score = normalized_score + exploration

            if ucb_score > best_ucb_score:
                best_ucb_score = ucb_score
                best_move = move

        # Nota: Con UCB non serve Epsilon-Greedy (random 10%),
        # perché l'esplorazione è già matematica nella formula.

        # Controllo di sicurezza: se la mossa migliore ha comunque un punteggio medio
        # terribile (sotto il pareggio), non giocarla, lascia calcolare al Minimax.
        # -30 è appena sotto il Reward del pareggio (-20).
        stat_entry = next((s for s in stats if s[0] == best_move), None)
        if stat_entry:
            avg = stat_entry[2] / stat_entry[1]
            if avg < -30:
               # print(f"[BOOK] Mossa UCB scartata (Punteggio troppo basso: {avg})")
               return None, False

        # print(f"[BOOK] Mossa UCB scelta: {best_move+1} (Score: {best_ucb_score:.2f})")
        return best_move, True