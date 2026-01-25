import pygame


class GameView:
    """
    * Gestisce il rendering grafico avanzato e l'interfaccia utente (UI).
    """

    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        # Riserviamo i primi 100px in alto per le statistiche
        self.ui_height = 100
        self.sq_size = int(self.width / 7)
        self.radius = int(self.sq_size / 2 - 8)

        # Palette Colori Modern
        self.COLOR_BG = (30, 30, 30)
        self.COLOR_BOARD = (25, 60, 150)
        self.COLOR_EMPTY = (15, 15, 15)
        self.COLOR_P1 = (220, 50, 50)  # Rosso
        self.COLOR_P2 = (240, 200, 40)  # Giallo
        self.COLOR_TEXT = (255, 255, 255)

        self.font_main = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_score = pygame.font.SysFont("monospace", 20)

    def draw(self, board, turn, stats):
        """
        * Disegna la scacchiera e la barra delle statistiche.
        * * @param stats Dizionario con 'wins_p1', 'wins_p2', 'moves_p1', 'moves_p2'
        """
        self.screen.fill(self.COLOR_BG)

        # --- DISEGNO UI (Barra superiore) ---
        # Giocatore 1
        p1_txt = self.font_main.render(f"P1 (RED)", True, self.COLOR_P1)
        p1_score = self.font_score.render(f"Wins: {stats['wins_p1']} | Moves: {stats['moves_p1']}", True,
                                          self.COLOR_TEXT)
        self.screen.blit(p1_txt, (20, 15))
        self.screen.blit(p1_score, (20, 45))

        # Giocatore 2
        p2_txt = self.font_main.render(f"P2 (YELLOW)", True, self.COLOR_P2)
        p2_score = self.font_score.render(f"Wins: {stats['wins_p2']} | Moves: {stats['moves_p2']}", True,
                                          self.COLOR_TEXT)
        # Allineamento a destra
        self.screen.blit(p2_txt, (self.width - p2_txt.get_width() - 20, 15))
        self.screen.blit(p2_score, (self.width - p2_score.get_width() - 20, 45))

        # --- DISEGNO SCACCHIERA ---
        for c in range(7):
            for r in range(6):
                rect_x = c * self.sq_size
                # La scacchiera inizia dopo la UI height
                rect_y = (r * self.sq_size) + self.ui_height

                # Corpo scacchiera con angoli leggermente smussati
                pygame.draw.rect(self.screen, self.COLOR_BOARD, (rect_x, rect_y, self.sq_size, self.sq_size))

                # Centro del foro
                center_x = int(rect_x + self.sq_size / 2)
                center_y = int(rect_y + self.sq_size / 2)

                # Colore in base alla matrice (invertendo le righe per la gravità visiva)
                # board[r][c] dove r=0 è il fondo se invertito correttamente nell'engine
                cell_val = board[r][c]
                color = self.COLOR_EMPTY
                if cell_val == 1:
                    color = self.COLOR_P1
                elif cell_val == 2:
                    color = self.COLOR_P2

                # Effetto ombra interna per il foro
                pygame.draw.circle(self.screen, (0, 0, 0, 50), (center_x, center_y), self.radius + 2)
                pygame.draw.circle(self.screen, color, (center_x, center_y), self.radius)

        pygame.display.update()