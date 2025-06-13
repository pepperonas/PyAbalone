import pygame
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set, Dict
import sys
import random

# Konstanten
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
HEX_SIZE = 35
FPS = 60

# Basis Enums (müssen vor Settings definiert werden)
class GameState(Enum):
	MAIN_MENU = 'main_menu'
	SETTINGS = 'settings'
	GAME_PVP = 'game_pvp'
	GAME_AI = 'game_ai'
	GAME_2V2 = 'game_2v2'

class Theme(Enum):
	CLASSIC = 'classic'
	DARK = 'dark'
	OCEAN = 'ocean'
	FOREST = 'forest'

class AIDifficulty(Enum):
	EASY = 1
	MEDIUM = 2
	HARD = 3

# Einstellungen und Konfiguration
class Settings:
	def __init__(self):
		self.current_theme = Theme.CLASSIC
		self.sound_enabled = True
		self.ai_difficulty = AIDifficulty.MEDIUM
		
	def get_theme_colors(self):
		themes = {
			Theme.CLASSIC: {
				'background': (15, 20, 35),
				'board_start': (45, 55, 75),
				'board_end': (65, 75, 95),
				'board_border': (25, 35, 55),
				'board_highlight': (85, 95, 115),
				'highlight': (102, 187, 106),
				'button_start': (63, 81, 181),
				'button_end': (48, 63, 159)
			},
			Theme.DARK: {
				'background': (10, 10, 15),
				'board_start': (30, 30, 40),
				'board_end': (50, 50, 60),
				'board_border': (20, 20, 30),
				'board_highlight': (70, 70, 80),
				'highlight': (150, 150, 160),
				'button_start': (40, 40, 50),
				'button_end': (30, 30, 40)
			},
			Theme.OCEAN: {
				'background': (10, 25, 40),
				'board_start': (20, 60, 100),
				'board_end': (40, 80, 120),
				'board_border': (15, 45, 75),
				'board_highlight': (60, 120, 160),
				'highlight': (100, 200, 255),
				'button_start': (30, 144, 255),
				'button_end': (0, 100, 200)
			},
			Theme.FOREST: {
				'background': (20, 30, 20),
				'board_start': (40, 70, 40),
				'board_end': (60, 90, 60),
				'board_border': (25, 45, 25),
				'board_highlight': (80, 120, 80),
				'highlight': (144, 238, 144),
				'button_start': (34, 139, 34),
				'button_end': (0, 100, 0)
			}
		}
		return themes[self.current_theme]

# Globale Einstellungen
SETTINGS = Settings()

class AbaloneAI:
	"""KI-Gegner für Abalone mit verschiedenen Schwierigkeitsgraden"""
	
	def __init__(self, difficulty=AIDifficulty.MEDIUM):
		self.difficulty = difficulty
		self.max_depth = self._get_max_depth()
		self.thinking_time = 0.1  # Reduzierte Denkzeit für schnellere KI
		
	def _get_max_depth(self):
		"""Bestimmt die Suchtiefe basierend auf Schwierigkeit"""
		if self.difficulty == AIDifficulty.EASY:
			return 2
		elif self.difficulty == AIDifficulty.MEDIUM:
			return 3
		else:  # HARD
			return 4
	
	def get_best_move(self, game, player):
		"""Findet den besten Zug für den gegebenen Spieler"""
		import time
		start_time = time.time()
		
		# Alle möglichen Züge generieren
		all_moves = self._generate_all_moves(game, player)
		
		if not all_moves:
			return None
		
		# Bei einfacher Schwierigkeit: zufälliger Zug mit geringer Intelligenz
		if self.difficulty == AIDifficulty.EASY:
			# 70% zufällig, 30% intelligent
			if random.random() < 0.7:
				return random.choice(all_moves)
		
		# Minimax mit Alpha-Beta-Pruning
		best_move = None
		best_score = float('-inf')
		alpha = float('-inf')
		beta = float('inf')
		
		for move in all_moves:
			# Simuliere den Zug
			game_copy = self._copy_game_state(game)
			self._execute_move(game_copy, move, player)
			
			# Bewerte den resultierenden Zustand
			score = self._minimax(game_copy, self.max_depth - 1, alpha, beta, False, player)
			
			if score > best_score:
				best_score = score
				best_move = move
				
			alpha = max(alpha, score)
			if beta <= alpha:
				break  # Alpha-Beta-Pruning
		
		# Mindest-Denkzeit einhalten
		elapsed = time.time() - start_time
		if elapsed < self.thinking_time:
			time.sleep(self.thinking_time - elapsed)
		
		return best_move
	
	def _generate_all_moves(self, game, player):
		"""Generiert alle möglichen Züge für einen Spieler"""
		moves = []
		
		# Finde alle Kugeln des Spielers
		player_marbles = []
		for hex_pos, marble_player in game.board.items():
			if marble_player == player:
				player_marbles.append(hex_pos)
		
		# Generiere Züge für einzelne Kugeln
		for marble in player_marbles:
			valid_moves = game.calculate_valid_moves([marble])
			for target in valid_moves:
				moves.append(([marble], target))
		
		# Generiere Züge für 2er-Kombinationen
		for i in range(len(player_marbles)):
			for j in range(i + 1, len(player_marbles)):
				marble_combo = [player_marbles[i], player_marbles[j]]
				if game._are_marbles_in_line(marble_combo):
					valid_moves = game.calculate_valid_moves(marble_combo)
					for target in valid_moves:
						moves.append((marble_combo, target))
		
		# Generiere Züge für 3er-Kombinationen
		for i in range(len(player_marbles)):
			for j in range(i + 1, len(player_marbles)):
				for k in range(j + 1, len(player_marbles)):
					marble_combo = [player_marbles[i], player_marbles[j], player_marbles[k]]
					if game._are_marbles_in_line(marble_combo):
						valid_moves = game.calculate_valid_moves(marble_combo)
						for target in valid_moves:
							moves.append((marble_combo, target))
		
		return moves
	
	def _minimax(self, game, depth, alpha, beta, maximizing_player, ai_player):
		"""Minimax-Algorithmus mit Alpha-Beta-Pruning"""
		# Terminalbedingungen
		winner = game.check_winner()
		if winner == ai_player:
			return 1000 + depth  # Bevorzuge schnelle Siege
		elif winner is not None:
			return -1000 - depth  # Vermeide schnelle Niederlagen
		elif depth == 0:
			return self._evaluate_position(game, ai_player)
		
		current_player = ai_player if maximizing_player else (Player.WHITE if ai_player == Player.BLACK else Player.BLACK)
		moves = self._generate_all_moves(game, current_player)
		
		if not moves:
			return self._evaluate_position(game, ai_player)
		
		if maximizing_player:
			max_eval = float('-inf')
			for move in moves:
				game_copy = self._copy_game_state(game)
				self._execute_move(game_copy, move, current_player)
				eval_score = self._minimax(game_copy, depth - 1, alpha, beta, False, ai_player)
				max_eval = max(max_eval, eval_score)
				alpha = max(alpha, eval_score)
				if beta <= alpha:
					break
			return max_eval
		else:
			min_eval = float('inf')
			for move in moves:
				game_copy = self._copy_game_state(game)
				self._execute_move(game_copy, move, current_player)
				eval_score = self._minimax(game_copy, depth - 1, alpha, beta, True, ai_player)
				min_eval = min(min_eval, eval_score)
				beta = min(beta, eval_score)
				if beta <= alpha:
					break
			return min_eval
	
	def _evaluate_position(self, game, ai_player):
		"""Bewertet eine Spielposition aus Sicht der KI"""
		opponent = Player.WHITE if ai_player == Player.BLACK else Player.BLACK
		
		score = 0
		
		# 1. Scores (wichtigster Faktor)
		score += (game.scores[ai_player] - game.scores[opponent]) * 200
		
		# 2. Zentrale Kontrolle
		center_positions = [Hex(0, 0), Hex(1, 0), Hex(-1, 0), Hex(0, 1), Hex(0, -1), Hex(1, -1), Hex(-1, 1)]
		ai_center_control = sum(1 for pos in center_positions if game.board.get(pos) == ai_player)
		opponent_center_control = sum(1 for pos in center_positions if game.board.get(pos) == opponent)
		score += (ai_center_control - opponent_center_control) * 10
		
		# 3. Zusammenhalt der Kugeln (gruppierte Kugeln sind stärker)
		ai_cohesion = self._calculate_cohesion(game, ai_player)
		opponent_cohesion = self._calculate_cohesion(game, opponent)
		score += (ai_cohesion - opponent_cohesion) * 5
		
		# 4. Randnähe (Kugeln am Rand sind gefährdeter)
		ai_edge_penalty = self._calculate_edge_penalty(game, ai_player)
		opponent_edge_penalty = self._calculate_edge_penalty(game, opponent)
		score += (opponent_edge_penalty - ai_edge_penalty) * 3
		
		# 5. Anzahl möglicher Züge (Mobilität)
		ai_mobility = len(self._generate_all_moves(game, ai_player))
		opponent_mobility = len(self._generate_all_moves(game, opponent))
		score += (ai_mobility - opponent_mobility) * 1
		
		return score
	
	def _calculate_cohesion(self, game, player):
		"""Berechnet den Zusammenhalt der Kugeln eines Spielers"""
		player_marbles = [pos for pos, p in game.board.items() if p == player]
		cohesion = 0
		
		for marble in player_marbles:
			neighbors = 0
			for direction in range(6):
				neighbor_pos = marble.neighbor(direction)
				if game.board.get(neighbor_pos) == player:
					neighbors += 1
			cohesion += neighbors
		
		return cohesion
	
	def _calculate_edge_penalty(self, game, player):
		"""Berechnet die Strafe für Kugeln am Randbereich"""
		penalty = 0
		edge_positions = []
		
		# Bestimme Randpositionen (Positionen mit weniger als 6 Nachbarn auf dem Brett)
		for pos in game.board:
			neighbor_count = 0
			for direction in range(6):
				neighbor = pos.neighbor(direction)
				if neighbor in game.board:
					neighbor_count += 1
			if neighbor_count < 6:
				edge_positions.append(pos)
		
		# Zähle eigene Kugeln am Rand
		for pos in edge_positions:
			if game.board[pos] == player:
				penalty += 1
		
		return penalty
	
	def _copy_game_state(self, game):
		"""Erstellt eine Kopie des Spielzustands"""
		new_game = AbaloneGame()
		new_game.board = game.board.copy()
		new_game.current_player = game.current_player
		new_game.scores = game.scores.copy()
		return new_game
	
	def _execute_move(self, game, move, player):
		"""Führt einen Zug in einer Spielkopie aus"""
		selected_marbles, target = move
		game.current_player = player
		game.make_move(selected_marbles, target)

