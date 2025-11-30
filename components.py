"""
Core game logic for Minesweeper.

This module contains pure domain logic without any pygame or pixel-level
concerns. It defines:
- CellState: the state of a single cell
- Cell: a cell positioned by (col,row) with an attached CellState
- Board: grid management, mine placement, adjacency computation, reveal/flag

The Board exposes imperative methods that the presentation layer (run.py)
can call in response to user inputs, and does not know anything about
rendering, timing, or input devices.
"""

import random
from typing import List, Tuple


class CellState:
    """Mutable state of a single cell.

    Attributes:
        is_mine: Whether this cell contains a mine.
        is_revealed: Whether the cell has been revealed to the player.
        is_flagged: Whether the player flagged this cell as a mine.
        adjacent: Number of adjacent mines in the 8 neighboring cells.
    """

    def __init__(self, is_mine: bool = False, is_revealed: bool = False, is_flagged: bool = False, adjacent: int = 0):
        self.is_mine = is_mine
        self.is_revealed = is_revealed
        self.is_flagged = is_flagged
        self.adjacent = adjacent


class Cell:
    """Logical cell positioned on the board by column and row."""

    def __init__(self, col: int, row: int):
        self.col = col
        self.row = row
        self.state = CellState()


class Board:
    """Minesweeper board state and rules.

    Responsibilities:
    - Generate and place mines with first-click safety
    - Compute adjacency counts for every cell
    - Reveal cells (iterative flood fill when adjacent == 0)
    - Toggle flags, check win/lose conditions
    """

    def __init__(self, cols: int, rows: int, mines: int):
        self.cols = cols
        self.rows = rows
        self.num_mines = mines
        self.cells: List[Cell] = [Cell(c, r) for r in range(rows) for c in range(cols)]
        self._mines_placed = False
        self.revealed_count = 0
        self.game_over = False
        self.win = False

    def index(self, col: int, row: int) -> int:
        """Return the flat list index for (col,row)."""
        return row * self.cols + col

    def is_inbounds(self, col: int, row: int) -> bool:
        # TODO: Return True if (col,row) is inside the board bounds.
        # 해결
        return 0 <= col < self.cols and 0 <= row < self.rows
        pass

    def neighbors(self, col: int, row: int) -> List[Tuple[int, int]]:
        # TODO: Return list of valid neighboring coordinates around (col,row).
        # 해결
        deltas = [
            (-1, -1), (0, -1), (1, -1),
            (-1, 0),            (1, 0),
            (-1, 1),  (0, 1),  (1, 1),
        ]
        result = []
        for dx, dy in deltas:
            nx, ny = col + dx, row + dy
            if self.is_inbounds(nx, ny):
                result.append((nx, ny))
        return result
        pass

    def place_mines(self, safe_col: int, safe_row: int) -> None:
        # TODO: Place mines randomly, guaranteeing the first click and its neighbors are safe. And Compute adjacency counts        
        #지뢰를 놓을 수 있는 모든 좌표 리스트 생성
        all_positions = [(c, r) for r in range(self.rows) for c in range(self.cols)]
        
        #첫 클릭한 곳과 그 주변은 지뢰 금지 구역으로 설정
        forbidden = {(safe_col, safe_row)} | set(self.neighbors(safe_col, safe_row))
        
        #금지 구역을 뺀 나머지 좌표 중에서 랜덤으로 지뢰 개수만큼 뽑기
        pool = [p for p in all_positions if p not in forbidden]
        mine_positions = random.sample(pool, self.num_mines)

        #지뢰 배치
        for c, r in mine_positions:
            idx = self.index(c, r)
            self.cells[idx].state.is_mine = True

        #각 셀마다 주변에 지뢰가 몇 개인지 계산
        for r in range(self.rows):
            for c in range(self.cols):
                idx = self.index(c, r)
                if self.cells[idx].state.is_mine:
                    continue #지뢰 칸은 계산 안 함
                
                #주변 지뢰 개수 세기
                count = 0
                for nc, nr in self.neighbors(c, r):
                    n_idx = self.index(nc, nr)
                    if self.cells[n_idx].state.is_mine:
                        count += 1
                self.cells[idx].state.adjacent = count

        self._mines_placed = True

    def reveal(self, col: int, row: int) -> None:
        # TODO: Reveal a cell; if zero-adjacent, iteratively flood to neighbors.
        if not self.is_inbounds(col, row):
            return
        
        # 첫 클릭이라면 지뢰 배치부터 수행
        if not self._mines_placed:
            self.place_mines(col, row)

        idx = self.index(col, row)
        cell = self.cells[idx]

        # 이미 열렸거나 깃발이 꽂혀있으면 무시
        if cell.state.is_revealed or cell.state.is_flagged:
            return

        # 셀 오픈
        cell.state.is_revealed = True
        self.revealed_count += 1

        # 지뢰를 밟았을 경우 -> 게임 오버
        if cell.state.is_mine:
            self.game_over = True
            self._reveal_all_mines()
            return

        # 주변에 지뢰가 하나도 없는(0) 칸이라면, 주변 칸들도 자동으로 엽니다 (재귀/Flood fill)
        if cell.state.adjacent == 0:
            for nc, nr in self.neighbors(col, row):
                self.reveal(nc, nr)
        
        # 승리 조건 체크
        self._check_win()

    def toggle_flag(self, col: int, row: int) -> None:
        # TODO: Toggle a flag on a non-revealed cell.
        if not self.is_inbounds(col, row):
            return
        
        idx = self.index(col, row)
        cell = self.cells[idx]

        # 이미 열린 칸에는 깃발을 꽂을 수 없음
        if not cell.state.is_revealed:
            cell.state.is_flagged = not cell.state.is_flagged

    def flagged_count(self) -> int:
        # TODO: Return current number of flagged cells.
        pass

    def _reveal_all_mines(self) -> None:
        """Reveal all mines; called on game over."""
        for cell in self.cells:
            if cell.state.is_mine:
                cell.state.is_revealed = True

    def _check_win(self) -> None:
        """Set win=True when all non-mine cells have been revealed."""
        total_cells = self.cols * self.rows
        if self.revealed_count == total_cells - self.num_mines and not self.game_over:
            self.win = True
            for cell in self.cells:
                if not cell.state.is_revealed and not cell.state.is_mine:
                    cell.state.is_revealed = True





