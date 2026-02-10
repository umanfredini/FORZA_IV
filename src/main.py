import pygame
import sys

# --- MODULI CORE (MVC) ---
from board.engine import GameEngine
from board.interface import GameView
from board.controller import GameController
from board.menu import MenuManager, STATE_MAIN_MENU, STATE_GAME, STATE_BOT_SELECT, STATE_GAME_OVER

# --- MODULI INTELLIGENZA ARTIFICIALE ---
from ai.minimax import MinimaxAgent
from ai.evaluator import AdaptiveEvaluator
from ai.bots.training_evaluators import CasualEvaluator, DiagonalBlinderEvaluator, EdgeRunnerEvaluator
from db.persistence import GamePersistence


def main():
    """
    Punto di ingresso principale dell'applicazione.
    Gestisce il ciclo di vita del gioco, gli eventi di input e la macchina a stati.
    """

    # 1. Inizializzazione Pygame
    pygame.init()

    # Impostiamo la risoluzione a 1000x700
    WIDTH, HEIGHT = 1000, 700
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Forza 4 - AI Adattiva (Predator Engine)")

    # 2. Inizializzazione Componenti (Model-View-Controller + Persistence)
    engine = GameEngine()

    # La view carica gli asset grafici all'avvio
    view = GameView(screen)

    controller = GameController(engine, view)
    menu = MenuManager(screen)
    persistence = GamePersistence()

    # 3. Variabili di Stato
    bot = None
    app_state = STATE_MAIN_MENU
    game_mode = "PVP"

    # Variabili per la gestione del Game Over
    winner_text = ""
    btn_retry_rect = None
    btn_menu_rect = None

    clock = pygame.time.Clock()

    # --- MAIN LOOP ---
    while True:
        clock.tick(60)  # Limitiamo a 60 FPS per evitare carico CPU inutile

        # -----------------------------------------------------------------
        # STATO 1: MENU PRINCIPALE
        # -----------------------------------------------------------------
        if app_state == STATE_MAIN_MENU:
            # Il menu gestisce il proprio rendering internamente
            menu.draw_main_menu()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        # Modalità Giocatore vs Giocatore
                        game_mode = "PVP"
                        controller.reset_for_new_round()
                        app_state = STATE_GAME
                    elif event.key == pygame.K_2:
                        # Modalità Giocatore vs Bot (Passiamo alla selezione)
                        game_mode = "PVE"
                        app_state = STATE_BOT_SELECT

        # -----------------------------------------------------------------
        # STATO 2: SELEZIONE BOT
        # -----------------------------------------------------------------
        elif app_state == STATE_BOT_SELECT:
            menu.draw_bot_selection()

            selected_bot = None
            bot_db_name = None  # Nome usato nel DB per recuperare i Bias

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    # Tasto 1: Novizio (Casual)
                    if event.key == pygame.K_1:
                        selected_bot = MinimaxAgent(engine, CasualEvaluator(), depth=2)
                        bot_db_name = "casual_novice"

                    # Tasto 2: Bias Diagonale (Training Target)
                    elif event.key == pygame.K_2:
                        selected_bot = MinimaxAgent(engine, DiagonalBlinderEvaluator(), depth=4)
                        bot_db_name = "diagonal_blinder"

                    # Tasto 3: Edge Runner (Strategia alternativa)
                    elif event.key == pygame.K_3:
                        selected_bot = MinimaxAgent(engine, EdgeRunnerEvaluator(), depth=3)
                        bot_db_name = "edge_runner"

                    # Tasto 4: IA Adattiva (Impara dall'umano live)
                    elif event.key == pygame.K_4:
                        adaptive_eval = AdaptiveEvaluator(controller.profiler)
                        selected_bot = MinimaxAgent(engine, adaptive_eval, depth=4)
                        bot_db_name = "human_player"

                    # Tasto ESC: Torna indietro
                    elif event.key == pygame.K_ESCAPE:
                        app_state = STATE_MAIN_MENU

            # Se è stato selezionato un bot, configuriamo la partita
            if selected_bot:
                bot = selected_bot

                # --- CARICAMENTO MEMORIA PERSISTENTE ---
                # Cerchiamo nel DB se abbiamo già giocato contro questo tipo di bot.
                # Se sì, carichiamo i suoi "bias" noti nel Profiler.
                if bot_db_name:
                    latest_biases = persistence.get_latest_biases(bot_db_name)
                    if latest_biases:
                        print(f"[SYSTEM] Caricati bias storici per {bot_db_name}: {latest_biases}")
                        controller.profiler.biases = latest_biases
                    else:
                        # Se è la prima volta, resettiamo il profiler per imparare da zero
                        print(f"[SYSTEM] Nuovo avversario {bot_db_name}. Profiler resettato.")
                        controller.profiler.__init__()

                controller.reset_for_new_round()
                app_state = STATE_GAME

        # -----------------------------------------------------------------
        # STATO 3: GIOCO ATTIVO
        # -----------------------------------------------------------------
        elif app_state == STATE_GAME:
            # 1. Rendering Scena (Sfondo, Pedine, Griglia, UI)
            # Passiamo i dati necessari alla View per disegnare il frame corrente
            view.draw(engine.get_board_matrix(), controller.stats, profiler=controller.profiler)

            # 2. Logica Turno BOT (Solo in PvE)
            if game_mode == "PVE" and controller.turn == 1 and not controller.game_over:
                # Forziamo un update grafico per mostrare l'ultima mossa umana prima che il bot "pensi"
                pygame.display.update()
                pygame.time.wait(500)  # Piccola pausa per realismo (simula il pensiero)

                # Il bot sceglie la mossa (ritorna un indice colonna 0-6)
                col = bot.choose_move(1)

                # Aggiorniamo la barra EVAL in base alla valutazione del bot
                controller.stats["ai_eval"] = bot.evaluator.evaluate(engine, 1)

                if col is not None:
                    # Simuliamo una coordinata X per il controller
                    # (Il controller divide per sq_size, quindi moltiplichiamo per sq_size)
                    simulated_x = int(col * view.sq_size + (view.sq_size / 2))
                    win, player = controller.process_turn(simulated_x)

                    if win:
                        winner_text = "IL BOT VINCE!"
                        app_state = STATE_GAME_OVER

            # 3. Logica Input UMANO
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    app_state = STATE_MAIN_MENU

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Blocchiamo input se tocca al bot
                    if game_mode == "PVE" and controller.turn == 1: continue

                    if event.button == 1:
                        # --- GESTIONE CLICK ---

                        # A. Pulsante RESET GAME
                        if hasattr(view, 'reset_rect') and view.reset_rect.collidepoint(event.pos):
                            print("[INPUT] Reset richiesto dall'utente.")
                            controller.reset_for_new_round()
                            continue  # Saltiamo il resto della logica per questo frame

                        # B. Scacchiera (Nuova gestione coordinate centrate)
                        # Verifichiamo se il click è avvenuto dentro il rettangolo della board
                        if hasattr(view, 'board_rect') and view.board_rect.collidepoint(event.pos):
                            # Calcoliamo la X relativa all'inizio della griglia (slot_start_x)
                            # Questo converte la coordinata assoluta dello schermo in una relativa alla board
                            relative_x = event.pos[0] - view.slot_start_x

                            # process_turn si aspetta una X che parta da 0 per la colonna 0
                            win, player = controller.process_turn(relative_x)

                            # Se stiamo giocando contro IA, aggiorniamo l'Eval Bar
                            if game_mode == "PVE" and bot:
                                controller.stats["ai_eval"] = bot.evaluator.evaluate(engine, 1)

                            if win:
                                w_name = "GIOCATORE 1" if player == 0 else "GIOCATORE 2"
                                winner_text = f"{w_name} VINCE!"
                                app_state = STATE_GAME_OVER

            # 4. UPDATE FINALE (Anti-Flickering)
            # Aggiorniamo lo schermo una sola volta alla fine del ciclo logico
            pygame.display.update()

        # -----------------------------------------------------------------
        # STATO 4: GAME OVER (MODAL)
        # -----------------------------------------------------------------
        elif app_state == STATE_GAME_OVER:
            # 1. Disegna sfondo (Scacchiera + Sidebar) - Scrive sul buffer
            view.draw(engine.get_board_matrix(), controller.stats, profiler=controller.profiler)

            # 2. Disegna Modal sopra lo sfondo - Scrive sul buffer
            # Ritorna i rettangoli dei pulsanti per gestire i click
            btn_retry_rect, btn_menu_rect = view.draw_game_over_modal(winner_text)

            # 3. UPDATE UNICO (FIX FLICKERING)
            pygame.display.update()

            # 4. Gestione Eventi Modal
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos

                    # Click su "GIOCA ANCORA"
                    if btn_retry_rect.collidepoint(mouse_pos):
                        controller.reset_for_new_round()
                        app_state = STATE_GAME

                    # Click su "TORNA AL MENU"
                    elif btn_menu_rect.collidepoint(mouse_pos):
                        app_state = STATE_MAIN_MENU


if __name__ == "__main__":
    main()