# Abalone

A complete implementation of the classic Abalone board game in Python using pygame.

## About

Abalone is a strategic board game for two players, played on a hexagonal board with marbles. The objective is to push six of your opponent's marbles off the board to win. This implementation features a beautiful graphical interface with Material Design colors and smooth gameplay.

## Features

- **Complete Abalone gameplay** with all official rules
- **Hexagonal board** with accurate coordinate system
- **Three types of moves**: single marble, inline (pushing), and broadside
- **Sumito mechanics** - push opponent marbles with numerical superiority
- **Visual feedback** with hover effects and move previews
- **Material Design UI** with modern colors and smooth animations
- **Real-time scoring** and turn indication

## Installation

1. Make sure Python 3.6+ is installed
2. Install pygame:
```bash
pip install pygame
```

## Usage

Run the game:
```bash
python abalone.py
```

### How to Play

1. **Objective**: Push 6 opponent marbles off the board
2. **Marble Selection**: Click on your marbles to select them (up to 3 in a line)
3. **Movement**: Click on a highlighted valid move position
4. **Move Types**:
   - **Single**: Move one marble to an adjacent empty space
   - **Inline**: Move 2-3 marbles in their line direction, can push opponents
   - **Broadside**: Move 2-3 marbles sideways (perpendicular to their line)
5. **Pushing (Sumito)**: You can push opponent marbles when you outnumber them
6. **Winning**: First player to score 6 points (push 6 opponent marbles off) wins

### Controls

- **Mouse**: Click to select marbles and make moves
- **New Game**: Reset the game at any time
- **Quit**: Exit the application

## Game Rules

- Players alternate turns (Black starts first)
- You can move 1, 2, or 3 of your marbles per turn
- Multiple marbles must be in a straight line to move together
- You can push opponent marbles if you outnumber them (2v1 or 3v2)
- Marbles pushed off the board score points for the pushing player
- First to 6 points wins

## Technical Details

- **Coordinate System**: Uses axial coordinates for hexagonal board representation
- **Move Validation**: Comprehensive rule checking for all move types
- **Rendering**: Smooth graphics with pygame, including transparency effects
- **Architecture**: Clean separation between game logic and UI

## License

MIT License

Copyright (c) 2025 Martin Pfeffer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Developer

**Martin Pfeffer** - 2025