class Menu:
	"""Basis-Klasse für alle Menüs"""
	def __init__(self, screen, font, large_font):
		self.screen = screen
		self.font = font
		self.large_font = large_font
		self.buttons = []
		
	def add_button(self, x, y, width, height, text, action):
		button = Button(x, y, width, height, text, self.font)
		button.action = action
		self.buttons.append(button)
		return button
		
	def handle_event(self, event):
		for button in self.buttons:
			if button.handle_event(event):
				return button.action
		return None
		
	def draw_background(self):
		colors = SETTINGS.get_theme_colors()
		self.screen.fill(colors['background'])
		
	def draw_title(self, title, y_pos=100):
		colors = SETTINGS.get_theme_colors()
		title_shadow = self.large_font.render(title, True, (0, 0, 0))
		title_surface = self.large_font.render(title, True, TEXT_COLOR)
		title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, y_pos))
		shadow_rect = title_rect.copy()
		shadow_rect.x += 3
		shadow_rect.y += 3
		self.screen.blit(title_shadow, shadow_rect)
		self.screen.blit(title_surface, title_rect)

class MainMenu(Menu):
	"""Hauptmenü des Spiels"""
	def __init__(self, screen, font, large_font):
		super().__init__(screen, font, large_font)
		self.setup_buttons()
		
	def setup_buttons(self):
		center_x = WINDOW_WIDTH // 2
		button_width = 300
		button_height = 60
		start_y = 250
		spacing = 80
		
		self.add_button(center_x - button_width//2, start_y, button_width, button_height, 
						"Spiel starten", "start_game")
		self.add_button(center_x - button_width//2, start_y + spacing, button_width, button_height, 
						"KI Gegner", "ai_game")
		self.add_button(center_x - button_width//2, start_y + spacing*2, button_width, button_height, 
						"2 vs. 2", "team_game")
		self.add_button(center_x - button_width//2, start_y + spacing*3, button_width, button_height, 
						"Einstellungen", "settings")
		self.add_button(center_x - button_width//2, start_y + spacing*4, button_width, button_height, 
						"Beenden", "quit")
	
	def draw(self):
		self.draw_background()
		self.draw_title("Abalone")
		
		for button in self.buttons:
			button.draw(self.screen)

