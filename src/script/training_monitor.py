import sys
import os

# Aggiunge la root del progetto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.board.engine import GameEngine
from src.ai.evaluator import AdaptiveEvaluator
from src.ai.profiler import OpponentProfiler
from src.ai.minimax import MinimaxAgent

# [IMPORTANTE] Usa la tua classe di persistenza
from src.db.persistence import GamePersistence

# Importiamo i Training Evaluator
from src.ai.bots.training_evaluators import CasualEvaluator, DiagonalBlinderEvaluator, EdgeRunnerEvaluator


def run_training_session(opponent_type="diagonal", iterations=20):
    engine = GameEngine()

    # Inizializza il Database usando la tua classe
    try:
        db = GamePersistence()
        db_status = "ONLINE"
    except Exception as e:
        print(f"[WARNING] Errore DB: {e}")
        db = None
        db_status = "OFFLINE"

    # --- 1. SETUP IA ADATTIVA (Player 0) ---
    profiler = OpponentProfiler()

    # [MEMORIA] Se il DB è online, carichiamo i bias vecchi per imparare dal passato
    if db:
        opp_key = "diagonal_blinder" if opponent_type == "diagonal" else (
            "edge_runner" if opponent_type == "edge" else "casual_novice")
        past_biases = db.get_latest_biases(opp_key)
        if past_biases:
            print(f"[MEMORY] Caricati bias precedenti: {past_biases}")
            profiler.biases.update(past_biases)

    ai_evaluator = AdaptiveEvaluator(profiler)
    ai_agent = MinimaxAgent(engine, ai_evaluator, depth=4)

    # --- 2. SETUP AVVERSARIO DI TRAINING (Player 1) ---
    if opponent_type == "diagonal":
        opp_evaluator = DiagonalBlinderEvaluator()
        opp_name = "diagonal_blinder"
        display_name = "Diagonal Blinder (Weak Diag)"
        opp_depth = 4
    elif opponent_type == "edge":
        opp_evaluator = EdgeRunnerEvaluator()
        opp_name = "edge_runner"
        display_name = "Edge Runner (No Center)"
        opp_depth = 4
    else:
        opp_evaluator = CasualEvaluator()
        opp_name = "casual_novice"
        display_name = "Casual Novice (Standard)"
        opp_depth = 2

    # Creiamo l'agente avversario
    opponent_agent = MinimaxAgent(engine, opp_evaluator, depth=opp_depth)

    print(f"\n[DEBUG MONITOR] IA Adattiva (D4) vs {display_name} (D{opp_depth}) | DB: {db_status}")

    if hasattr(profiler, 'RATES'):
        rates_str = ", ".join([f"{k}: {v}" for k, v in profiler.RATES.items()])
        print(f"[CONFIG] Limit: {profiler.LIMIT} | Smoothing: {profiler.SMOOTHING} | Rates: {{{rates_str}}}")

    wins = 0
    draws = 0
    losses = 0

    # --- CICLO DI PARTITE ---
    for i in range(1, iterations + 1):
        engine.reset()
        ai_agent.transposition_table = {}
        opponent_agent.transposition_table = {}

        first_player = 0 if i % 2 != 0 else 1
        turn = first_player
        game_over = False
        moves = 0

        while not game_over:
            if turn == 0:
                # IA Adattiva
                move = ai_agent.choose_move(0)
                if move is None:
                    game_over = True
                    winner = "draw"
                else:
                    engine.drop_piece(move, 0)
            else:
                # Bot Avversario
                move = opponent_agent.choose_move(1)
                if move is None:
                    game_over = True
                    winner = "draw"
                else:
                    engine.drop_piece(move, 1)
                    profiler.update(engine.get_state(), move, 1)

            moves += 1
            if not game_over:
                if engine.check_victory(turn):
                    game_over = True
                    winner = "ai" if turn == 0 else "bot"
                # Fix controllo pareggio per engine bitboard
                elif len([c for c in range(7) if engine.is_valid_location(c)]) == 0:
                    game_over = True
                    winner = "draw"

            turn = (turn + 1) % 2

        # Risultato
        result = "win" if winner == "ai" else ("loss" if winner == "bot" else "draw")

        cooling_msg = ""
        if result == "loss":
            profiler.cooling_after_loss()
            cooling_msg = " >> [CHECK] Cooling check eseguito."

        if winner == "ai":
            wins += 1
        elif winner == "bot":
            losses += 1
        else:
            draws += 1

        # [SALVATAGGIO CORRETTO] Usa il metodo della tua classe GamePersistence
        db_msg = ""
        if db:
            try:
                db.save_game_result(
                    opponent_name=opp_name,
                    result=result,
                    final_biases=profiler.get_adaptive_weights(),
                    moves_count=moves
                )
            except Exception as e:
                db_msg = f"[DB ERR: {e}]"

        # Stampa Bias
        biases = profiler.get_adaptive_weights()
        b_str = " | ".join([f"{k[:4]}: {v:.2f}" for k, v in biases.items() if abs(v - 1.0) > 0.01])
        if not b_str: b_str = "NEUTRAL"

        icon = "🟢" if winner == "ai" else ("🔴" if winner == "bot" else "⚪")
        print(
            f"Match {i:03d} {icon} | {'AI ' if winner == 'ai' else 'BOT' if winner == 'bot' else 'DRAW'} {moves} mosse | {db_msg} Bias: [{b_str}]{cooling_msg}")

    print("\n" + "=" * 40)
    print(f"📊 REPORT FINALE vs {display_name.upper()}")
    print(f"Vittorie IA: {wins} ({wins / iterations * 100:.1f}%)")
    print(f"Vittorie BOT: {losses}")
    print(f"Pareggi:     {draws}")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    run_training_session("diagonal", iterations=100)