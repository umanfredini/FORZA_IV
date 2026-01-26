import pygame


class GameView:
    """
    * Gestisce il rendering grafico.
    * Include ora la visualizzazione numerica della valutazione Minimax.
    """

    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.ui_height = 100
        self.sq_size = int(self.width / 7)
        self.radius = int(self.sq_size / 2 - 8)

        # --- Colori ---
        self.COLOR_BG = (30, 30, 30)
        self.COLOR_BOARD = (25, 60, 150)
        self.COLOR_P1 = (220, 50, 50)  # Rosso
        self.COLOR_P2 = (240, 200, 40)  # Giallo
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_EVAL_NEUTRAL = (200, 200, 200)  # Grigio per parità

        # --- Fonts ---
        self.font_main = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_score = pygame.font.SysFont("monospace", 20)
        self.font_eval = pygame.font.SysFont("monospace", 28, bold=True)  # Font più grande per l'Eval

    def draw(self, board_matrix, stats):
        self.screen.fill(self.COLOR_BG)

        # ---------------------------------------------------------
        # 1. UI SINISTRA E DESTRA (Punteggi Giocatori)
        # ---------------------------------------------------------

        # P1 (Sinistra)
        p1_title = self.font_score.render(f"P1 (RED)", True, self.COLOR_P1)
        p1_stats = self.font_score.render(f"Wins: {stats['wins_p1']} | Moves: {stats['moves_p1']}", True,
                                          self.COLOR_TEXT)
        self.screen.blit(p1_title, (20, 20))
        self.screen.blit(p1_stats, (20, 50))

        # P2 (Destra)
        p2_title = self.font_score.render(f"BOT (YEL)", True, self.COLOR_P2)
        p2_stats = self.font_score.render(f"Wins: {stats['wins_p2']} | Moves: {stats['moves_p2']}", True,
                                          self.COLOR_TEXT)

        # Allineamento a destra
        self.screen.blit(p2_title, (self.width - p2_title.get_width() - 20, 20))
        self.screen.blit(p2_stats, (self.width - p2_stats.get_width() - 20, 50))

        # ---------------------------------------------------------
        # 2. UI CENTRALE (Valutazione Numerica AI)
        # ---------------------------------------------------------

        # Recuperiamo il valore (default a 0 se non esiste)
        score = stats.get('ai_eval', 0)

        # Determiniamo testo e colore
        if score > 10000:
            eval_text = "MATE (BOT)"
            color_eval = self.COLOR_P2
        elif score < -10000:
            eval_text = "MATE (P1)"
            color_eval = self.COLOR_P1
        else:
            # Aggiungiamo il "+" se positivo per chiarezza
            sign = "+" if score > 0 else ""
            eval_text = f"EVAL: {sign}{score}"

            if score > 20:
                color_eval = self.COLOR_P2  # Bot sta vincendo
            elif score < -20:
                color_eval = self.COLOR_P1  # Umano sta vincendo
            else:
                color_eval = self.COLOR_EVAL_NEUTRAL  # Equilibrato

        # Rendering del testo centrale
        eval_surface = self.font_eval.render(eval_text, True, color_eval)

        # Posizionamento esatto al centro della barra superiore
        center_x = (self.width // 2) - (eval_surface.get_width() // 2)
        self.screen.blit(eval_surface, (center_x, 35))  # 35px dall'alto

        # ---------------------------------------------------------
        # 3. DISEGNO SCACCHIERA
        # ---------------------------------------------------------
        for c in range(7):
            for r in range(6):
                rect_x = c * self.sq_size
                rect_y = r * self.sq_size + self.ui_height

                pygame.draw.rect(self.screen, self.COLOR_BOARD, (rect_x, rect_y, self.sq_size, self.sq_size))

                cell = board_matrix[r][c]
                color = (15, 15, 15)
                if cell == 1:
                    color = self.COLOR_P1
                elif cell == 2:
                    color = self.COLOR_P2

                pygame.draw.circle(self.screen, color, (rect_x + self.sq_size // 2, rect_y + self.sq_size // 2),
                                   self.radius)

        pygame.display.update()