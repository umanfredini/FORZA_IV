"""
ai/profiler.py
Modulo di Profilazione Comportamentale.
Analizza la discrepanza tra la "Mossa Ottimale" (Teoria dei Giochi)
e la "Mossa Effettuata" (Realtà) per calcolare i Bias cognitivi.
"""
from ai.analysis import get_threat_mask

class OpponentProfiler:
    def __init__(self):
        # HEATMAP DEI BIAS (1.0 = Standard)
        self.biases = {
            "missed_win": 1.0,           # Cecità alla propria vittoria
            "vertical_weakness": 1.0,    # Ignora minacce verticali
            "horizontal_weakness": 1.0,  # Ignora minacce orizzontali
            "diagonal_weakness": 1.0,    # Ignora minacce diagonali
            "threat_underestimation": 1.0 # Tendenza generale a ignorare le nostre minacce
        }

        self.stats = {
            "moves_analyzed": 0,
            "fatal_errors": 0,
        }

    def update(self, state_before, move_col, opponent_idx):
        """
        Esegue l'autopsia della mossa avversaria.
        Args:
            state_before: Lista [bitboard_p1, bitboard_p2] PRIMA della mossa.
            move_col: Indice colonna (0-6) dove ha giocato.
            opponent_idx: Indice del giocatore che ha mosso (0 o 1).
        """
        self.stats["moves_analyzed"] += 1

        # 1. RICOSTRUZIONE STATO PRECEDENTE
        # Nota: Il controller passa self.engine.bitboards.copy(), che è [p1_bb, p2_bb]
        p1_map = state_before[0]
        p2_map = state_before[1]
        full_mask = p1_map | p2_map

        # Identificazione Ruoli
        # Se opponent_idx ha mosso, 'opp_pieces' sono i suoi pezzi
        opp_pieces = state_before[opponent_idx]           # Chi ha mosso (Lui)
        my_pieces = state_before[(opponent_idx + 1) % 2]  # L'altro (Noi/IA)

        # 2. CALCOLO DEL BIT GIOCATO
        # Non avendo l'array 'heights', lo calcoliamo dalla full_mask.
        # Maschera della colonna intera
        col_mask = 0
        for r in range(6):
            col_mask |= (1 << (move_col * 7 + r))

        # Isariamo solo i pezzi in quella colonna
        col_pieces = full_mask & col_mask

        # Il bit giocato è il primo bit zero sopra i pezzi esistenti in quella colonna.
        # Trucco bitwise: (pieces + 1) trova il prossimo bit libero se partiamo da base colonna
        # Ma dobbiamo fare attenzione all'offset della colonna.
        # Metodo più sicuro e leggibile: iteriamo l'altezza.
        played_bit = 0
        for r in range(6):
            bit_pos = move_col * 7 + r
            if not (full_mask & (1 << bit_pos)):
                played_bit = (1 << bit_pos)
                break

        if played_bit == 0:
            # Colonna piena? Non dovrebbe succedere se la mossa è valida.
            return

        # --- FASE 1: KILLER INSTINCT (Lui poteva vincere?) ---
        winning_spots = get_threat_mask(opp_pieces, full_mask)

        if winning_spots > 0:
            if (winning_spots & played_bit) == 0:
                print(f"[PROFILER] L'avversario ha mancato una vittoria LETALE!")
                self.biases["missed_win"] += 0.5
                self.stats["fatal_errors"] += 1
            else:
                pass # Ha vinto.

        # --- FASE 2: DIFESA (Noi stavamo per vincere?) ---
        my_lethal_threats = get_threat_mask(my_pieces, full_mask)

        if my_lethal_threats > 0:
            if (my_lethal_threats & played_bit) != 0:
                # Ha parato.
                self._decay_biases(0.01)
            else:
                # Non ha parato.
                print(f"[PROFILER] L'avversario non ha parato una nostra vittoria!")
                self._analyze_missed_threat_type(my_pieces, my_lethal_threats)
                self.biases["threat_underestimation"] += 0.3
                self.stats["fatal_errors"] += 1

        # --- FASE 3: ANALISI TATTICA ---
        if winning_spots == 0 and my_lethal_threats == 0:
            self._check_positional_errors(my_pieces, played_bit, full_mask)

    def _analyze_missed_threat_type(self, my_pieces, threat_mask):
        """ Identifica geometricamente quale tipo di minaccia è stata ignorata """
        # Verticale
        vert = my_pieces & (my_pieces >> 1) & (my_pieces >> 2)
        # Shift 1 * 3 = 3 (la minaccia è sopra il tris)
        if ((vert << 3) & threat_mask) != 0:
            self.biases["vertical_weakness"] += 0.2
            return

        # Orizzontale (Shift 7)
        horiz_check = self._get_directional_threat(my_pieces, 7)
        if (horiz_check & threat_mask) != 0:
            self.biases["horizontal_weakness"] += 0.2
            return

        # Diagonali (Shift 6 e 8)
        diag1 = self._get_directional_threat(my_pieces, 6)
        diag2 = self._get_directional_threat(my_pieces, 8)

        if ((diag1 | diag2) & threat_mask) != 0:
            self.biases["diagonal_weakness"] += 0.4
            print("[PROFILER] Bias Rilevato: Cecità Diagonale")

    def _get_directional_threat(self, pieces, shift):
        # Helper per isolare minacce in una direzione
        threats = 0
        trios = pieces & (pieces >> shift) & (pieces >> (shift * 2))
        threats |= (trios << (shift * 3)) | (trios >> shift)

        gap1 = pieces & (pieces >> shift) & (pieces >> (shift * 3))
        threats |= (gap1 << (shift * 2))
        gap2 = pieces & (pieces >> (shift * 2)) & (pieces >> (shift * 3))
        threats |= (gap2 << shift)
        return threats

    def _check_positional_errors(self, my_pieces, played_bit, full_mask):
        """ Controlla se l'avversario ha ignorato espansioni diagonali """
        for shift in [6, 8]:
            pairs = my_pieces & (my_pieces >> shift)
            expansion_slots = (pairs >> shift) | (pairs << (shift * 2))
            expansion_slots &= ~full_mask # Solo spazi vuoti

            if expansion_slots > 0:
                if (expansion_slots & played_bit) == 0:
                    self.biases["diagonal_weakness"] += 0.05

    def _decay_biases(self, amount):
        for k in self.biases:
            if self.biases[k] > 1.0:
                self.biases[k] = max(1.0, self.biases[k] - amount)

    def get_adaptive_weights(self):
        return self.biases