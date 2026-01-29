"""
ai/profiler.py
Modulo di Profilazione Comportamentale.
Ottimizzato con .bit_count()
"""
from ai.analysis import get_threat_mask

class OpponentProfiler:
    def __init__(self):
        self.biases = {
            "missed_win": 1.0,
            "vertical_weakness": 1.0,
            "horizontal_weakness": 1.0,
            "diagonal_weakness": 1.0,
            "threat_underestimation": 1.0
        }

        self.stats = {
            "moves_analyzed": 0,
            "fatal_errors": 0,
        }

    def update(self, state_before, move_col, opponent_idx):
        self.stats["moves_analyzed"] += 1

        p1_map = state_before[0]
        p2_map = state_before[1]
        full_mask = p1_map | p2_map

        opp_pieces = state_before[opponent_idx]
        my_pieces = state_before[(opponent_idx + 1) % 2]

        # Calcolo bit giocato (senza heights)
        played_bit = 0
        for r in range(6):
            bit_pos = move_col * 7 + r
            if not (full_mask & (1 << bit_pos)):
                played_bit = (1 << bit_pos)
                break

        if played_bit == 0: return

        # --- FASE 1: KILLER INSTINCT ---
        winning_spots = get_threat_mask(opp_pieces, full_mask)

        if winning_spots > 0:
            if (winning_spots & played_bit) == 0:
                print(f"[PROFILER] L'avversario ha mancato una vittoria LETALE!")
                self.biases["missed_win"] += 0.5
                self.stats["fatal_errors"] += 1

        # --- FASE 2: DIFESA ---
        my_lethal_threats = get_threat_mask(my_pieces, full_mask)

        if my_lethal_threats > 0:
            if (my_lethal_threats & played_bit) != 0:
                self._decay_biases(0.01)
            else:
                print(f"[PROFILER] L'avversario non ha parato una nostra vittoria!")
                self._analyze_missed_threat_type(my_pieces, my_lethal_threats)
                self.biases["threat_underestimation"] += 0.3
                self.stats["fatal_errors"] += 1

        # --- FASE 3: ANALISI TATTICA ---
        if winning_spots == 0 and my_lethal_threats == 0:
            self._check_positional_errors(my_pieces, played_bit, full_mask)

    def _analyze_missed_threat_type(self, my_pieces, threat_mask):
        # Verticale
        vert = my_pieces & (my_pieces >> 1) & (my_pieces >> 2)
        if ((vert << 3) & threat_mask) != 0:
            self.biases["vertical_weakness"] += 0.2
            return

        # Orizzontale
        horiz_check = self._get_directional_threat(my_pieces, 7)
        if (horiz_check & threat_mask) != 0:
            self.biases["horizontal_weakness"] += 0.2
            return

        # Diagonali
        diag1 = self._get_directional_threat(my_pieces, 6)
        diag2 = self._get_directional_threat(my_pieces, 8)

        if ((diag1 | diag2) & threat_mask) != 0:
            self.biases["diagonal_weakness"] += 0.4
            print("[PROFILER] Bias Rilevato: Cecità Diagonale")

    def _get_directional_threat(self, pieces, shift):
        threats = 0
        trios = pieces & (pieces >> shift) & (pieces >> (shift * 2))
        threats |= (trios << (shift * 3)) | (trios >> shift)

        gap1 = pieces & (pieces >> shift) & (pieces >> (shift * 3))
        threats |= (gap1 << (shift * 2))
        gap2 = pieces & (pieces >> (shift * 2)) & (pieces >> (shift * 3))
        threats |= (gap2 << shift)
        return threats

    def _check_positional_errors(self, my_pieces, played_bit, full_mask):
        for shift in [6, 8]:
            pairs = my_pieces & (my_pieces >> shift)
            expansion_slots = (pairs >> shift) | (pairs << (shift * 2))
            expansion_slots &= ~full_mask

            if expansion_slots > 0:
                if (expansion_slots & played_bit) == 0:
                    self.biases["diagonal_weakness"] += 0.05

    def _decay_biases(self, amount):
        for k in self.biases:
            if self.biases[k] > 1.0:
                self.biases[k] = max(1.0, self.biases[k] - amount)

    def get_adaptive_weights(self):
        return self.biases