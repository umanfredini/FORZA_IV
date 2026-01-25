import pygame
import sys
from board.engine import GameEngine
from board.interface import GameView
from board.controller import GameController


def main():
    pygame.init()
    # 700px larghezza, 700px altezza (100 UI + 600 Board)
    screen = pygame.display.set_mode((700, 700))
    pygame.display.set_caption("Connect4 Adaptive - Stats Edition")

    engine = GameEngine()
    view = GameView(screen)
    controller = GameController(engine, view)

    while True:  # Loop infinito per permettere più partite
        game_over = False
        engine.reset()  # Implementa questo metodo nell'engine (azzera bitboards)
        controller.reset_game()

        view.draw(engine.get_board_matrix(), controller.turn, controller.stats)

        while not game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    col, state, win, player = controller.process_turn(event.pos[0])

                    if col is not None:
                        view.draw(engine.get_board_matrix(), controller.turn, controller.stats)

                        if win:
                            game_over = True
                            pygame.time.wait(2000)


if __name__ == "__main__":
    main()