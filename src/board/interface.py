import pygame


class GameView:
    """
    * Gestisce il rendering grafico.
    * Include ora la SIDEBAR DI ANALISI (1000x700).
    """

    def __init__(self, screen):
        self.screen = screen
        self.total_width = screen.get_width()
        self.height = screen.get_height()

        # --- LAYOUT ---
        # La scacchiera occupa sempre i primi 700px
        self.board_width = 700
        self.sidebar_width = self.total_width - self.board_width

        # Dimensioni della griglia (basate sulla board_width, non total_width)
        self.ui_height = 100
        self.sq_size = int(self.board_width / 7)
        self.radius = int(self.sq_size / 2 - 8)

        # --- Colori ---
        self.COLOR_BG = (30, 30, 30)
        self.COLOR_SIDEBAR = (20, 20, 25)  # Sfondo scuro per la sidebar
        self.COLOR_BOARD = (25, 60, 150)
        self.COLOR_P1 = (220, 50, 50)
        self.COLOR_P2 = (240, 200, 40)
        self.COLOR_TEXT = (255, 255, 255)

        # Colori Bias
        self.COLOR_BIAS_DIAG = (0, 255, 255)  # Ciano (Debolezza diagonale)
        self.COLOR_BIAS_VERT = (50, 255, 50)  # Verde (Debolezza verticale)
        self.COLOR_BIAS_WARN = (255, 50, 50)  # Rosso (Errori fatali)

        # --- Fonts ---
        self.font_main = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_score = pygame.font.SysFont("monospace", 20)
        self.font_eval = pygame.font.SysFont("monospace", 28, bold=True)
        self.font_sidebar_title = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_sidebar_text = pygame.font.SysFont("Consolas", 14)

        # Fonts Modal
        self.font_modal_title = pygame.font.SysFont("Arial", 50, bold=True)
        self.font_modal_btn = pygame.font.SysFont("Arial", 30, bold=True)

    def draw(self, board_matrix, stats, profiler=None):
        """
        Renderizza tutto. Ora accetta opzionalmente 'profiler' per disegnare la sidebar.
        """
        # Pulizia sfondo
        self.screen.fill(self.COLOR_BG)

        # Disegna Scacchiera (Parte Sinistra)
        self._draw_board_area(board_matrix, stats)

        # Disegna Sidebar (Parte Destra) se il profiler è disponibile
        if self.total_width >= 1000 and profiler:
            self._draw_sidebar(profiler)

        pygame.display.update()

    def _draw_board_area(self, board_matrix, stats):
        # 1. UI Punteggi
        p1_title = self.font_score.render(f"P1 (RED)", True, self.COLOR_P1)
        p1_stats = self.font_score.render(f"Wins: {stats['wins_p1']} | Moves: {stats['moves_p1']}", True,
                                          self.COLOR_TEXT)
        self.screen.blit(p1_title, (20, 20))
        self.screen.blit(p1_stats, (20, 50))

        p2_title = self.font_score.render(f"BOT (YEL)", True, self.COLOR_P2)
        p2_stats = self.font_score.render(f"Wins: {stats['wins_p2']} | Moves: {stats['moves_p2']}", True,
                                          self.COLOR_TEXT)
        # Allineato al bordo destro della SCACCHIERA (700px), non della finestra
        right_limit = self.board_width
        self.screen.blit(p2_title, (right_limit - p2_title.get_width() - 20, 20))
        self.screen.blit(p2_stats, (right_limit - p2_stats.get_width() - 20, 50))

        # 2. UI Eval
        score = stats.get('ai_eval', 0)
        if score > 10000:
            eval_text = "MATE (BOT)"
            color_eval = self.COLOR_P2
        elif score < -10000:
            eval_text = "MATE (P1)"
            color_eval = self.COLOR_P1
        else:
            sign = "+" if score > 0 else ""
            eval_text = f"EVAL: {sign}{score}"
            if score > 20:
                color_eval = self.COLOR_P2
            elif score < -20:
                color_eval = self.COLOR_P1
            else:
                color_eval = (200, 200, 200)

        eval_surface = self.font_eval.render(eval_text, True, color_eval)
        center_x = (self.board_width // 2) - (eval_surface.get_width() // 2)
        self.screen.blit(eval_surface, (center_x, 35))

        # 3. Griglia
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

    def _draw_sidebar(self, profiler):
        """ Disegna i grafici dei Bias """
        # Sfondo Sidebar
        sidebar_rect = pygame.Rect(self.board_width, 0, self.sidebar_width, self.height)
        pygame.draw.rect(self.screen, self.COLOR_SIDEBAR, sidebar_rect)
        pygame.draw.line(self.screen, (100, 100, 100), (self.board_width, 0), (self.board_width, self.height), 2)

        start_x = self.board_width + 20
        y = 30

        # Titolo
        title = self.font_sidebar_title.render("NEURAL PROFILER", True, (0, 255, 200))
        self.screen.blit(title, (start_x, y))
        y += 50

        # Recuperiamo i Bias
        biases = profiler.get_adaptive_weights()

        # Definizione barre da disegnare
        # (Label, Chiave Dizionario, Colore)
        bars = [
            ("DIAGONAL WEAKNESS", "diagonal_weakness", self.COLOR_BIAS_DIAG),
            ("VERTICAL WEAKNESS", "vertical_weakness", self.COLOR_BIAS_VERT),
            ("HORIZ. WEAKNESS", "horizontal_weakness", (255, 165, 0)),
            ("THREAT BLINDNESS", "threat_underestimation", (255, 100, 200)),
        ]

        for label, key, color in bars:
            val = biases.get(key, 1.0)
            # Normalizziamo: 1.0 (Min) -> 0px, 3.0 (Max) -> Full Width
            # Lunghezza massima barra = 200px
            bar_len = min(200, int((val - 1.0) * 100))
            if bar_len < 5: bar_len = 5  # Minimo visibile

            # Testo Label
            lbl_surf = self.font_sidebar_text.render(f"{label}: {val:.2f}", True, (200, 200, 200))
            self.screen.blit(lbl_surf, (start_x, y))
            y += 20

            # Disegno Barra
            # Sfondo barra (grigio scuro)
            pygame.draw.rect(self.screen, (50, 50, 50), (start_x, y, 200, 15))
            # Barra Valore
            pygame.draw.rect(self.screen, color, (start_x, y, bar_len, 15))
            y += 40  # Spazio per prossima barra

        # Statistiche Errori
        y += 20
        stats = profiler.stats
        err_txt = self.font_sidebar_title.render(f"FATAL ERRORS: {stats['fatal_errors']}", True, self.COLOR_BIAS_WARN)
        self.screen.blit(err_txt, (start_x, y))

        # Icona Lampeggiante per Trappola (Simulata)
        # Se c'è un bias diagonale alto, mostriamo un avviso
        if biases.get("diagonal_weakness", 1.0) > 1.5:
            y += 60
            warn_rect = pygame.Rect(start_x, y, 220, 40)
            pygame.draw.rect(self.screen, (100, 0, 0), warn_rect, border_radius=5)
            warn_txt = self.font_sidebar_title.render("! DIAG VULNERABLE !", True, (255, 255, 255))
            self.screen.blit(warn_txt, (start_x + 10, y + 8))

    def draw_game_over_modal(self, winner_text):
        """ (Invariato rispetto a prima, ma centratura aggiornata su total_width) """
        overlay = pygame.Surface((self.total_width, self.height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        box_w, box_h = 400, 280
        # Centrato rispetto alla finestra totale
        box_x = (self.total_width - box_w) // 2
        box_y = (self.height - box_h) // 2

        pygame.draw.rect(self.screen, (40, 40, 50), (box_x, box_y, box_w, box_h), border_radius=20)
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_w, box_h), 2, border_radius=20)

        text_color = self.COLOR_TEXT
        if "P1" in winner_text or "GIOCATORE 1" in winner_text: text_color = self.COLOR_P1
        if "BOT" in winner_text or "GIOCATORE 2" in winner_text: text_color = self.COLOR_P2

        title_surf = self.font_modal_title.render(winner_text, True, text_color)
        self.screen.blit(title_surf, (self.total_width // 2 - title_surf.get_width() // 2, box_y + 30))

        btn_w, btn_h = 280, 50
        btn_x = (self.total_width - btn_w) // 2

        retry_y = box_y + 110
        rect_retry = pygame.Rect(btn_x, retry_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (50, 180, 50), rect_retry, border_radius=10)
        retry_text = self.font_modal_btn.render("GIOCA ANCORA", True, (255, 255, 255))
        self.screen.blit(retry_text, (rect_retry.centerx - retry_text.get_width() // 2,
                                      rect_retry.centery - retry_text.get_height() // 2))

        menu_y = box_y + 180
        rect_menu = pygame.Rect(btn_x, menu_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (180, 50, 50), rect_menu, border_radius=10)
        menu_text = self.font_modal_btn.render("TORNA AL MENU", True, (255, 255, 255))
        self.screen.blit(menu_text, (rect_menu.centerx - menu_text.get_width() // 2,
                                     rect_menu.centery - menu_text.get_height() // 2))

        pygame.display.update()
        return rect_retry, rect_menu