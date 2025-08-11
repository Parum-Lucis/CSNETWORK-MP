def print_board(board):
    """
    Prints a Tic Tac Toe board nicely formatted.
    Example:
       X | O |
      ---+---+---
         | X |
      ---+---+---
       O |   | X
    """
    print("\n")
    for i in range(3):
        row = " | ".join(board[i*3:(i+1)*3])
        print(f" {row} ")
        if i < 2:
            print("---+---+---")
    print("\n")
