import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.board.engine import GameEngine
from src.ai.evaluator import AdaptiveEvaluator
from src.ai.profiler import OpponentProfiler
from src.ai.minimax import MinimaxAgent
from src.ai.opening_manager import OpeningManager
from src.db.persistence import GamePersistence
from src.ai.bots.training_evaluators import CasualEvaluator, DiagonalBlinderEvaluator, EdgeRunnerEvaluator


def run_training_session(opponent_type="diagonal", iterations=20, silent=False):
    """
    Esegue una sessione di training.
    :param silent: Se True, non stampa il log mossa per mossa, ma solo una barra di avanzamento.
    :return: (wins, losses, draws)
    """
    engine = GameEngine()

    try:
        db = GamePersistence()
    except Exception:
        db = None

    opening_manager = OpeningManager(db) if db else None
    profiler = OpponentProfiler()

    if db:
        opp_key = "diagonal_blinder" if opponent_type == "diagonal" else (
            "edge_runner" if opponent_type == "edge" else "casual_novice")
        past_biases = db.get_latest_biases(opp_key)
        if past_biases:
            profiler.biases.update(past_biases)

    ai_evaluator = AdaptiveEvaluator(profiler)
    ai_agent = MinimaxAgent(engine, ai_evaluator, depth=4)

    # Configurazione Avversario
    if opponent_type == "diagonal":
        opp_evaluator = DiagonalBlinderEvaluator()
        opp_depth = 4
        opp_noise = 0.1
    elif opponent_type == "edge":
        opp_evaluator = EdgeRunnerEvaluator()
        opp_depth = 4
        opp_noise = 0.2
    else:
        # Fallback per "casual", "novice" o qualsiasi altro nome
        opp_evaluator = CasualEvaluator()
        opp_depth = 2
        opp_noise = 0.3

    try:
        opponent_agent = MinimaxAgent(engine, opp_evaluator, depth=opp_depth, randomness=opp_noise)
    except TypeError:
        opponent_agent = MinimaxAgent(engine, opp_evaluator, depth=opp_depth)

    # Calcolo step per la notifica del 10%
    progress_step = max(1, iterations // 10)

    wins = 0
    draws = 0
    losses = 0

    for i in range(1, iterations + 1):
        engine.reset()
        if opening_manager: opening_manager.game_history.clear()

        # Reset Cache
        ai_agent.transposition_table = {}
        opponent_agent.transposition_table = {}

        starting_player = 0 if i % 2 != 0 else 1
        moves = 0
        game_over = False
        winner = None

        while not game_over:
            if moves >= 42:
                game_over = True;
                winner = "draw";
                break

            current_turn = (starting_player + moves) % 2

            if current_turn == 0:
                move = None
                if opening_manager: move, _ = opening_manager.get_best_move(engine)
                if move is None: move = ai_agent.choose_move(0)

                if move is None:
                    game_over = True;
                    winner = "draw"
                else:
                    if opening_manager: opening_manager.record_move(engine, move, 0)
                    engine.drop_piece(move, 0)
            else:
                state_before = engine.get_state()
                move = opponent_agent.choose_move(1)

                if move is None:
                    game_over = True;
                    winner = "draw"
                else:
                    if opening_manager: opening_manager.record_move(engine, move, 1)
                    engine.drop_piece(move, 1)
                    profiler.update(state_before, move, 1)

            moves += 1
            if not game_over:
                if engine.check_victory(current_turn):
                    game_over = True
                    winner = "ai" if current_turn == 0 else "bot"
                elif len([c for c in range(7) if engine.is_valid_location(c)]) == 0:
                    game_over = True
                    winner = "draw"

        # Backpropagation
        if opening_manager and winner is not None:
            w_idx = 0 if winner == "ai" else (1 if winner == "bot" else "draw")
            opening_manager.finalize_game(w_idx)

        # Stats Update
        result = "loss" if winner == "bot" else ("win" if winner == "ai" else "draw")

        if result == "loss": profiler.cooling_after_loss()

        if winner == "ai":
            wins += 1
        elif winner == "bot":
            losses += 1
        else:
            draws += 1

        if db:
            db.save_game_result(opponent_type, result, profiler.get_adaptive_weights(), moves)

        # --- GESTIONE OUTPUT SILENZIOSO / PROGRESSO ---
        if not silent:
            # Vecchio comportamento: stampa tutto
            icon = "🟢" if winner == "ai" else ("🔴" if winner == "bot" else "⚪")
            print(f"Match {i:03d} {icon} | {result.upper()} | Moves: {moves}")
        else:
            # Nuovo comportamento: Stampa solo al 10, 20, 30... %
            if i % progress_step == 0 or i == iterations:
                percent = (i / iterations) * 100
                print(f"   ... Progresso: {percent:.0f}% ({i}/{iterations}) completato.")

    # Restituisce i dati per la tabella finale
    return wins, losses, draws


if __name__ == "__main__":
    # Parametri
    OPPONENT = "edge"  # o "edge", "diagonal"
    ITERATIONS = 100

    print(f"🚀 Avvio Training vs {OPPONENT.upper()} ({ITERATIONS} partite)...")

    # Esecuzione e cattura risultati
    w, l, d = run_training_session(OPPONENT, iterations=ITERATIONS, silent=False)

    # Calcolo percentuali
    total = w + l + d
    win_rate = (w / total * 100) if total > 0 else 0

    # Stampa Report Finale
    print("\n" + "=" * 40)
    print(f"📊 REPORT RISULTATI ({OPPONENT.upper()})")
    print("=" * 40)
    print(f"✅ Vittorie (IA): {w}")
    print(f"❌ Sconfitte:     {l}")
    print(f"⚪ Pareggi:       {d}")
    print("-" * 40)
    print(f"📈 Win Rate:      {win_rate:.1f}%")
    print("=" * 40)