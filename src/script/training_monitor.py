import sys
import os
import random
import time

# Hack per path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.board.engine import GameEngine
from src.ai.minmax import MinimaxAgent # Verifica che il nome file sia corretto (minimax.py o minmax.py)
from src.ai.evaluator import AdaptiveEvaluator
from src.ai.profiler import OpponentProfiler
from src.db.persistence import GamePersistence
from src.ai.bots.training_evaluators import DiagonalBlinderEvaluator, EdgeRunnerEvaluator, CasualEvaluator

# --- STRUMENTI DI DEBUGGING ---

def print_ascii_board(engine):
    """ Visualizza lo stato della bitboard nel terminale per debug visivo. """
    print("\n--- DEBUG BOARD DUMP ---")
    matrix = engine.get_board_matrix()
    for row in matrix:
        line = "|"
        for cell in row:
            if cell == 0: symbol = "."
            elif cell == 1: symbol = "X" # Player 0 (IA)
            elif cell == 2: symbol = "O" # Player 1 (Bot)
            line += f" {symbol} "
        print(line + "|")
    print("-" * 23)
    print(f"Counter: {engine.counter} | Heights: {engine.heights}")
    print("------------------------\n")

def check_integrity(engine, context=""):
    """
    Verifica che il contatore delle mosse sia sincronizzato con le bitboard.
    Fondamentale per capire se il Minimax sta corrompendo lo stato.
    """
    p1_bits = engine.bitboards[0].bit_count()
    p2_bits = engine.bitboards[1].bit_count()
    total_pieces = p1_bits + p2_bits

    if total_pieces != engine.counter:
        print(f"\n[CRITICAL ERROR] {context}")
        print(f"DESYNC RILEVATO: Engine.counter dice {engine.counter}, ma ci sono {total_pieces} bit attivi!")
        print_ascii_board(engine)
        raise RuntimeError("Game State Corrupted")

    if engine.counter > 42:
        print(f"\n[CRITICAL ERROR] {context}")
        print(f"OVERFLOW RILEVATO: Mosse {engine.counter} > 42!")
        print_ascii_board(engine)
        raise RuntimeError("Move Overflow")

# --- SIMULAZIONE ---

def simulate_game(ai_agent, bot_agent, engine, profiler, starting_player, starting_biases=None, match_id=0):
    engine.reset()

    # Reset Profiler
    profiler.__init__()
    if starting_biases:
        profiler.biases = starting_biases.copy()

    game_over = False
    winner = None

    # Debug: tracciamo la storia delle mosse
    move_history = []

    while not game_over:
        # 1. CONTROLLO INTEGRITÀ PRE-MOSSA
        try:
            check_integrity(engine, context=f"Match {match_id} - Pre-Turn Check")
        except RuntimeError as e:
            print(f"Ultima sequenza mosse: {move_history}")
            sys.exit(1)

        current_turn = (starting_player + engine.counter) % 2
        player_role = "IA (X)" if current_turn == 0 else "BOT (O)"

        # --- ESECUZIONE MOSSA ---
        if current_turn == 0:
            # Turno IA
            move = ai_agent.choose_move(0)
            if move is None:
                print(f"[ERROR] L'IA si è arresa (None returned) alla mossa {engine.counter}!")
                print_ascii_board(engine)
                break
            engine.drop_piece(move, 0)
        else:
            # Turno BOT (Opponent)
            state_before = engine.get_state()
            move = bot_agent.choose_move(1)
            if move is None:
                print(f"[ERROR] Il BOT si è arreso (None returned) alla mossa {engine.counter}!")
                print_ascii_board(engine)
                break

            engine.drop_piece(move, 1)
            profiler.update(state_before, move, 1)

        move_history.append(move)

        # 2. CONTROLLO VITTORIA E PAREGGIO
        if engine.check_victory(0):
            winner = "ai"
            game_over = True
        elif engine.check_victory(1):
            winner = "bot"
            game_over = True
        elif engine.counter >= 42:
            winner = "draw"
            game_over = True

        # 3. DEBUG DRAW SOSPETTO
        # Se il Minimax dice "non ci sono mosse" ma il counter < 42
        if not game_over and engine.counter < 42:
            # Verifichiamo se ci sono colonne piene non rilevate
            pass

    # 4. POST-GAME CHECK
    if winner == "draw" and engine.counter < 42:
        print(f"[WARNING] Pareggio Prematuro alla mossa {engine.counter}. Bug nel check validità?")
        print_ascii_board(engine)

    return winner, engine.counter, profiler.get_adaptive_weights()

def run_training_session(bot_type, iterations=10):
    engine = GameEngine()
    profiler = OpponentProfiler()
    persistence = GamePersistence()

    # Setup Agenti
    ai_eval = AdaptiveEvaluator(profiler)
    ai_agent = MinimaxAgent(engine, ai_eval, depth=4)

    if bot_type == "diagonal":
        bot_agent = MinimaxAgent(engine, DiagonalBlinderEvaluator(), depth=4)
        bot_name = "diagonal_blinder"
    elif bot_type == "edge":
        bot_agent = MinimaxAgent(engine, EdgeRunnerEvaluator(), depth=3)
        bot_name = "edge_runner"
    else:
        bot_agent = MinimaxAgent(engine, CasualEvaluator(), depth=2)
        bot_name = "casual_novice"

    print(f"\n[DEBUG MONITOR] Avvio sessione controllata: IA vs {bot_name}")
    print("[DEBUG MONITOR] Integrity Checks: ACTIVE")

    latest_biases = persistence.get_latest_biases(bot_name)

    stats = {"ai": 0, "bot": 0, "draw": 0}

    for i in range(iterations):
        current_starter = random.choice([0, 1])

        start_time = time.time()
        winner, moves, new_biases = simulate_game(ai_agent, bot_agent, engine, profiler, current_starter, latest_biases, match_id=i)
        duration = time.time() - start_time

        latest_biases = new_biases
        stats[winner] += 1

        # Salvataggio
        result = "win" if winner == "ai" else ("loss" if winner == "bot" else "draw")
        persistence.save_game_result(bot_name, result, new_biases, moves)

        # Output compatto
        icon = "🟢" if winner == "ai" else "🔴" if winner == "bot" else "⚪"
        print(f"Match {i+1:02d} {icon} | {winner.upper()} in {moves} mosse ({duration:.2f}s) | Bias Diag: {new_biases.get('diagonal_weakness', 1.0):.2f}")

    print("\n--- RISULTATI SESSIONE ---")
    print(f"IA Wins: {stats['ai']}")
    print(f"Bot Wins: {stats['bot']}")
    print(f"Draws:   {stats['draw']}")

if __name__ == "__main__":
    # Eseguiamo poche iterazioni per vedere subito se crasha
    run_training_session("novice", iterations=100)