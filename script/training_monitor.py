"""
scripts/training_monitor.py
Script per l'allenamento massivo e la verifica delle performance.
"""
import sys
import os

# Aggiunge la cartella radice al path per permettere gli import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from board.engine import GameEngine
from ai.minmax import MinimaxAgent
from ai.evaluator import AdaptiveEvaluator
from ai.profiler import OpponentProfiler
from db.persistence import GamePersistence
from ai.bots.training_evaluators import DiagonalBlinderEvaluator, EdgeRunnerEvaluator, CasualEvaluator


def simulate_game(ai_agent, bot_agent, engine, profiler):
    engine.reset()
    # Reset del profiler per ogni nuova partita (apprendimento fresco)
    profiler.__init__()

    moves_count = 0
    game_over = False
    winner = None

    while not game_over:
        # Turno 0: La nostra IA (Giallo)
        if engine.counter % 2 == 0:
            move = ai_agent.choose_move(0)
            engine.drop_piece(move, 0)
        # Turno 1: Il Bot di allenamento (Rosso)
        else:
            state_before = engine.get_state()
            move = bot_agent.choose_move(1)
            engine.drop_piece(move, 1)
            # IL PROFILER ANALIZZA LA MOSSA DEL BOT
            profiler.update(engine, state_before, move, 1)

        moves_count += 1

        # Controllo Vittoria
        if engine.check_victory(0):
            winner = "ai"
            game_over = True
        elif engine.check_victory(1):
            winner = "bot"
            game_over = True
        elif engine.counter >= 42:
            winner = "draw"
            game_over = True

    return winner, moves_count, profiler.get_adaptive_weights()


def run_training_session(bot_type, iterations=10):
    engine = GameEngine()
    profiler = OpponentProfiler()
    persistence = GamePersistence()

    # 1. Configura la nostra IA
    ai_eval = AdaptiveEvaluator(profiler)
    ai_agent = MinimaxAgent(engine, ai_eval, depth=4)

    # 2. Configura il Bot avversario
    if bot_type == "diagonal":
        bot_eval = DiagonalBlinderEvaluator()
        bot_agent = MinimaxAgent(engine, bot_eval, depth=4)
        name = "diagonal_blinder"
    elif bot_type == "edge":
        bot_eval = EdgeRunnerEvaluator()
        bot_agent = MinimaxAgent(engine, bot_eval, depth=3)
        name = "edge_runner"
    else:
        bot_eval = CasualEvaluator()
        bot_agent = MinimaxAgent(engine, bot_eval, depth=2)
        name = "casual_novice"

    print(f"\n[TRAINING] Inizio sessione contro: {name} ({iterations} partite)")

    for i in range(iterations):
        winner, moves, final_biases = simulate_game(ai_agent, bot_agent, engine, profiler)

        # Salvataggio nel Database SQLite
        persistence.save_game_result(
            opponent_name=name,
            result="win" if winner == "ai" else ("loss" if winner == "bot" else "draw"),
            final_biases=final_biases,
            moves_count=moves
        )
        print(f" Partita {i + 1}/{iterations}: Vincitore -> {winner} in {moves} mosse.")


if __name__ == "__main__":
    # Test veloce: 10 partite contro il cieco diagonale
    run_training_session("diagonal", iterations=10)