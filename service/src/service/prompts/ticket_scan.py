"""Vision prompt for Lotofácil ticket scanning."""

TICKET_SCAN_PROMPT = """\
You are analysing a photograph of a Lotofácil lottery ticket.

You have been given TWO images:
- Image 1: the BLANK reference ticket (no marks, all cells clean).
- Image 2: the FILLED ticket photographed by the player.

TICKET STRUCTURE:
Each game grid has a 5 × 5 matrix. The number printed in each cell is FIXED and never changes.
Use the table below to map every cell position to its number — do NOT try to read the digit
(it may be covered by ink):

  Row\Col  C1   C2   C3   C4   C5
  Row 1    21   16   11   06   01
  Row 2    22   17   12   07   02
  Row 3    23   18   13   08   03
  Row 4    24   19   14   09   04
  Row 5    25   20   15   10   05

YOUR TASK:
Compare Image 2 (filled) against Image 1 (blank). A cell is MARKED when it shows additional
ink (stroke, cross, circle, scribble, fill) that is not present in the blank reference.
Use the position table above to identify which number each marked cell corresponds to.

- Do NOT read the printed digit; use cell (row, col) position to look up the number.
- Do NOT report a cell as marked if it looks the same as in the blank reference.
- If you are uncertain about a specific cell, leave it unmarked.

OUTPUT:
Return ONLY a JSON object — no prose, no markdown, no explanation:
{"games": [[n, n, n, ...], [n, n, n, ...]]}

Each inner array is the sorted list of marked integers for one game grid.
Omit any grid that has no ink marks.
If you cannot determine which cells are marked, return: {"games": []}

EXAMPLE — a ticket with two filled grids might look like:
{"games": [[3, 7, 9, 14, 18, 20, 22], [1, 5, 8, 11, 16, 19, 23, 25]]}
"""
