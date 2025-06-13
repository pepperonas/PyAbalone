import pygame
import math
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional, Set, Dict
import sys

# Konstanten
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
HEX_SIZE = 35
FPS = 60

# Material Design Farben
BACKGROUND_COLOR = (44, 46, 59)  # #2C2E3B
BOARD_COLOR = (69, 71, 90)
HIGHLIGHT_COLOR = (76, 175, 80)  # Material Green
VALID_MOVE_COLOR = (76, 175, 80, 100)  # Semi-transparent green
BLACK_MARBLE_COLOR = (33, 33, 33)
WHITE_MARBLE_COLOR = (240, 240, 240)
SELECTED_GLOW = (255, 193, 7)  # Material Amber
HOVER_GLOW = (100, 181, 246)  # Material Light Blue
TEXT_COLOR = (255, 255, 255)
BUTTON_COLOR = (63, 81, 181)  # Material Indigo
BUTTON_HOVER_COLOR = (92, 107, 192)

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


class Button:
	"""Einfache Button-Klasse für UI"""

	def __init__(self, x, y, width, height, text, font):
		self.rect = pygame.Rect(x, y, width, height)
		self.text = text
		self.font = font
		self.hovered = False

	def draw(self, screen):
		color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
		pygame.draw.rect(screen, color, self.rect, border_radius=5)
		text_surface = self.font.render(self.text, True, TEXT_COLOR)
		text_rect = text_surface.get_rect(center=self.rect.center)
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

		self.game = AbaloneGame()
		self.center_x = WINDOW_WIDTH // 2
		self.center_y = WINDOW_HEIGHT // 2

		self.dragging = False
		self.drag_start = None
		self.hovered_hex = None
		self.selected_marbles = []
		self.mouse_pos = (0, 0)

		# Buttons
		self.new_game_button = Button(50, 50, 150, 40, "Neues Spiel", self.small_font)
		self.quit_button = Button(50, 100, 150, 40, "Beenden", self.small_font)

		# Animation
		self.animations = []

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

	def draw_hexagon(self, center_x, center_y, color, border_color=None):
		"""Zeichnet ein Hexagon"""
		points = []
		for i in range(6):
			angle = math.pi / 3 * i + math.pi / 6
			x = center_x + HEX_SIZE * math.cos(angle)
			y = center_y + HEX_SIZE * math.sin(angle)
			points.append((x, y))

		pygame.draw.polygon(self.screen, color, points)
		if border_color:
			pygame.draw.polygon(self.screen, border_color, points, 2)

	def draw_board(self):
		"""Zeichnet das Spielbrett"""
		for hex_pos in self.game.board:
			x, y = self.hex_to_pixel(hex_pos)

			# Basis-Hexagon
			self.draw_hexagon(x, y, BOARD_COLOR, (100, 100, 100))

			# Highlight für gültige Züge
			if hex_pos in self.game.valid_moves:
				# Zeichne semi-transparenten grünen Kreis
				s = pygame.Surface((HEX_SIZE * 2, HEX_SIZE * 2), pygame.SRCALPHA)
				pygame.draw.circle(s, VALID_MOVE_COLOR, (HEX_SIZE, HEX_SIZE), HEX_SIZE // 2)
				self.screen.blit(s, (x - HEX_SIZE, y - HEX_SIZE))

			# Hover-Effekt
			if hex_pos == self.hovered_hex:
				pygame.draw.circle(self.screen, HOVER_GLOW, (x, y), HEX_SIZE // 2, 3)

	def draw_marble(self, hex_pos, color, selected=False, preview=False):
		"""Zeichnet eine Kugel"""
		x, y = self.hex_to_pixel(hex_pos)

		if preview:
			# Transparente Vorschau
			s = pygame.Surface((HEX_SIZE * 2, HEX_SIZE * 2), pygame.SRCALPHA)

			# Schatten (noch transparenter)
			pygame.draw.circle(s, (20, 20, 20, 50), (HEX_SIZE + 2, HEX_SIZE + 2), HEX_SIZE // 2 - 5)

			# Kugel (transparent)
			marble_color = (*color, 100)  # Alpha = 100 für Transparenz
			pygame.draw.circle(s, marble_color, (HEX_SIZE, HEX_SIZE), HEX_SIZE // 2 - 5)

			# Glanzlicht (transparent)
			pygame.draw.circle(s, (255, 255, 255, 30), (HEX_SIZE - 5, HEX_SIZE - 5), HEX_SIZE // 4)

			self.screen.blit(s, (x - HEX_SIZE, y - HEX_SIZE))
		else:
			# Normale Darstellung
			# Schatten
			pygame.draw.circle(self.screen, (20, 20, 20), (x + 2, y + 2), HEX_SIZE // 2 - 5)

			# Kugel
			pygame.draw.circle(self.screen, color, (x, y), HEX_SIZE // 2 - 5)

			# Glanzlicht
			pygame.draw.circle(self.screen, (255, 255, 255, 50), (x - 5, y - 5), HEX_SIZE // 4)

			# Auswahlmarkierung
			if selected:
				pygame.draw.circle(self.screen, SELECTED_GLOW, (x, y), HEX_SIZE // 2 - 3, 3)

	def draw_ui(self):
		"""Zeichnet die UI-Elemente"""
		# Spieler-Info
		player_text = "Schwarz" if self.game.current_player == Player.BLACK else "Weiß"
		text_surface = self.font.render(f"Am Zug: {player_text}", True, TEXT_COLOR)
		self.screen.blit(text_surface, (WINDOW_WIDTH - 300, 50))

		# Punktestand
		black_score = self.font.render(f"Schwarz: {self.game.scores[Player.BLACK]}/6", True, TEXT_COLOR)
		white_score = self.font.render(f"Weiß: {self.game.scores[Player.WHITE]}/6", True, TEXT_COLOR)
		self.screen.blit(black_score, (WINDOW_WIDTH - 300, 100))
		self.screen.blit(white_score, (WINDOW_WIDTH - 300, 140))

		# Buttons
		self.new_game_button.draw(self.screen)
		self.quit_button.draw(self.screen)

		# Gewinner-Nachricht
		winner = self.game.check_winner()
		if winner:
			winner_text = "Schwarz" if winner == Player.BLACK else "Weiß"
			win_surface = self.font.render(f"{winner_text} hat gewonnen!", True, SELECTED_GLOW)
			win_rect = win_surface.get_rect(center=(WINDOW_WIDTH // 2, 100))
			pygame.draw.rect(self.screen, BACKGROUND_COLOR, win_rect.inflate(20, 10))
			self.screen.blit(win_surface, win_rect)

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
				color = BLACK_MARBLE_COLOR if self.game.current_player == Player.BLACK else WHITE_MARBLE_COLOR
				self.draw_marble(new_pos, color, preview=True)

	def handle_click(self, pos):
		"""Verarbeitet Mausklicks"""
		hex_pos = self.pixel_to_hex(*pos)

		if hex_pos not in self.game.board:
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
				self.selected_marbles = []
				self.game.valid_moves = set()

	def run(self):
		"""Hauptspiel-Loop"""
		running = True

		while running:
			# Events verarbeiten
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False

				elif event.type == pygame.MOUSEBUTTONDOWN:
					if self.new_game_button.handle_event(event):
						self.game.reset_game()
						self.selected_marbles = []
					elif self.quit_button.handle_event(event):
						running = False
					else:
						self.handle_click(event.pos)

				elif event.type == pygame.MOUSEMOTION:
					self.mouse_pos = event.pos
					self.new_game_button.handle_event(event)
					self.quit_button.handle_event(event)

					# Update hover
					self.hovered_hex = self.pixel_to_hex(*event.pos)
					if self.hovered_hex not in self.game.board:
						self.hovered_hex = None

			# Bildschirm zeichnen
			self.screen.fill(BACKGROUND_COLOR)

			# Zeichne Brett
			self.draw_board()

			# Zeichne Kugeln
			for hex_pos, player in self.game.board.items():
				if player != Player.EMPTY:
					color = BLACK_MARBLE_COLOR if player == Player.BLACK else WHITE_MARBLE_COLOR
					selected = hex_pos in self.selected_marbles
					self.draw_marble(hex_pos, color, selected)

			# Zeichne Vorschau
			self.draw_preview()

			# Zeichne UI
			self.draw_ui()

			# Update
			pygame.display.flip()
			self.clock.tick(FPS)

		pygame.quit()
		sys.exit()


if __name__ == "__main__":
	game = AbaloneUI()
	game.run()