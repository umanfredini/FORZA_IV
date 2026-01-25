import pygame


class GameView:
    def __init__(self, screen):
        self.screen = screen
        # Calcoliamo la dimensione dinamica in base alla larghezza della finestra
        self.width = screen.get_width()
        self.height = screen.get_height()
        # 7 colonne: dividiamo la larghezza per 7 per trovare la dimensione del quadrato
        self.sq_size = int(self.width / 7)
        # Raggio della pedina (un po' più piccolo della casella)
        self.radius = int(self.sq_size / 2 - 5)

        # Colori
        self.BLUE = (0, 0, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)

    def draw(self, board, turn):
        # Disegniamo prima la griglia blu
        for c in range(7):
            for r in range(6):
                # Rettangolo blu (struttura)
                rect_x = c * self.sq_size
                # Aggiungiamo un offset in alto (sq_size) se vogliamo una barra del menu,
                # altrimenti partiamo da 0. Nel tuo caso partiamo da 0 se la finestra è quadrata.
                rect_y = r * self.sq_size

                pygame.draw.rect(self.screen, self.BLUE, (rect_x, rect_y, self.sq_size, self.sq_size))

                # Cerchio (vuoto o pieno)
                # Calcolo centro del cerchio
                center_x = int(c * self.sq_size + self.sq_size / 2)
                center_y = int(r * self.sq_size + self.sq_size / 2)

                if board[r][c] == 0:
                    pygame.draw.circle(self.screen, self.BLACK, (center_x, center_y), self.radius)
                elif board[r][c] == 1:
                    pygame.draw.circle(self.screen, self.RED, (center_x, center_y), self.radius)
                elif board[r][c] == 2:
                    pygame.draw.circle(self.screen, self.YELLOW, (center_x, center_y), self.radius)

        pygame.display.update()