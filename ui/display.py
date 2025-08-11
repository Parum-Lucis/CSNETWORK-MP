def print_board_colored(board: list):
    """Render a 3x3 board with minimal ANSI coloring to match existing display style."""
    def cell(v):
        return v if v is not None else " "

    def colorize(val):
        if val == "X":
            return f"\x1b[31m{val}\x1b[0m"  # red for X
        if val == "O":
            return f"\x1b[36m{val}\x1b[0m"  # cyan for O
        return val

    rows = [
        f" {colorize(cell(board[0]))} | {colorize(cell(board[1]))} | {colorize(cell(board[2]))} ",
        f" {colorize(cell(board[3]))} | {colorize(cell(board[4]))} | {colorize(cell(board[5]))} ",
        f" {colorize(cell(board[6]))} | {colorize(cell(board[7]))} | {colorize(cell(board[8]))} ",
    ]
    sep = "\n-----------\n"
    print(rows[0] + sep + rows[1] + sep + rows[2])
