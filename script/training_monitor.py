"""
scripts/training_monitor.py
Script di simulazione "Headless" (senza grafica).
Esegue sessioni di allenamento massivo IA vs Bot e salva i dati nel DB SQLite.
Gestisce l'alternanza dei turni per garantire dati statistici bilanciati.
"""
import sys
import os
import random

# Hack per includere la cartella principale nel path e permettere gli import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- IMPORTS DEL MOTORE DI GIOCO ---
from board.engine import GameEngine
from ai.minmax import MinimaxAgent
from ai.evaluator import AdaptiveEvaluator
from ai.profiler import OpponentProfiler
from db.persistence import GamePersistence

# --- IMPORTS DEI BOT DI ALLENAMENTO ---
from ai.bots.training_evaluators import DiagonalBlinderEvaluator, EdgeRunnerEvaluator, CasualEvaluator

def simulate_game(ai_agent, bot_agent, engine, profiler, starting_player):
    """
    Simula una singola partita completa.
    :param starting_player: 0 = Inizia la Nostra IA (Giallo), 1 = Inizia il Bot (Rosso)
    """
    engine.reset()
    # Resettiamo il profiler per testare la velocità di apprendimento "da zero" in ogni match.
    # Se volessi un apprendimento continuo su 100 partite, sposta questa riga fuori dalla funzione.
    profiler.__init__()

    game_over = False
    winner = None # 'ai', 'bot', o 'draw'

    while not game_over:
        # Calcoliamo di chi è il turno corrente
        # Se starting_player è 0: Turni 0, 2, 4... -> IA (0)
        # Se starting_player è 1: Turni 0, 2, 4... -> Bot (1)
        # La formula (starting + counter) % 2 gestisce correttamente l'offset.
        current_turn = (starting_player + engine.counter) % 2

        if current_turn == 0:
            # --- TURNO IA (Adaptive) ---
            # L'IA è sempre player_idx 0 in questo contesto di simulazione
            move = ai_agent.choose_move(0)
            engine.drop_piece(move, 0)

        else:
            # --- TURNO BOT (Training Dummy) ---
            # Il Bot è sempre player_idx 1
            # Salviamo lo stato PRIMA della mossa per il Profiler
            state_before = engine.get_state()

            move = bot_agent.choose_move(1)
            engine.drop_piece(move, 1)

            # IL PROFILER ANALIZZA LA MOSSA APPENA FATTA DAL BOT
            profiler.update(engine, state_before, move, 1)

        # --- CONTROLLI FINE PARTITA ---
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
    """
    Esegue un loop di partite e salva i risultati nel Database.
    """
    # 1. Inizializzazione Componenti
    engine = GameEngine()
    profiler = OpponentProfiler()
    persistence = GamePersistence() # Si collega automaticamente a data/connect4_factory.db

    # 2. Configurazione Nostra IA (Genius)
    # Depth 4 è un buon compromesso tra velocità e intelligenza per il training
    ai_eval = AdaptiveEvaluator(profiler)
    ai_agent = MinimaxAgent(engine, ai_eval, depth=4)

    # 3. Configurazione Bot Avversario (Dummy)
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
    print(f"[CONFIG] Iterazioni: {iterations} | DB: SQLite")

    # 4. Scelta Casuale del Primo Giocatore Assoluto (50/50)
    current_starter = random.choice([0, 1])

    for i in range(iterations):
        # Eseguiamo la partita
        winner, moves, final_biases = simulate_game(ai_agent, bot_agent, engine, profiler, current_starter)

        # Determiniamo il risultato testuale per il DB
        result="win" if winner == "ai" else ("loss" if winner == "bot" else "draw"),

        # 5. Salvataggio Dati
        persistence.save_game_result(
            opponent_name=bot_name,
            result=result,
            final_biases=final_biases,
            moves_count=moves
        )

        # Output console minimalista
        starter_str = "IA" if current_starter == 0 else "BOT"
        print(f" > Match {i+1:03d}: Start={starter_str} | Winner={winner.upper()} | Moves={moves} | Bias={final_biases}")

        # 6. ALTERNANZA RIGOROSA: Se ha iniziato 0, il prossimo è 1.
        current_starter = 1 - current_starter

    print("\n[TRAINING] Sessione completata. Dati salvati in 'data/connect4_factory.db'.")

if __name__ == "__main__":
    # Esempio di utilizzo:
    # Puoi cambiare "diagonal" con "edge" o "casual"
    # Puoi aumentare le iterazioni a 50 o 100 per test seri
    run_training_session("diagonal", iterations=20)