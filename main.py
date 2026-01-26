import pygame
import sys
from board.engine import GameEngine
from board.interface import GameView
from board.controller import GameController
# Assicurati che il file si chiami 'minimax.py' dentro la cartella 'ai'
from ai.minmax import MinimaxBot

# --- COSTANTI DI STATO ---
STATE_MENU = 0
STATE_GAME = 1


def draw_menu(screen, font):
    """
    * Disegna il menu principale con le opzioni di gioco.
    """
    screen.fill((30, 30, 30))
    title = font.render("FORZA 4 - MAIN MENU", True, (255, 255, 255))
    opt1 = font.render("1. Giocatore vs Giocatore", True, (200, 200, 200))
    opt2 = font.render("2. Giocatore vs Bot (AI)", True, (200, 200, 200))

    # Centratura testo
    screen.blit(title, (screen.get_width() // 2 - title.get_width() // 2, 100))
    screen.blit(opt1, (screen.get_width() // 2 - opt1.get_width() // 2, 300))
    screen.blit(opt2, (screen.get_width() // 2 - opt2.get_width() // 2, 400))

    pygame.display.update()


def main():
    """
    * Funzione principale (Entry Point) dell'applicazione.
    * Gestisce il ciclo di vita del gioco, gli stati (Menu/Game) e il loop degli eventi.
    """
    pygame.init()
    screen = pygame.display.set_mode((700, 700))
    pygame.display.set_caption("Forza 4 - AI & PvP")

    # Font di sistema sicuro
    font = pygame.font.SysFont("Arial", 40, bold=True)

    engine = GameEngine()
    view = GameView(screen)
    controller = GameController(engine, view)

    # Inizializzazione Bot (Profondità 4 per velocità, 6 per sfida)
    try:
        bot = MinimaxBot(depth=1)
    except Exception as e:
        print(f"Errore caricamento Bot: {e}")
        return

    app_state = STATE_MENU
    game_mode = "PVP"  # "PVP" o "PVE"

    while True:
        # -----------------------------------------------------------------
        # GESTIONE MENU
        # -----------------------------------------------------------------
        if app_state == STATE_MENU:
            draw_menu(screen, font)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        game_mode = "PVP"
                        app_state = STATE_GAME
                        controller.reset_for_new_round()
                    elif event.key == pygame.K_2:
                        game_mode = "PVE"
                        app_state = STATE_GAME
                        controller.reset_for_new_round()

        # -----------------------------------------------------------------
        # GESTIONE PARTITA
        # -----------------------------------------------------------------
        elif app_state == STATE_GAME:

            # --- LOGICA TURNO BOT (Fuori dal loop eventi) ---
            # Esegue solo se è PVE, tocca al bot (turn 1) e il gioco non è finito
            if game_mode == "PVE" and controller.turn == 1 and not controller.game_over:
                pygame.time.wait(500)  # Delay per realismo

                # 1. Ottieni mossa e punteggio (Unpacking corretto)
                col, score = bot.get_best_move(engine)
                controller.stats["ai_eval"] = score

                # 2. Aggiorna la barra di valutazione con il pensiero del bot
                quick_eval = bot.get_evaluation(engine)
                controller.stats["ai_eval"] = quick_eval

                if col is not None:
                    # 3. Esegui la mossa
                    simulated_x = col * view.sq_size + 10
                    win, player = controller.process_turn(simulated_x)
                    view.draw(engine.get_board_matrix(), controller.stats)

                    if win:
                        print(f"Il Bot ha vinto!")
                        pygame.time.wait(2000)
                        app_state = STATE_MENU

            # --- LOGICA INPUT UMANO ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Solo click sinistro

                        # Se tocca al bot, ignora i click dell'umano
                        if game_mode == "PVE" and controller.turn == 1:
                            continue

                        # 1. Processa mossa umana
                        win, player = controller.process_turn(event.pos[0])

                        # 2. Se PVE, chiedi al bot di valutare la mossa umana subito
                        if game_mode == "PVE" and not win:
                            quick_eval = bot.get_evaluation(engine)
                            controller.stats["ai_eval"] = quick_eval

                        # 3. Aggiorna grafica
                        view.draw(engine.get_board_matrix(), controller.stats)

                        if win:
                            winner_name = "Giocatore 1" if player == 0 else (
                                "Giocatore 2" if game_mode == "PVP" else "Bot")
                            print(f"{winner_name} ha vinto!")
                            pygame.time.wait(2000)
                            app_state = STATE_MENU

            # Rendering continuo
            view.draw(engine.get_board_matrix(), controller.stats)


if __name__ == "__main__":
    main()