class SettingsMenu(Menu):
	"""Einstellungsmenü"""
	def __init__(self, screen, font, large_font):
		super().__init__(screen, font, large_font)
		self.setup_buttons()
		
	def setup_buttons(self):
		center_x = WINDOW_WIDTH // 2
		button_width = 280
		button_height = 45
		left_col_x = center_x - 320
		right_col_x = center_x + 40
		col_width = 280
		
		# Theme-Buttons (linke Spalte)
		theme_start_y = 220
		theme_names = ["Classic", "Dark", "Ocean", "Forest"]
		themes = [Theme.CLASSIC, Theme.DARK, Theme.OCEAN, Theme.FOREST]
		
		for i, (name, theme) in enumerate(zip(theme_names, themes)):
			prefix = "✓ " if SETTINGS.current_theme == theme else "  "
			self.add_button(left_col_x, theme_start_y + i*55, 
							col_width, button_height, f"{prefix}{name}", f"theme_{theme.value}")
		
		# Audio & KI Settings (rechte Spalte)
		audio_start_y = 220
		
		# Sound-Button
		sound_text = "✓ Sound An" if SETTINGS.sound_enabled else "  Sound Aus"
		self.add_button(right_col_x, audio_start_y, 
						col_width, button_height, sound_text, "toggle_sound")
		
		# KI-Schwierigkeit
		ai_levels = ["Leicht", "Mittel", "Schwer"]
		difficulties = [AIDifficulty.EASY, AIDifficulty.MEDIUM, AIDifficulty.HARD]
		
		for i, (name, diff) in enumerate(zip(ai_levels, difficulties)):
			prefix = "✓ " if SETTINGS.ai_difficulty == diff else "  "
			self.add_button(right_col_x, audio_start_y + (i+1)*55, 
							col_width, button_height, f"{prefix}KI {name}", f"ai_{diff.value}")
		
		# Zurück-Button (zentriert unten)
		self.add_button(center_x - 150, 550, 
						300, 50, "Zurück", "back")
	
	def draw(self):
		self.draw_background()
		self.draw_title("Einstellungen")
		
		# Kategorie-Überschriften
		colors = SETTINGS.get_theme_colors()
		
		# Linke Spalte: Themes
		theme_title_shadow = self.font.render("🎨 Themes", True, (0, 0, 0))
		theme_title = self.font.render("🎨 Themes", True, colors['highlight'])
		theme_rect = theme_title.get_rect(center=(WINDOW_WIDTH // 2 - 180, 180))
		theme_shadow_rect = theme_rect.copy()
		theme_shadow_rect.x += 2
		theme_shadow_rect.y += 2
		self.screen.blit(theme_title_shadow, theme_shadow_rect)
		self.screen.blit(theme_title, theme_rect)
		
		# Rechte Spalte: Audio & KI
		settings_title_shadow = self.font.render("⚙️ Audio & KI", True, (0, 0, 0))
		settings_title = self.font.render("⚙️ Audio & KI", True, colors['highlight'])
		settings_rect = settings_title.get_rect(center=(WINDOW_WIDTH // 2 + 180, 180))
		settings_shadow_rect = settings_rect.copy()
		settings_shadow_rect.x += 2
		settings_shadow_rect.y += 2
		self.screen.blit(settings_title_shadow, settings_shadow_rect)
		self.screen.blit(settings_title, settings_rect)
		
		# Vertikale Trennlinie
		line_x = WINDOW_WIDTH // 2
		line_start_y = 200
		line_end_y = 500
		
		# Trennlinie mit Verlauf
		for i in range(line_end_y - line_start_y):
			alpha = 100 - abs(i - (line_end_y - line_start_y) // 2) * 2
			if alpha > 20:
				color = (*colors['board_border'], alpha)
				line_surface = pygame.Surface((2, 1), pygame.SRCALPHA)
				line_surface.fill(color)
				self.screen.blit(line_surface, (line_x - 1, line_start_y + i))
		
		# Horizontale Trennlinien unter Kategorien
		for col_x in [WINDOW_WIDTH // 2 - 180, WINDOW_WIDTH // 2 + 180]:
			line_y = 200
			line_surface = pygame.Surface((280, 2), pygame.SRCALPHA)
			for x in range(280):
				alpha = 80 - abs(x - 140) // 2
				if alpha > 10:
					color = (*colors['board_highlight'], alpha)
					pygame.draw.rect(line_surface, color, (x, 0, 1, 2))
			self.screen.blit(line_surface, (col_x - 140, line_y))
		
		# Buttons zeichnen
		for button in self.buttons:
			button.draw(self.screen)

# Enhanced Color Scheme
BACKGROUND_COLOR = (15, 20, 35)  # Deep navy
BOARD_GRADIENT_START = (45, 55, 75)  # Darker blue-gray
BOARD_GRADIENT_END = (65, 75, 95)  # Lighter blue-gray
BOARD_BORDER_COLOR = (25, 35, 55)  # Dark border
BOARD_HIGHLIGHT_COLOR = (85, 95, 115)  # Light border

HIGHLIGHT_COLOR = (102, 187, 106)  # Material Green 400
VALID_MOVE_COLOR = (102, 187, 106, 120)  # Semi-transparent green
INVALID_MOVE_COLOR = (244, 67, 54, 80)  # Semi-transparent red

# Marble colors with gradients
BLACK_MARBLE_DARK = (20, 20, 25)
BLACK_MARBLE_LIGHT = (45, 45, 55)
BLACK_MARBLE_HIGHLIGHT = (80, 80, 90)

WHITE_MARBLE_DARK = (220, 220, 225)
WHITE_MARBLE_LIGHT = (245, 245, 250)
WHITE_MARBLE_HIGHLIGHT = (255, 255, 255)

# UI colors
SELECTED_GLOW = (255, 193, 7, 150)  # Material Amber with alpha
HOVER_GLOW = (100, 181, 246, 100)  # Material Light Blue with alpha
TEXT_COLOR = (255, 255, 255)
TEXT_SHADOW_COLOR = (0, 0, 0, 100)

# Button colors
BUTTON_GRADIENT_START = (63, 81, 181)
BUTTON_GRADIENT_END = (48, 63, 159)
BUTTON_HOVER_START = (92, 107, 192)
BUTTON_HOVER_END = (75, 93, 173)
BUTTON_BORDER_COLOR = (33, 51, 131)
BUTTON_TEXT_SHADOW = (0, 0, 0, 150)

# Richtungen in Axialkoordinaten
DIRECTIONS = [
	(1, 0), (1, -1), (0, -1),
	(-1, 0), (-1, 1), (0, 1)
]


@dataclass
class Hex:
	"""Repräsentiert eine Position auf dem Hexagon-Brett"""
	q: int
	r: int

	def __hash__(self):
		return hash((self.q, self.r))

	def __eq__(self, other):
		if other is None:
			return False
		return self.q == other.q and self.r == other.r

	def __add__(self, other):
		return Hex(self.q + other.q, self.r + other.r)

	def __sub__(self, other):
		return Hex(self.q - other.q, self.r - other.r)

	def distance(self, other):
		"""Berechnet die Distanz zwischen zwei Hexagonen"""
		return (abs(self.q - other.q) + abs(self.q + self.r - other.q - other.r) +
		        abs(self.r - other.r)) // 2

	def neighbor(self, direction_index):
		"""Gibt den Nachbarn in der angegebenen Richtung zurück"""
		dq, dr = DIRECTIONS[direction_index]
		return Hex(self.q + dq, self.r + dr)

	def to_pixel(self, center_x, center_y):
		"""Konvertiert Axialkoordinaten zu Pixelkoordinaten"""
		x = HEX_SIZE * (3 / 2 * self.q)
		y = HEX_SIZE * (math.sqrt(3) / 2 * self.q + math.sqrt(3) * self.r)
		return int(center_x + x), int(center_y + y)


class Player(Enum):
	BLACK = 'B'
	WHITE = 'W'
	EMPTY = None


def draw_gradient_rect(surface, rect, start_color, end_color, vertical=True):
	"""Zeichnet ein Rechteck mit Farbverlauf"""
	if vertical:
		for y in range(rect.height):
			ratio = y / rect.height
			color = [
				int(start_color[i] + (end_color[i] - start_color[i]) * ratio)
				for i in range(3)
			]
			pygame.draw.line(surface, color, 
							(rect.x, rect.y + y), 
							(rect.x + rect.width, rect.y + y))
	else:
		for x in range(rect.width):
			ratio = x / rect.width
			color = [
				int(start_color[i] + (end_color[i] - start_color[i]) * ratio)
				for i in range(3)
			]
			pygame.draw.line(surface, color, 
							(rect.x + x, rect.y), 
							(rect.x + x, rect.y + rect.height))

def draw_gradient_circle(surface, center, radius, inner_color, outer_color):
	"""Zeichnet einen Kreis mit radialem Farbverlauf"""
	for r in range(radius, 0, -1):
		ratio = (radius - r) / radius
		color = [
			int(outer_color[i] + (inner_color[i] - outer_color[i]) * ratio)
			for i in range(3)
		]
		pygame.draw.circle(surface, color, center, r)

class Button:
	"""Erweiterte Button-Klasse mit Farbverläufen"""

	def __init__(self, x, y, width, height, text, font):
		self.rect = pygame.Rect(x, y, width, height)
		self.text = text
		self.font = font
		self.hovered = False
		self.pressed = False

	def draw(self, screen):
		# Farbverlauf je nach Zustand - verwende Theme-Farben
		colors = SETTINGS.get_theme_colors()
		if self.hovered:
			start_color = colors['button_start']
			end_color = colors['button_end']
			# Aufhellen für Hover-Effekt
			start_color = tuple(min(255, c + 30) for c in start_color)
			end_color = tuple(min(255, c + 30) for c in end_color)
		else:
			start_color = colors['button_start']
			end_color = colors['button_end']
		
		# Rand zeichnen
		border_rect = self.rect.inflate(4, 4)
		pygame.draw.rect(screen, BUTTON_BORDER_COLOR, border_rect, border_radius=8)
		
		# Farbverlauf zeichnen
		draw_gradient_rect(screen, self.rect, start_color, end_color)
		
		# Text mit Schatten
		text_surface = self.font.render(self.text, True, TEXT_COLOR)
		shadow_surface = self.font.render(self.text, True, (0, 0, 0))
		text_rect = text_surface.get_rect(center=self.rect.center)
		shadow_rect = text_rect.copy()
		shadow_rect.x += 1
		shadow_rect.y += 1
		
		screen.blit(shadow_surface, shadow_rect)
		screen.blit(text_surface, text_rect)

	def handle_event(self, event):
		if event.type == pygame.MOUSEMOTION:
			self.hovered = self.rect.collidepoint(event.pos)
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if self.rect.collidepoint(event.pos):
				return True
		return False


class AbaloneGame:
	"""Hauptklasse für die Spiellogik"""

	def __init__(self):
		self.board = {}
		self.current_player = Player.BLACK
		self.scores = {Player.BLACK: 0, Player.WHITE: 0}
		self.selected_marbles = []
		self.valid_moves = set()
		self.animating_marbles = []
		self._create_board()
		self._setup_initial_position()

	def _create_board(self):
		"""Erstellt das hexagonale Spielbrett"""
		for q in range(-4, 5):
			for r in range(-4, 5):
				s = -q - r
				if -4 <= s <= 4:
					self.board[Hex(q, r)] = Player.EMPTY

	def _setup_initial_position(self):
		"""Standard-Startaufstellung"""
		# Schwarze Kugeln (oben)
		black_positions = [
			Hex(-4, 0), Hex(-3, -1), Hex(-2, -2), Hex(-1, -3), Hex(0, -4),
			Hex(-4, 1), Hex(-3, 0), Hex(-2, -1), Hex(-1, -2), Hex(0, -3), Hex(1, -4),
			Hex(-2, 0), Hex(-1, -1), Hex(0, -2)
		]

		# Weiße Kugeln (unten)
		white_positions = [
			Hex(4, 0), Hex(3, 1), Hex(2, 2), Hex(1, 3), Hex(0, 4),
			Hex(4, -1), Hex(3, 0), Hex(2, 1), Hex(1, 2), Hex(0, 3), Hex(-1, 4),
			Hex(2, 0), Hex(1, 1), Hex(0, 2)
		]

		for pos in black_positions:
			self.board[pos] = Player.BLACK

		for pos in white_positions:
			self.board[pos] = Player.WHITE

	def _is_valid_position(self, hex_pos):
		"""Prüft, ob eine Position auf dem Brett ist"""
		return hex_pos in self.board

	def _get_line_direction(self, marbles):
		"""Bestimmt die Richtung einer Linie von Kugeln"""
		if len(marbles) < 2:
			return None

		# Sortiere die Kugeln für konsistente Verarbeitung
		marbles = sorted(marbles, key=lambda h: (h.q, h.r))

		# Prüfe alle 6 Richtungen
		for dir_idx in range(6):
			dq, dr = DIRECTIONS[dir_idx]
			valid = True

			# Prüfe ob alle Kugeln in dieser Richtung aufgereiht sind
			for i in range(1, len(marbles)):
				expected_q = marbles[0].q + dq * i
				expected_r = marbles[0].r + dr * i

				# Prüfe ob eine Kugel an der erwarteten Position ist
				found = False
				for marble in marbles:
					if marble.q == expected_q and marble.r == expected_r:
						found = True
						break

				if not found:
					valid = False
					break

			if valid:
				return dir_idx

		return None

	def _are_marbles_in_line(self, marbles):
		"""Prüft, ob Kugeln in einer Linie liegen"""
		if len(marbles) == 1:
			return True

		if len(marbles) > 3:
			return False  # Maximal 3 Kugeln können bewegt werden

		# Nutze _get_line_direction - wenn es eine Richtung zurückgibt, sind sie in einer Linie
		return self._get_line_direction(marbles) is not None

	def calculate_valid_moves(self, selected_marbles):
		"""Berechnet alle gültigen Züge für die ausgewählten Kugeln"""
		valid_moves = set()

		if not selected_marbles:
			return valid_moves

		# Prüfe ob alle Kugeln dem aktuellen Spieler gehören
		for marble in selected_marbles:
			if self.board[marble] != self.current_player:
				return valid_moves

		# Bei einer einzelnen Kugel
		if len(selected_marbles) == 1:
			marble = selected_marbles[0]
			# Prüfe alle 6 Nachbarfelder
			for dir_idx in range(6):
				target = marble.neighbor(dir_idx)
				if self._is_valid_position(target) and self.board[target] == Player.EMPTY:
					valid_moves.add(target)
			return valid_moves

		# Prüfe ob Kugeln in einer Linie liegen
		if not self._are_marbles_in_line(selected_marbles):
			return valid_moves

		# Prüfe alle 6 Richtungen für mehrere Kugeln
		for dir_idx in range(6):
			# Inline-Bewegung
			if self._can_move_inline(selected_marbles, dir_idx):
				# Berechne Zielposition für die führende Kugel
				lead_marble = self._get_lead_marble(selected_marbles, dir_idx)
				target = lead_marble.neighbor(dir_idx)
				valid_moves.add(target)

			# Seitwärtsbewegung
			if self._can_move_broadside(selected_marbles, dir_idx):
				# Füge die erste Kugel als Repräsentant hinzu
				target = selected_marbles[0].neighbor(dir_idx)
				valid_moves.add(target)

		return valid_moves

	def _get_lead_marble(self, marbles, direction):
		"""Findet die führende Kugel in einer bestimmten Richtung"""
		return max(marbles, key=lambda m: m.q * DIRECTIONS[direction][0] + m.r * DIRECTIONS[direction][1])

	def _can_move_inline(self, marbles, direction):
		"""Prüft, ob eine Inline-Bewegung möglich ist"""
		# Sortiere Kugeln in Bewegungsrichtung
		lead = self._get_lead_marble(marbles, direction)
		target = lead.neighbor(direction)

		# Prüfe, ob Ziel auf dem Brett ist
		if not self._is_valid_position(target):
			return False

		# Prüfe ob das Ziel eine eigene Kugel ist (nicht erlaubt!)
		if self.board[target] == self.current_player:
			return False

		# Leeres Feld - einfache Bewegung
		if self.board[target] == Player.EMPTY:
			return True

		# Gegnerische Kugel - prüfe Sumito
		if self.board[target] != self.current_player:
			return self._can_push(marbles, direction)

		return False

	def _can_move_broadside(self, marbles, direction):
		"""Prüft, ob eine Seitwärtsbewegung möglich ist"""
		# Bei einzelnen Kugeln gibt es keine Seitwärtsbewegung
		if len(marbles) < 2:
			return False

		# Prüfe ob die Richtung senkrecht zur Linie ist
		line_dir = self._get_line_direction(marbles)
		if line_dir is None:
			return False

		# Richtung muss senkrecht zur Linie sein (nicht parallel)
		if direction == line_dir or direction == (line_dir + 3) % 6:
			return False

		# WICHTIG: Prüfe ob ALLE Zielfelder frei sind
		for marble in marbles:
			target = marble.neighbor(direction)
			# Ziel muss auf dem Brett sein
			if not self._is_valid_position(target):
				return False
			# Ziel muss leer sein - keine eigenen oder gegnerischen Kugeln!
			if self.board[target] != Player.EMPTY:
				return False

		return True

	def _can_push(self, marbles, direction):
		"""Prüft, ob ein Sumito (Schieben) möglich ist"""
		opponent = Player.WHITE if self.current_player == Player.BLACK else Player.BLACK

		# Finde alle gegnerischen Kugeln in der Schieberichtung
		lead = self._get_lead_marble(marbles, direction)
		opponent_marbles = []

		current = lead.neighbor(direction)
		while self._is_valid_position(current) and self.board[current] == opponent:
			opponent_marbles.append(current)
			current = current.neighbor(direction)

		# Prüfe numerische Überlegenheit
		if len(marbles) <= len(opponent_marbles):
			return False

		# Prüfe ob das Feld hinter der letzten gegnerischen Kugel frei ist
		if opponent_marbles:
			last_opponent = opponent_marbles[-1]
			behind = last_opponent.neighbor(direction)

			# Kann vom Brett geschoben werden
			if not self._is_valid_position(behind):
				return True

			# Oder auf ein leeres Feld
			return self.board[behind] == Player.EMPTY

		return False

	def make_move(self, selected_marbles, target_hex):
		"""Führt einen Zug aus"""
		if not selected_marbles or target_hex not in self.calculate_valid_moves(selected_marbles):
			return False

		# Bestimme die Bewegungsrichtung
		direction = None

		# Für einzelne Kugeln ist es einfach
		if len(selected_marbles) == 1:
			for dir_idx in range(6):
				if selected_marbles[0].neighbor(dir_idx) == target_hex:
					direction = dir_idx
					break
		else:
			# Für mehrere Kugeln müssen wir prüfen ob es inline oder broadside ist
			for dir_idx in range(6):
				# Prüfe Seitwärtsbewegung
				if self._can_move_broadside(selected_marbles, dir_idx):
					# Bei Seitwärtsbewegung bewegen sich alle Kugeln in dieselbe Richtung
					if selected_marbles[0].neighbor(dir_idx) == target_hex:
						direction = dir_idx
						break

				# Prüfe Inline-Bewegung
				if self._can_move_inline(selected_marbles, dir_idx):
					lead = self._get_lead_marble(selected_marbles, dir_idx)
					if lead.neighbor(dir_idx) == target_hex:
						direction = dir_idx
						break

		if direction is None:
			return False

		# Führe den Zug aus
		if self._is_inline_move(selected_marbles, direction):
			self._execute_inline_move(selected_marbles, direction)
		else:
			# Nochmalige Validierung für Seitwärtsbewegung
			if not self._can_move_broadside(selected_marbles, direction):
				return False
			self._execute_broadside_move(selected_marbles, direction)

		# Wechsle den Spieler
		self.current_player = Player.WHITE if self.current_player == Player.BLACK else Player.BLACK
		return True

	def _is_inline_move(self, marbles, direction):
		"""Prüft, ob es eine Inline-Bewegung ist"""
		if len(marbles) == 1:
			return True  # Einzelne Kugeln sind immer inline

		line_dir = self._get_line_direction(marbles)
		if line_dir is None:
			return False

		# Inline wenn die Bewegung parallel zur Linie ist
		return line_dir == direction or line_dir == (direction + 3) % 6

	def _execute_inline_move(self, marbles, direction):
		"""Führt eine Inline-Bewegung aus"""
		# Sortiere Kugeln in Bewegungsrichtung (führende Kugel hat höchsten Wert)
		dq, dr = DIRECTIONS[direction]
		sorted_marbles = sorted(marbles,
		                        key=lambda m: m.q * dq + m.r * dr,
		                        reverse=True)

		# Die führende Kugel
		lead = sorted_marbles[0]
		target = lead.neighbor(direction)

		# Prüfe auf Sumito (Schieben gegnerischer Kugeln)
		if self._is_valid_position(target) and self.board[target] != Player.EMPTY:
			self._push_opponent_marbles(lead, direction)

		# Sammle alle Bewegungen (alte Position -> neue Position)
		moves = []
		for marble in sorted_marbles:
			old_pos = marble
			new_pos = marble.neighbor(direction)
			color = self.board[old_pos]
			moves.append((old_pos, new_pos, color))

		# Lösche erst alle alten Positionen
		for old_pos, _, _ in moves:
			self.board[old_pos] = Player.EMPTY

		# Setze dann alle neuen Positionen
		for _, new_pos, color in moves:
			self.board[new_pos] = color

	def _execute_broadside_move(self, marbles, direction):
		"""Führt eine Seitwärtsbewegung aus"""
		# Bewege alle Kugeln gleichzeitig
		new_positions = []
		for marble in marbles:
			new_pos = marble.neighbor(direction)
			new_positions.append((marble, new_pos))

		# Erst alle alten Positionen leeren
		for old, _ in new_positions:
			self.board[old] = Player.EMPTY

		# Dann alle neuen Positionen setzen
		for _, new in new_positions:
			self.board[new] = self.current_player

	def _push_opponent_marbles(self, from_pos, direction):
		"""Schiebt gegnerische Kugeln"""
		opponent = Player.WHITE if self.current_player == Player.BLACK else Player.BLACK

		# Finde alle zu schiebenden Kugeln
		marbles_to_push = []
		current = from_pos.neighbor(direction)

		while self._is_valid_position(current) and self.board[current] == opponent:
			marbles_to_push.append(current)
			current = current.neighbor(direction)

		# Schiebe von hinten nach vorne
		for marble in reversed(marbles_to_push):
			new_pos = marble.neighbor(direction)

			if not self._is_valid_position(new_pos):
				# Kugel wird vom Brett geschoben
				self.board[marble] = Player.EMPTY
				self.scores[self.current_player] += 1
			else:
				# Kugel wird auf neues Feld geschoben
				self.board[new_pos] = opponent
				self.board[marble] = Player.EMPTY

	def check_winner(self):
		"""Prüft, ob es einen Gewinner gibt"""
		if self.scores[Player.BLACK] >= 6:
			return Player.BLACK
		if self.scores[Player.WHITE] >= 6:
			return Player.WHITE
		return None

	def reset_game(self):
		"""Setzt das Spiel zurück"""
		self.board.clear()
		self.current_player = Player.BLACK
		self.scores = {Player.BLACK: 0, Player.WHITE: 0}
		self.selected_marbles = []
		self.valid_moves = set()
		self._create_board()
		self._setup_initial_position()


class AbaloneUI:
	"""UI-Klasse für die grafische Darstellung"""

	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption("Abalone")
		self.clock = pygame.time.Clock()
		self.font = pygame.font.Font(None, 36)
		self.small_font = pygame.font.Font(None, 24)
		self.large_font = pygame.font.Font(None, 48)

		# Game State Management
		self.current_state = GameState.MAIN_MENU
		self.game = None  # Wird erst bei Spielstart erstellt
		self.center_x = WINDOW_WIDTH // 2
		self.center_y = WINDOW_HEIGHT // 2

		# Game-spezifische Variablen
		self.dragging = False
		self.drag_start = None
		self.hovered_hex = None
		self.selected_marbles = []
		self.mouse_pos = (0, 0)
		
		# KI-spezifische Variablen
		self.ai = None
		self.ai_player = Player.WHITE  # KI spielt standardmäßig Weiß
		self.ai_thinking = False
		self.ai_move_timer = 0

		# Menüs
		self.main_menu = MainMenu(self.screen, self.font, self.large_font)
		self.settings_menu = SettingsMenu(self.screen, self.font, self.large_font)

		# Buttons für Game-View (werden bei Bedarf erstellt)
		self.new_game_button = None
		self.quit_button = None

		# Animation und Effekte
		self.animations = []
		self.particles = []
		self.background_pattern = self._create_background_pattern()
		self.animation_time = 0
	
	def start_game(self, game_mode):
		"""Startet ein neues Spiel im angegebenen Modus"""
		self.game = AbaloneGame()
		self.selected_marbles = []
		self.current_state = game_mode
		
		# KI-Setup für KI-Spiele
		if game_mode == GameState.GAME_AI:
			self.ai = AbaloneAI(SETTINGS.ai_difficulty)
			self.ai_player = Player.WHITE  # KI spielt Weiß
			self.ai_thinking = False
		else:
			self.ai = None
		
		# Erstelle Game-UI-Buttons
		self.new_game_button = Button(30, 20, 120, 40, "Menü", self.small_font)
		self.quit_button = Button(30, 70, 120, 40, "Beenden", self.small_font)
	
	def handle_menu_action(self, action):
		"""Behandelt Menü-Aktionen"""
		if action == "start_game":
			self.start_game(GameState.GAME_PVP)
		elif action == "ai_game":
			self.start_game(GameState.GAME_AI)
		elif action == "team_game":
			self.start_game(GameState.GAME_2V2)
		elif action == "settings":
			self.current_state = GameState.SETTINGS
		elif action == "quit":
			return "quit"
		elif action == "back":
			self.current_state = GameState.MAIN_MENU
		elif action.startswith("theme_"):
			theme_name = action.split("_")[1]
			for theme in Theme:
				if theme.value == theme_name:
					SETTINGS.current_theme = theme
					break
			# Menü neu aufbauen um Checkmarks zu aktualisieren
			self.settings_menu = SettingsMenu(self.screen, self.font, self.large_font)
		elif action == "toggle_sound":
			SETTINGS.sound_enabled = not SETTINGS.sound_enabled
			self.settings_menu = SettingsMenu(self.screen, self.font, self.large_font)
		elif action.startswith("ai_"):
			difficulty_level = int(action.split("_")[1])
			for diff in AIDifficulty:
				if diff.value == difficulty_level:
					SETTINGS.ai_difficulty = diff
					break
			self.settings_menu = SettingsMenu(self.screen, self.font, self.large_font)
		
		return None

	def _create_background_pattern(self):
		"""Erstellt ein Hintergrundmuster"""
		pattern = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		
		# Gradient background
		for y in range(WINDOW_HEIGHT):
			ratio = y / WINDOW_HEIGHT
			color = [
				int(BACKGROUND_COLOR[i] + (BOARD_GRADIENT_START[i] - BACKGROUND_COLOR[i]) * ratio * 0.3)
				for i in range(3)
			]
			pygame.draw.line(pattern, color, (0, y), (WINDOW_WIDTH, y))
		
		# Subtile geometrische Muster
		for x in range(0, WINDOW_WIDTH, 100):
			for y in range(0, WINDOW_HEIGHT, 100):
				if (x + y) % 200 == 0:
					color = [min(255, c + 5) for c in BACKGROUND_COLOR]
					pygame.draw.circle(pattern, color, (x, y), 20, 1)
		
		return pattern

	def add_particle_effect(self, pos, color, count=10):
		"""Fügt Partikel-Effekt hinzu"""
		for _ in range(count):
			particle = {
				'pos': list(pos),
				'vel': [random.uniform(-3, 3), random.uniform(-3, 3)],
				'color': color,
				'life': 1.0,
				'size': random.uniform(2, 5)
			}
			self.particles.append(particle)

	def update_particles(self):
		"""Aktualisiert Partikel-Effekte"""
		for particle in self.particles[:]:
			particle['pos'][0] += particle['vel'][0]
			particle['pos'][1] += particle['vel'][1]
			particle['life'] -= 0.02
			particle['vel'][1] += 0.1  # Gravity
			
			if particle['life'] <= 0:
				self.particles.remove(particle)

	def draw_particles(self):
		"""Zeichnet Partikel-Effekte"""
		for particle in self.particles:
			alpha = int(255 * particle['life'])
			if alpha > 0:
				color = (*particle['color'][:3], alpha)
				size = int(particle['size'] * particle['life'])
				if size > 0:
					s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
					pygame.draw.circle(s, color, (size, size), size)
					self.screen.blit(s, (particle['pos'][0] - size, particle['pos'][1] - size))

	def hex_to_pixel(self, hex_pos):
		"""Konvertiert Hex-Koordinaten zu Pixel-Koordinaten"""
		return hex_pos.to_pixel(self.center_x, self.center_y)

	def pixel_to_hex(self, x, y):
		"""Konvertiert Pixel-Koordinaten zu Hex-Koordinaten"""
		# Offset vom Zentrum
		x -= self.center_x
		y -= self.center_y

		# Konvertiere zu Axialkoordinaten
		q = (2 / 3 * x) / HEX_SIZE
		r = (-1 / 3 * x + math.sqrt(3) / 3 * y) / HEX_SIZE

		# Runde zu nächstem Hex
		return self._round_hex(q, r)

	def _round_hex(self, q, r):
		"""Rundet fraktionale Hex-Koordinaten"""
		s = -q - r
		rq = round(q)
		rr = round(r)
		rs = round(s)

		q_diff = abs(rq - q)
		r_diff = abs(rr - r)
		s_diff = abs(rs - s)

		if q_diff > r_diff and q_diff > s_diff:
			rq = -rr - rs
		elif r_diff > s_diff:
			rr = -rq - rs

		return Hex(int(rq), int(rr))

	def draw_hexagon(self, center_x, center_y, use_gradient=True, selected=False, valid_move=False):
		"""Zeichnet ein verbessertes Hexagon mit Farbverläufen ohne Überlappung"""
		# Optimierte Hexagon-Größe für größeres Spielfeld
		hex_draw_size = HEX_SIZE * 0.9
		
		points = []
		for i in range(6):
			angle = math.pi / 3 * i + math.pi / 6
			x = center_x + hex_draw_size * math.cos(angle)
			y = center_y + hex_draw_size * math.sin(angle)
			points.append((x, y))

		# Äußerer Rand (dunkler) - mit Abstand
		outer_points = []
		for i in range(6):
			angle = math.pi / 3 * i + math.pi / 6
			x = center_x + (hex_draw_size + 1) * math.cos(angle)
			y = center_y + (hex_draw_size + 1) * math.sin(angle)
			outer_points.append((x, y))
		
		pygame.draw.polygon(self.screen, BOARD_BORDER_COLOR, outer_points)

		# Basis-Hexagon mit Farbverlauf
		if use_gradient:
			# Simuliere Farbverlauf durch mehrere Polygone
			for i in range(8):  # Reduziert für bessere Performance
				ratio = i / 8
				color = [
					int(BOARD_GRADIENT_START[j] + (BOARD_GRADIENT_END[j] - BOARD_GRADIENT_START[j]) * ratio)
					for j in range(3)
				]
				size_factor = 1 - (i * 0.06)
				inner_points = []
				for k in range(6):
					angle = math.pi / 3 * k + math.pi / 6
					x = center_x + (hex_draw_size * size_factor) * math.cos(angle)
					y = center_y + (hex_draw_size * size_factor) * math.sin(angle)
					inner_points.append((x, y))
				pygame.draw.polygon(self.screen, color, inner_points)
		else:
			pygame.draw.polygon(self.screen, BOARD_GRADIENT_START, points)

		# Highlight-Effekte - reduzierte Größe
		if valid_move:
			# Grüner Glow für gültige Züge
			s = pygame.Surface((hex_draw_size * 2.5, hex_draw_size * 2.5), pygame.SRCALPHA)
			for i in range(10):
				alpha = 100 - (i * 10)
				if alpha > 0:
					color = (*HIGHLIGHT_COLOR, alpha)
					pygame.draw.circle(s, color, (hex_draw_size * 1.25, hex_draw_size * 1.25), 
									  hex_draw_size * 0.6 + i * 2)
			self.screen.blit(s, (center_x - hex_draw_size * 1.25, center_y - hex_draw_size * 1.25))
		
		if selected:
			# Goldener Glow für Auswahl
			s = pygame.Surface((hex_draw_size * 2.5, hex_draw_size * 2.5), pygame.SRCALPHA)
			for i in range(8):
				alpha = 120 - (i * 15)
				if alpha > 0:
					color = (*SELECTED_GLOW[:3], alpha)
					pygame.draw.circle(s, color, (hex_draw_size * 1.25, hex_draw_size * 1.25), 
									  hex_draw_size * 0.6 + i * 2)
			self.screen.blit(s, (center_x - hex_draw_size * 1.25, center_y - hex_draw_size * 1.25))

		# Innerer Highlight - angepasste Größe
		inner_points = []
		for i in range(6):
			angle = math.pi / 3 * i + math.pi / 6
			x = center_x + (hex_draw_size * 0.75) * math.cos(angle)
			y = center_y + (hex_draw_size * 0.75) * math.sin(angle)
			inner_points.append((x, y))
		pygame.draw.polygon(self.screen, BOARD_HIGHLIGHT_COLOR, inner_points, 1)

	def draw_board(self):
		"""Zeichnet das verbesserte Spielbrett mit Theme-Farben"""
		# Verwende Theme-Farben
		colors = SETTINGS.get_theme_colors()
		self.screen.fill(colors['background'])
		
		# Subtile Animation des Hintergrunds
		self.animation_time += 0.02
		animation_offset = math.sin(self.animation_time) * 2
		
		# Zeichne Board-Rand mit Glow-Effekt
		board_center = (self.center_x, self.center_y)
		board_radius = HEX_SIZE * 6
		
		# Äußerer Glow
		for i in range(20):
			alpha = 30 - i
			if alpha > 0:
				color = (*BOARD_HIGHLIGHT_COLOR, alpha)
				s = pygame.Surface((board_radius * 2 + i * 4, board_radius * 2 + i * 4), pygame.SRCALPHA)
				pygame.draw.circle(s, color, (board_radius + i * 2, board_radius + i * 2), board_radius + i * 2, 2)
				self.screen.blit(s, (board_center[0] - board_radius - i * 2, board_center[1] - board_radius - i * 2))
		
		for hex_pos in self.game.board:
			x, y = self.hex_to_pixel(hex_pos)

			# Bestimme Hexagon-Zustand
			selected = hex_pos in self.selected_marbles
			valid_move = hex_pos in self.game.valid_moves
			
			# Basis-Hexagon mit Verbesserungen und Animation
			animated_y = y + animation_offset
			self.draw_hexagon(x, animated_y, use_gradient=True, selected=selected, valid_move=valid_move)

			# Hover-Effekt - angepasste Größe
			if hex_pos == self.hovered_hex and hex_pos not in self.selected_marbles:
				hex_draw_size = HEX_SIZE * 0.85
				s = pygame.Surface((hex_draw_size * 2, hex_draw_size * 2), pygame.SRCALPHA)
				for i in range(6):
					alpha = 80 - (i * 12)
					if alpha > 0:
						color = (*HOVER_GLOW[:3], alpha)
						pygame.draw.circle(s, color, (hex_draw_size, hex_draw_size), 
										  hex_draw_size * 0.6 + i * 2)
				self.screen.blit(s, (x - hex_draw_size, animated_y - hex_draw_size))

	def draw_marble(self, hex_pos, player, selected=False, preview=False):
		"""Zeichnet eine verbesserte Kugel mit 3D-Effekt"""
		x, y = self.hex_to_pixel(hex_pos)
		# Angepasste Kugel-Größe für bessere Darstellung
		radius = int(HEX_SIZE * 0.4)

		# Bestimme Farben basierend auf Spieler
		if player == Player.BLACK:
			dark_color = BLACK_MARBLE_DARK
			light_color = BLACK_MARBLE_LIGHT
			highlight_color = BLACK_MARBLE_HIGHLIGHT
		else:
			dark_color = WHITE_MARBLE_DARK
			light_color = WHITE_MARBLE_LIGHT
			highlight_color = WHITE_MARBLE_HIGHLIGHT

		if preview:
			# Transparente Vorschau
			s = pygame.Surface((HEX_SIZE * 2, HEX_SIZE * 2), pygame.SRCALPHA)

			# Schatten
			pygame.draw.circle(s, (0, 0, 0, 40), (HEX_SIZE + 3, HEX_SIZE + 3), radius)

			# Basis-Kugel mit Transparenz
			for i in range(radius, 0, -2):
				ratio = (radius - i) / radius
				color = [
					int(dark_color[j] + (light_color[j] - dark_color[j]) * ratio)
					for j in range(3)
				]
				color.append(80)  # Alpha für Transparenz
				pygame.draw.circle(s, color, (HEX_SIZE, HEX_SIZE), i)

			# Glanzlicht
			pygame.draw.circle(s, (*highlight_color, 60), (HEX_SIZE - 8, HEX_SIZE - 8), radius // 3)

			self.screen.blit(s, (x - HEX_SIZE, y - HEX_SIZE))
		else:
			# Normale Darstellung mit 3D-Effekt
			# Schatten (mehrschichtig für weicheren Effekt)
			for i in range(5):
				alpha = 60 - (i * 10)
				if alpha > 0:
					s = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
					pygame.draw.circle(s, (0, 0, 0, alpha), (radius + 5, radius + 5), radius + i)
					self.screen.blit(s, (x - radius - 5 + 2, y - radius - 5 + 2))

			# Radialer Farbverlauf für 3D-Effekt
			for i in range(radius, 0, -1):
				ratio = (radius - i) / radius
				color = [
					int(dark_color[j] + (light_color[j] - dark_color[j]) * ratio)
					for j in range(3)
				]
				pygame.draw.circle(self.screen, color, (x, y), i)

			# Mehrere Glanzlichter für realistischen Effekt
			# Hauptglanzlicht
			pygame.draw.circle(self.screen, highlight_color, (x - 8, y - 8), radius // 3)
			# Sekundäres Glanzlicht
			pygame.draw.circle(self.screen, highlight_color, (x - 12, y - 6), radius // 6)
			# Subtiler Rim-Light
			pygame.draw.circle(self.screen, light_color, (x, y), radius, 1)

			# Auswahlmarkierung mit Glow-Effekt
			if selected:
				s = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
				for i in range(12):
					alpha = 200 - (i * 16)
					if alpha > 0:
						color = (*SELECTED_GLOW[:3], alpha)
						pygame.draw.circle(s, color, (radius * 1.5, radius * 1.5), radius + i)
				self.screen.blit(s, (x - radius * 1.5, y - radius * 1.5))

	def draw_ui(self):
		"""Zeichnet die kompaktere UI-Info-Box"""
		# Kleineres UI-Panel rechts oben
		ui_rect = pygame.Rect(WINDOW_WIDTH - 280, 20, 250, 180)
		
		# Kompakte Panel-Darstellung
		colors = SETTINGS.get_theme_colors()
		panel_bg = pygame.Surface((ui_rect.width, ui_rect.height), pygame.SRCALPHA)
		draw_gradient_rect(panel_bg, pygame.Rect(0, 0, ui_rect.width, ui_rect.height), 
						  (*colors['board_start'], 200), (*colors['board_end'], 200))
		self.screen.blit(panel_bg, ui_rect.topleft)
		
		# Rand
		pygame.draw.rect(self.screen, colors['board_border'], ui_rect, 2, border_radius=8)
		
		# Kompakte Spieler-Info
		player_text = "Schwarz" if self.game.current_player == Player.BLACK else "Weiß"
		
		# Am Zug Text (kompakt)
		turn_text = f"Am Zug: {player_text}"
		turn_shadow = self.small_font.render(turn_text, True, (0, 0, 0))
		turn_surface = self.small_font.render(turn_text, True, TEXT_COLOR)
		self.screen.blit(turn_shadow, (ui_rect.x + 11, ui_rect.y + 11))
		self.screen.blit(turn_surface, (ui_rect.x + 10, ui_rect.y + 10))

		# Kompakte Scores
		black_text = f"Schwarz: {self.game.scores[Player.BLACK]}/6"
		white_text = f"Weiß: {self.game.scores[Player.WHITE]}/6"
		
		black_shadow = self.small_font.render(black_text, True, (0, 0, 0))
		black_surface = self.small_font.render(black_text, True, (180, 180, 190))
		white_shadow = self.small_font.render(white_text, True, (0, 0, 0))
		white_surface = self.small_font.render(white_text, True, (255, 255, 255))
		
		self.screen.blit(black_shadow, (ui_rect.x + 11, ui_rect.y + 41))
		self.screen.blit(black_surface, (ui_rect.x + 10, ui_rect.y + 40))
		self.screen.blit(white_shadow, (ui_rect.x + 11, ui_rect.y + 61))
		self.screen.blit(white_surface, (ui_rect.x + 10, ui_rect.y + 60))
		
		# Kompakte Progress-Balken
		bar_width = 200
		bar_height = 8
		bar_x = ui_rect.x + 10
		
		# Schwarz Balken
		black_bar = pygame.Rect(bar_x, ui_rect.y + 85, bar_width, bar_height)
		pygame.draw.rect(self.screen, colors['board_border'], black_bar, border_radius=4)
		black_progress = pygame.Rect(bar_x, ui_rect.y + 85, 
									(bar_width * self.game.scores[Player.BLACK]) // 6, bar_height)
		if black_progress.width > 0:
			pygame.draw.rect(self.screen, (120, 120, 140), black_progress, border_radius=4)
		
		# Weiß Balken
		white_bar = pygame.Rect(bar_x, ui_rect.y + 100, bar_width, bar_height)
		pygame.draw.rect(self.screen, colors['board_border'], white_bar, border_radius=4)
		white_progress = pygame.Rect(bar_x, ui_rect.y + 100, 
									(bar_width * self.game.scores[Player.WHITE]) // 6, bar_height)
		if white_progress.width > 0:
			pygame.draw.rect(self.screen, (255, 255, 255), white_progress, border_radius=4)

		# Gewinner-Nachricht mit Effekt
		winner = self.game.check_winner()
		if winner:
			winner_text = "Schwarz" if winner == Player.BLACK else "Weiß"
			
			# Hintergrund mit Glow
			wins_bg_rect = pygame.Rect(0, 100, WINDOW_WIDTH, 100)
			win_bg = pygame.Surface((WINDOW_WIDTH, 100), pygame.SRCALPHA)
			draw_gradient_rect(win_bg, pygame.Rect(0, 0, WINDOW_WIDTH, 100), 
							  (255, 193, 7, 200), (102, 187, 106, 200))
			self.screen.blit(win_bg, (0, 100))
			
			# Text mit größerer Schrift und besserem Kontrast
			win_text = f"🎉 {winner_text} hat gewonnen! 🎉"
			win_shadow = self.large_font.render(win_text, True, (0, 0, 0))
			win_surface = self.large_font.render(win_text, True, (255, 255, 255))
			win_rect = win_surface.get_rect(center=(WINDOW_WIDTH // 2, 150))
			win_shadow_rect = win_rect.copy()
			win_shadow_rect.x += 3
			win_shadow_rect.y += 3
			
			self.screen.blit(win_shadow, win_shadow_rect)
			self.screen.blit(win_surface, win_rect)
			
			# Partikel-Effekt für Gewinn
			if random.random() < 0.3:
				self.add_particle_effect((WINDOW_WIDTH // 2, 150), SELECTED_GLOW[:3])

	def draw_preview(self):
		"""Zeichnet eine Vorschau der ausgewählten Kugeln an der Mausposition"""
		if not self.selected_marbles or not self.hovered_hex:
			return

		# Prüfe ob dies ein gültiger Zug wäre
		if self.hovered_hex not in self.game.valid_moves:
			return

		# Bestimme die Bewegungsrichtung
		direction = None

		if len(self.selected_marbles) == 1:
			# Für einzelne Kugeln
			for dir_idx in range(6):
				if self.selected_marbles[0].neighbor(dir_idx) == self.hovered_hex:
					direction = dir_idx
					break
		else:
			# Für mehrere Kugeln
			for dir_idx in range(6):
				# Prüfe ob es eine gültige Bewegung in diese Richtung ist
				if self.game._is_inline_move(self.selected_marbles, dir_idx):
					lead = self.game._get_lead_marble(self.selected_marbles, dir_idx)
					if lead.neighbor(dir_idx) == self.hovered_hex:
						direction = dir_idx
						break
				elif self.game._can_move_broadside(self.selected_marbles, dir_idx):
					if self.selected_marbles[0].neighbor(dir_idx) == self.hovered_hex:
						direction = dir_idx
						break

		if direction is None:
			return

		# Zeichne gestrichelte Linien von Original zu Vorschau
		for marble in self.selected_marbles:
			start_x, start_y = self.hex_to_pixel(marble)
			new_pos = marble.neighbor(direction)
			if self.game._is_valid_position(new_pos):
				end_x, end_y = self.hex_to_pixel(new_pos)

				# Zeichne gestrichelte Linie
				distance = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
				steps = int(distance / 10)
				for i in range(0, steps, 2):
					t1 = i / steps
					t2 = min((i + 1) / steps, 1)
					x1 = start_x + (end_x - start_x) * t1
					y1 = start_y + (end_y - start_y) * t1
					x2 = start_x + (end_x - start_x) * t2
					y2 = start_y + (end_y - start_y) * t2
					pygame.draw.line(self.screen, HIGHLIGHT_COLOR, (x1, y1), (x2, y2), 2)

		# Zeichne transparente Vorschau der Kugeln an neuer Position
		for marble in self.selected_marbles:
			new_pos = marble.neighbor(direction)
			if self.game._is_valid_position(new_pos):
				self.draw_marble(new_pos, self.game.current_player, preview=True)

	def handle_click(self, pos):
		"""Verarbeitet Mausklicks"""
		hex_pos = self.pixel_to_hex(*pos)

		if hex_pos not in self.game.board:
			return

		# Bei KI-Spiel: Verhindere Klicks wenn KI am Zug ist
		if self.ai and self.game.current_player == self.ai_player:
			return

		marble = self.game.board[hex_pos]

		# Klick auf eigene Kugel
		if marble == self.game.current_player:
			if hex_pos in self.selected_marbles:
				self.selected_marbles.remove(hex_pos)
			else:
				self.selected_marbles.append(hex_pos)

			# Aktualisiere gültige Züge
			self.game.valid_moves = self.game.calculate_valid_moves(self.selected_marbles)

		# Klick auf gültigen Zug
		elif hex_pos in self.game.valid_moves:
			if self.game.make_move(self.selected_marbles, hex_pos):
				# Partikel-Effekt für erfolgreichen Zug
				pixel_pos = self.hex_to_pixel(hex_pos)
				self.add_particle_effect(pixel_pos, HIGHLIGHT_COLOR, 8)
				
				self.selected_marbles = []
				self.game.valid_moves = set()

	def run(self):
		"""Hauptspiel-Loop mit State-Management"""
		running = True

		while running:
			# Events verarbeiten
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False

				elif event.type == pygame.MOUSEBUTTONDOWN:
					if self.current_state == GameState.MAIN_MENU:
						action = self.main_menu.handle_event(event)
						if action:
							result = self.handle_menu_action(action)
							if result == "quit":
								running = False
								
					elif self.current_state == GameState.SETTINGS:
						action = self.settings_menu.handle_event(event)
						if action:
							result = self.handle_menu_action(action)
							if result == "quit":
								running = False
								
					elif self.current_state in [GameState.GAME_PVP, GameState.GAME_AI, GameState.GAME_2V2]:
						# Game-spezifische Event-Behandlung
						if self.new_game_button and self.new_game_button.handle_event(event):
							self.current_state = GameState.MAIN_MENU
						elif self.quit_button and self.quit_button.handle_event(event):
							running = False
						else:
							# Nur Klicks verarbeiten wenn KI nicht am Denken ist
							if not self.ai_thinking:
								self.handle_click(event.pos)

				elif event.type == pygame.MOUSEMOTION:
					self.mouse_pos = event.pos
					
					# Menü-Hover-Effekte
					if self.current_state == GameState.MAIN_MENU:
						self.main_menu.handle_event(event)
					elif self.current_state == GameState.SETTINGS:
						self.settings_menu.handle_event(event)
					elif self.current_state in [GameState.GAME_PVP, GameState.GAME_AI, GameState.GAME_2V2]:
						# Game-spezifische Hover-Behandlung
						if self.new_game_button:
							self.new_game_button.handle_event(event)
						if self.quit_button:
							self.quit_button.handle_event(event)

						# Update hover für Hexagons
						if self.game:
							self.hovered_hex = self.pixel_to_hex(*event.pos)
							if self.hovered_hex not in self.game.board:
								self.hovered_hex = None

			# Bildschirm zeichnen basierend auf aktuellem State
			if self.current_state == GameState.MAIN_MENU:
				self.main_menu.draw()
			elif self.current_state == GameState.SETTINGS:
				self.settings_menu.draw()
			elif self.current_state in [GameState.GAME_PVP, GameState.GAME_AI, GameState.GAME_2V2]:
				self.draw_game()

			# Update
			pygame.display.flip()
			self.clock.tick(FPS)

		pygame.quit()
		sys.exit()
	
	def draw_game(self):
		"""Zeichnet das Spiel"""
		if not self.game:
			return
			
		# KI-Update (falls KI-Spiel)
		self.update_ai()
			
		# Zeichne Brett (enthält jetzt Hintergrund)
		self.draw_board()

		# Zeichne Kugeln
		for hex_pos, player in self.game.board.items():
			if player != Player.EMPTY:
				selected = hex_pos in self.selected_marbles
				self.draw_marble(hex_pos, player, selected)

		# Zeichne Vorschau (nur wenn nicht KI am Zug)
		if not self.ai_thinking:
			self.draw_preview()

		# Update und zeichne Partikel
		self.update_particles()
		self.draw_particles()

		# Zeichne kompakte UI
		self.draw_ui()
		
		# Zeichne Game-Buttons
		if self.new_game_button:
			self.new_game_button.draw(self.screen)
		if self.quit_button:
			self.quit_button.draw(self.screen)
			
		# Zeichne KI-Status
		if self.ai_thinking:
			self.draw_ai_thinking()
	
	def update_ai(self):
		"""Aktualisiert die KI-Logik"""
		if not self.ai or self.current_state != GameState.GAME_AI:
			return
			
		# Prüfe ob KI am Zug ist
		if self.game.current_player == self.ai_player and not self.ai_thinking:
			# Starte KI-Denkprozess in eigenem Thread
			import threading
			self.ai_thinking = True
			self.selected_marbles = []  # Deselektiere alle Kugeln
			
			def ai_move_thread():
				try:
					ai_move = self.ai.get_best_move(self.game, self.ai_player)
					if ai_move:
						selected_marbles, target_hex = ai_move
						# Führe den Zug aus
						if self.game.make_move(selected_marbles, target_hex):
							# Partikel-Effekt für KI-Zug
							pixel_pos = self.hex_to_pixel(target_hex)
							self.add_particle_effect(pixel_pos, HIGHLIGHT_COLOR, 12)
				except Exception as e:
					print(f"KI-Fehler: {e}")
				finally:
					self.ai_thinking = False
			
			threading.Thread(target=ai_move_thread, daemon=True).start()
	
	def draw_ai_thinking(self):
		"""Zeichnet KI-Denkstatus"""
		colors = SETTINGS.get_theme_colors()
		
		# Thinking-Box
		think_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, 50, 300, 60)
		
		# Panel mit Animation
		panel_bg = pygame.Surface((think_rect.width, think_rect.height), pygame.SRCALPHA)
		draw_gradient_rect(panel_bg, pygame.Rect(0, 0, think_rect.width, think_rect.height),
						  (*colors['button_start'], 180), (*colors['button_end'], 180))
		self.screen.blit(panel_bg, think_rect.topleft)
		
		pygame.draw.rect(self.screen, colors['board_border'], think_rect, 2, border_radius=8)
		
		# Animierter Text
		dots = "." * ((int(self.animation_time * 3) % 4) + 1)
		think_text = f"KI denkt{dots}"
		
		think_shadow = self.font.render(think_text, True, (0, 0, 0))
		think_surface = self.font.render(think_text, True, TEXT_COLOR)
		think_text_rect = think_surface.get_rect(center=think_rect.center)
		think_shadow_rect = think_text_rect.copy()
		think_shadow_rect.x += 2
		think_shadow_rect.y += 2
		
		self.screen.blit(think_shadow, think_shadow_rect)
		self.screen.blit(think_surface, think_text_rect)


if __name__ == "__main__":
	game = AbaloneUI()
	game.run()