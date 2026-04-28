"""Vision prompt for Lotofácil ticket scanning."""

TICKET_SCAN_PROMPT = """\
You are analysing a photograph of a Lotofácil lottery ticket.

TICKET STRUCTURE:
Each game grid contains the numbers 01 through 25 arranged in a 5 × 5 matrix.
Every cell has a printed number. A player marks cells by drawing a pen stroke, cross (X),
circle, scribble, or any visible ink over or through the printed number.

YOUR TASK:
Identify which cells have been physically marked with ink in each game grid.
- A MARKED cell: has a pen stroke, cross, circle, fill, or any ink on top of the printed number.
- An UNMARKED cell: shows only the clean printed number with no additional ink on it.

Do NOT report cells that are merely printed and visible — only report cells with additional ink marks on them. Do not guess or infer.

OUTPUT:
Return ONLY a JSON object with no prose, no markdown, no explanation:
{"games": [[n, n, n, ...], [n, n, n, ...]]}

Each inner array is the sorted list of marked integers for one game grid.
Omit any grid that has no ink marks.
If you cannot determine which cells are marked, return: {"games": []}

EXAMPLE — a ticket with two filled grids might look like:
{"games": [[3, 7, 9, 14, 18, 20, 22], [1, 5, 8, 11, 16, 19, 23, 25]]}
"""
