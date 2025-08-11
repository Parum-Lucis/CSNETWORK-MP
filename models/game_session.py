import time
import uuid
from ui.display import print_board
from senders.game_move_unicast import send_game_move

# In-memory game state
games = {}

def start_game(local_profile, listener, game_id, opponent_user_id, my_symbol, first_turn):
    """
    Initializes a Tic Tac Toe game session and starts the game loop.
    """
    games[game_id] = {
        "board": [" "] * 9,
        "turn": 1,
        "my_symbol": my_symbol,
        "opponent_symbol": "O" if my_symbol == "X" else "X",
        "opponent_user_id": opponent_user_id,
        "listener": listener,
        "local_profile": local_profile,
        "my_turn": first_turn
    }

    print(f"🎮 Game {game_id} started against {opponent_user_id}. You are '{my_symbol}'.")
    game_loop(game_id)


def game_loop(game_id):
    """
    Main game loop for Tic Tac Toe.
    """
    game = games[game_id]

    while True:
        print_board(game["board"])
        if check_winner(game["board"]):
            print(f"🏆 Winner: {check_winner(game['board'])}")
            break
        if " " not in game["board"]:
            print("🤝 It's a draw!")
            break

        if game["my_turn"]:
            try:
                pos = int(input(f"Your move (0-8): "))
            except ValueError:
                print("Invalid input, try again.")
                continue

            if pos < 0 or pos > 8 or game["board"][pos] != " ":
                print("Invalid position, try again.")
                continue

            apply_move(game_id, pos, game["my_symbol"], send_over_network=True)
            game["my_turn"] = False
        else:
            print("⏳ Waiting for opponent...")
            time.sleep(1)  # Let the dispatcher handle incoming moves


def apply_move(game_id, position, symbol, send_over_network=False):
    """
    Applies a move to the board. Optionally sends it over the network.
    """
    game = games[game_id]
    game["board"][position] = symbol

    if send_over_network:
        send_game_move(
            game["local_profile"],
            game["listener"],
            game_id,
            game["opponent_user_id"],
            position,
            symbol,
            game["turn"]
        )
    game["turn"] += 1
    game["my_turn"] = not game["my_turn"]


def check_winner(board):
    """
    Checks if there's a winner and returns the symbol.
    """
    winning_lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
        (0, 4, 8), (2, 4, 6)              # diagonals
    ]
    for a, b, c in winning_lines:
        if board[a] == board[b] == board[c] != " ":
            return board[a]
    return None
