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
		# Farbverlauf je nach Zustand
		if self.hovered:
			start_color = BUTTON_HOVER_START
			end_color = BUTTON_HOVER_END
		else:
			start_color = BUTTON_GRADIENT_START
			end_color = BUTTON_GRADIENT_END
		
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

		self.game = AbaloneGame()
		self.center_x = WINDOW_WIDTH // 2
		self.center_y = WINDOW_HEIGHT // 2

		self.dragging = False
		self.drag_start = None
		self.hovered_hex = None
		self.selected_marbles = []
		self.mouse_pos = (0, 0)

		# Buttons mit verbessertem Design und besserer Position
		self.new_game_button = Button(30, 80, 200, 55, "Neues Spiel", self.small_font)
		self.quit_button = Button(30, 150, 200, 55, "Beenden", self.small_font)

		# Animation und Effekte
		self.animations = []
		self.particles = []
		self.background_pattern = self._create_background_pattern()
		self.animation_time = 0

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
		"""Zeichnet das verbesserte Spielbrett"""
		# Zeichne animierten Hintergrund
		self.screen.blit(self.background_pattern, (0, 0))
		
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
		"""Zeichnet die verbesserten UI-Elemente"""
		# Rechtes UI-Panel mit verbesserter Größe und Position
		ui_rect = pygame.Rect(WINDOW_WIDTH - 380, 80, 350, 250)
		
		# Panel-Hintergrund mit stärkerem Kontrast
		panel_bg = pygame.Surface((ui_rect.width, ui_rect.height), pygame.SRCALPHA)
		draw_gradient_rect(panel_bg, pygame.Rect(0, 0, ui_rect.width, ui_rect.height), 
						  (35, 40, 60, 220), (55, 65, 85, 220))
		self.screen.blit(panel_bg, ui_rect.topleft)
		
		# Rand mit besserer Sichtbarkeit
		pygame.draw.rect(self.screen, (80, 90, 110), ui_rect, 3, border_radius=12)
		pygame.draw.rect(self.screen, (120, 130, 150), ui_rect, 1, border_radius=12)
		
		# Spieler-Info mit verbesserter Lesbarkeit
		player_text = "Schwarz" if self.game.current_player == Player.BLACK else "Weiß"
		player_color = (220, 220, 230) if self.game.current_player == Player.BLACK else (255, 255, 255)
		
		# Aktueller Spieler - größerer Text
		current_player_text = f"Am Zug:"
		player_name_text = f"{player_text}"
		
		# Header-Text
		header_shadow = self.font.render(current_player_text, True, (0, 0, 0, 180))
		header_text = self.font.render(current_player_text, True, (200, 210, 230))
		self.screen.blit(header_shadow, (ui_rect.x + 21, ui_rect.y + 21))
		self.screen.blit(header_text, (ui_rect.x + 20, ui_rect.y + 20))
		
		# Spielername - noch größer und farbig
		name_shadow = self.large_font.render(player_name_text, True, (0, 0, 0, 200))
		name_text = self.large_font.render(player_name_text, True, player_color)
		self.screen.blit(name_shadow, (ui_rect.x + 21, ui_rect.y + 51))
		self.screen.blit(name_text, (ui_rect.x + 20, ui_rect.y + 50))

		# Punktestand-Sektion mit besserer Strukturierung
		score_y_start = ui_rect.y + 100
		
		# "Punktestand" Titel
		score_title_shadow = self.font.render("Punktestand:", True, (0, 0, 0, 180))
		score_title = self.font.render("Punktestand:", True, (200, 210, 230))
		self.screen.blit(score_title_shadow, (ui_rect.x + 21, score_y_start + 1))
		self.screen.blit(score_title, (ui_rect.x + 20, score_y_start))
		
		# Schwarz Score
		black_score_text = f"Schwarz: {self.game.scores[Player.BLACK]}/6"
		black_shadow = self.font.render(black_score_text, True, (0, 0, 0, 200))
		black_score = self.font.render(black_score_text, True, (180, 180, 190))
		self.screen.blit(black_shadow, (ui_rect.x + 21, score_y_start + 31))
		self.screen.blit(black_score, (ui_rect.x + 20, score_y_start + 30))
		
		# Weiß Score
		white_score_text = f"Weiß: {self.game.scores[Player.WHITE]}/6"
		white_shadow = self.font.render(white_score_text, True, (0, 0, 0, 200))
		white_score = self.font.render(white_score_text, True, (255, 255, 255))
		self.screen.blit(white_shadow, (ui_rect.x + 21, score_y_start + 61))
		self.screen.blit(white_score, (ui_rect.x + 20, score_y_start + 60))
		
		# Score-Balken mit besserer Sichtbarkeit
		bar_width = 250
		bar_height = 12
		bar_x = ui_rect.x + 20
		
		# Schwarz Balken
		black_bar_rect = pygame.Rect(bar_x, score_y_start + 95, bar_width, bar_height)
		pygame.draw.rect(self.screen, (40, 45, 60), black_bar_rect, border_radius=6)
		pygame.draw.rect(self.screen, (70, 75, 90), black_bar_rect, 2, border_radius=6)
		
		black_progress = pygame.Rect(bar_x, score_y_start + 95, 
									(bar_width * self.game.scores[Player.BLACK]) // 6, bar_height)
		if black_progress.width > 0:
			pygame.draw.rect(self.screen, (120, 120, 140), black_progress, border_radius=6)
		
		# Weiß Balken
		white_bar_rect = pygame.Rect(bar_x, score_y_start + 115, bar_width, bar_height)
		pygame.draw.rect(self.screen, (40, 45, 60), white_bar_rect, border_radius=6)
		pygame.draw.rect(self.screen, (70, 75, 90), white_bar_rect, 2, border_radius=6)
		
		white_progress = pygame.Rect(bar_x, score_y_start + 115, 
									(bar_width * self.game.scores[Player.WHITE]) // 6, bar_height)
		if white_progress.width > 0:
			pygame.draw.rect(self.screen, (255, 255, 255), white_progress, border_radius=6)

		# Buttons mit mehr Abstand zum Panel
		self.new_game_button.draw(self.screen)
		self.quit_button.draw(self.screen)

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
			# Zeichne Brett (enthält jetzt Hintergrund)
			self.draw_board()

			# Zeichne Kugeln
			for hex_pos, player in self.game.board.items():
				if player != Player.EMPTY:
					selected = hex_pos in self.selected_marbles
					self.draw_marble(hex_pos, player, selected)

			# Zeichne Vorschau
			self.draw_preview()

			# Update und zeichne Partikel
			self.update_particles()
			self.draw_particles()

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