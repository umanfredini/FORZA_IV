import pygame
import sys
from board.engine import GameEngine
from board.interface import GameView
from board.controller import GameController
from ai.minmax import MinimaxBot

# --- COSTANTI DI STATO ---
STATE_MENU = 0
STATE_GAME = 1


def draw_menu(screen, font):
    """
    * Disegna il menu principale.
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
    * Funzione principale con gestione stati.
    """
    pygame.init()
    screen = pygame.display.set_mode((700, 700))
    pygame.display.set_caption("Forza 4 - AI & PvP")

    font = pygame.font.SysFont("Arial", 40, bold=True)

    engine = GameEngine()
    view = GameView(screen)
    controller = GameController(engine, view)

    # Inizializzazione Bot
    bot = MinimaxBot(depth=4)  # Depth 4 è veloce e abbastanza intelligente

    app_state = STATE_MENU
    game_mode = "PVP"  # "PVP" o "PVE"

    while True:
        # --- GESTIONE MENU ---
        if app_state == STATE_MENU:
            draw_menu(screen, font)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
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

        # --- GESTIONE GIOCO ---
        elif app_state == STATE_GAME:

            # Se è PVE e tocca al Bot (Turno 1)
            if game_mode == "PVE" and controller.turn == 1 and not controller.game_over:
                pygame.time.wait(500)  # Piccola pausa per simulare "pensiero" ed evitare mosse istantanee

                col = bot.get_best_move(engine)

                if col is not None:
                    # Simuliamo il click per il controller o chiamiamo direttamente la logica
                    # Qui chiamiamo la logica diretta simulando coordinate o metodo dedicato
                    # Per semplicità, usiamo una chiamata diretta (dobbiamo adattare process_turn o crearne uno nuovo)
                    # Adattiamo process_turn per accettare colonna esplicita o simuliamo posx

                    simulated_x = col * view.sq_size + 10
                    win, player = controller.process_turn(simulated_x)
                    view.draw(engine.get_board_matrix(), controller.stats)

                    if win:
                        print(f"Il Bot ha vinto!")
                        pygame.time.wait(2000)
                        app_state = STATE_MENU  # Torna al menu

            # Eventi standard (Umano)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        # Se è PVE e tocca al bot, ignora i click dell'umano
                        if game_mode == "PVE" and controller.turn == 1:
                            continue

                        win, player = controller.process_turn(event.pos[0])
                        view.draw(engine.get_board_matrix(), controller.stats)

                        if win:
                            winner_name = "Giocatore 1" if player == 0 else (
                                "Giocatore 2" if game_mode == "PVP" else "Bot")
                            print(f"{winner_name} ha vinto!")
                            pygame.time.wait(2000)
                            app_state = STATE_MENU

            # Rendering continuo se nessuno muove
            view.draw(engine.get_board_matrix(), controller.stats)
            pygame.display.update()


if __name__ == "__main__":
    main()