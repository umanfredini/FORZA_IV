import pygame


class GameView:
    """
    * Gestisce il rendering grafico.
    * Include ora la visualizzazione numerica e il MODAL di Game Over.
    """

    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        # Dimensioni della griglia
        self.ui_height = 100
        self.sq_size = int(self.width / 7)
        self.radius = int(self.sq_size / 2 - 8)

        # --- Colori ---
        self.COLOR_BG = (30, 30, 30)
        self.COLOR_BOARD = (25, 60, 150)
        self.COLOR_P1 = (220, 50, 50)  # Rosso
        self.COLOR_P2 = (240, 200, 40)  # Giallo
        self.COLOR_TEXT = (255, 255, 255)
        self.COLOR_EVAL_NEUTRAL = (200, 200, 200)

        # --- Fonts ---
        self.font_main = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_score = pygame.font.SysFont("monospace", 20)
        self.font_eval = pygame.font.SysFont("monospace", 28, bold=True)

        # --- NUOVI FONT PER IL MODAL (Game Over) ---
        self.font_modal_title = pygame.font.SysFont("Arial", 50, bold=True)
        self.font_modal_btn = pygame.font.SysFont("Arial", 30, bold=True)

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
        self.screen.blit(p2_title, (self.width - p2_title.get_width() - 20, 20))
        self.screen.blit(p2_stats, (self.width - p2_stats.get_width() - 20, 50))

        # ---------------------------------------------------------
        # 2. UI CENTRALE (Valutazione Numerica AI)
        # ---------------------------------------------------------
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
                color_eval = self.COLOR_EVAL_NEUTRAL

        eval_surface = self.font_eval.render(eval_text, True, color_eval)
        center_x = (self.width // 2) - (eval_surface.get_width() // 2)
        self.screen.blit(eval_surface, (center_x, 35))

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

    # ---------------------------------------------------------
    # 4. NUOVO METODO: MODAL GAME OVER
    # ---------------------------------------------------------
    def draw_game_over_modal(self, winner_text):
        """
        Disegna un overlay semi-trasparente con i pulsanti 'Rigioca' e 'Menu'.
        Ritorna i rect dei pulsanti per gestire i click nel main.
        """
        # 1. Overlay Scuro (Dimming)
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(180)  # Trasparenza (0-255)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # 2. Box Centrale
        box_w, box_h = 400, 280
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2

        # Disegno Box
        pygame.draw.rect(self.screen, (40, 40, 50), (box_x, box_y, box_w, box_h), border_radius=20)
        pygame.draw.rect(self.screen, (255, 255, 255), (box_x, box_y, box_w, box_h), 2, border_radius=20)

        # 3. Testo Vittoria
        # Colore dinamico in base al testo
        text_color = self.COLOR_TEXT
        if "P1" in winner_text or "GIOCATORE 1" in winner_text: text_color = self.COLOR_P1
        if "BOT" in winner_text or "GIOCATORE 2" in winner_text: text_color = self.COLOR_P2

        title_surf = self.font_modal_title.render(winner_text, True, text_color)
        self.screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, box_y + 30))

        # 4. Pulsanti
        btn_w, btn_h = 280, 50
        btn_x = (self.width - btn_w) // 2

        # Pulsante RETRY
        retry_y = box_y + 110
        rect_retry = pygame.Rect(btn_x, retry_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (50, 180, 50), rect_retry, border_radius=10)  # Verde
        retry_text = self.font_modal_btn.render("GIOCA ANCORA", True, (255, 255, 255))
        self.screen.blit(retry_text, (rect_retry.centerx - retry_text.get_width() // 2,
                                      rect_retry.centery - retry_text.get_height() // 2))

        # Pulsante MENU
        menu_y = box_y + 180
        rect_menu = pygame.Rect(btn_x, menu_y, btn_w, btn_h)
        pygame.draw.rect(self.screen, (180, 50, 50), rect_menu, border_radius=10)  # Rosso
        menu_text = self.font_modal_btn.render("TORNA AL MENU", True, (255, 255, 255))
        self.screen.blit(menu_text, (rect_menu.centerx - menu_text.get_width() // 2,
                                     rect_menu.centery - menu_text.get_height() // 2))

        pygame.display.update()

        # IMPORTANTE: Ritorniamo i rettangoli affinché il main sappia dove clicchiamo
        return rect_retry, rect_menu