"""
scripts/training_monitor.py
Script di simulazione "Headless" con Memoria Persistente.
L'IA carica i bias precedenti dal DB prima di iniziare.
"""
import sys
import os
import random

# Hack per path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.board.engine import GameEngine
from src.ai.minmax import MinimaxAgent
from src.ai.evaluator import AdaptiveEvaluator
from src.ai.profiler import OpponentProfiler
from src.db.persistence import GamePersistence
from src.ai.bots.training_evaluators import DiagonalBlinderEvaluator, EdgeRunnerEvaluator, CasualEvaluator

def simulate_game(ai_agent, bot_agent, engine, profiler, starting_player, starting_biases=None):
    """
    Simula una singola partita.
    Se starting_biases è presente, il Profiler viene inizializzato con quei valori
    invece di partire da zero.
    """
    engine.reset()

    # --- GESTIONE MEMORIA ---
    profiler.__init__() # Reset strutture base (stats, etc.)
    if starting_biases:
        # Iniettiamo la memoria a lungo termine
        profiler.biases = starting_biases.copy()

    game_over = False
    winner = None

    while not game_over:
        current_turn = (starting_player + engine.counter) % 2

        if current_turn == 0:
            # TURNO IA (Adaptive)
            move = ai_agent.choose_move(0)
            engine.drop_piece(move, 0)
        else:
            # TURNO BOT (Dummy)
            state_before = engine.get_state() # Snapshot per Profiler
            move = bot_agent.choose_move(1)
            engine.drop_piece(move, 1)

            # Il Profiler osserva e impara (o aggiorna i bias esistenti)
            # Nota: Passiamo 1 come indice avversario
            profiler.update(state_before, move, 1)

        # Controlli vittoria
        if engine.check_victory(0):
            winner = "ai"
            game_over = True
        elif engine.check_victory(1):
            winner = "bot"
            game_over = True
        elif engine.counter >= 42:
            winner = "draw"
            game_over = True

    return winner, engine.counter, profiler.get_adaptive_weights()

def run_training_session(bot_type, iterations=10):
    # 1. Init
    engine = GameEngine()
    profiler = OpponentProfiler()
    persistence = GamePersistence()

    # 2. Configurazione IA
    ai_eval = AdaptiveEvaluator(profiler)
    ai_agent = MinimaxAgent(engine, ai_eval, depth=4)

    # 3. Configurazione Bot
    if bot_type == "diagonal":
        bot_eval = DiagonalBlinderEvaluator()
        bot_agent = MinimaxAgent(engine, bot_eval, depth=4)
        bot_name = "diagonal_blinder"
    elif bot_type == "edge":
        bot_eval = EdgeRunnerEvaluator()
        bot_agent = MinimaxAgent(engine, bot_eval, depth=3)
        bot_name = "edge_runner"
    else:
        bot_eval = CasualEvaluator()
        bot_agent = MinimaxAgent(engine, bot_eval, depth=2)
        bot_name = "casual_novice"

    print(f"\n[TRAINING] Avvio sessione: IA vs {bot_name}")

    # --- CARICAMENTO MEMORIA PERSISTENTE ---
    latest_biases = persistence.get_latest_biases(bot_name)
    if latest_biases:
        print(f"[MEMORY] Trovati bias precedenti nel DB. L'IA parte avvantaggiata!")
        print(f"[MEMORY] Bias caricati: {latest_biases}")
    else:
        print(f"[MEMORY] Nessun dato precedente. L'IA inizierà l'analisi da zero.")

    print(f"[CONFIG] Iterazioni: {iterations} | DB: SQLite")

    current_starter = random.choice([0, 1])

    for i in range(iterations):
        # Passiamo i bias caricati (o quelli aggiornati dalla partita precedente se volessimo continuità)
        # In questo script:
        # - Se vogliamo apprendimento intra-sessione: passiamo latest_biases aggiornato a ogni ciclo.
        # - Se vogliamo testare solo il caricamento iniziale: passiamo latest_biases fisso all'inizio.
        # Qui implementiamo l'apprendimento CONTINUO: il risultato di una partita diventa l'input della prossima.

        winner, moves, new_biases = simulate_game(ai_agent, bot_agent, engine, profiler, current_starter, latest_biases)

        # Aggiorniamo i bias per il prossimo round nella RAM
        latest_biases = new_biases

        result = "win" if winner == "ai" else ("loss" if winner == "bot" else "draw")

        # Salviamo su DB (così la prossima sessione ripartirà da qui)
        persistence.save_game_result(bot_name, result, new_biases, moves)

        starter_str = "IA" if current_starter == 0 else "BOT"
        print(f" > Match {i+1:03d}: Start={starter_str} | Winner={winner.upper()} | Moves={moves}")

        current_starter = 1 - current_starter

    print("\n[TRAINING] Sessione completata. Dati salvati.")

if __name__ == "__main__":
    run_training_session("diagonal", iterations=20)