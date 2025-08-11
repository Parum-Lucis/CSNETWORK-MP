import threading
from ui.display import print_board
from senders.game_move_unicast import send_game_move

games = {}

def start_game(local_profile, listener, game_id, opponent_user_id, my_symbol, first_turn):
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
    print_board(games[game_id]["board"])

    if games[game_id]["my_turn"]:
        prompt_move(game_id)
    else:
        print("⏳ Waiting for opponent to move...")

def prompt_move(game_id):
    """
    Ask the user for input in a separate thread so it doesn't block network listeners.
    """
    def get_move():
        while True:
            try:
                pos = int(input("Your move (0-8): "))
                game = games[game_id]
                if pos < 0 or pos > 8 or game["board"][pos] != " ":
                    print("Invalid position, try again.")
                    continue
                apply_move(game_id, pos, games[game_id]["my_symbol"], send_over_network=True)
                break
            except ValueError:
                print("Invalid input, try again.")

    thread = threading.Thread(target=get_move)
    thread.start()

def apply_move(game_id, position, symbol, send_over_network=False):
    game = games[game_id]
    game["board"][position] = symbol
    print_board(game["board"])

    winner = check_winner(game["board"])
    if winner:
        print(f"🏆 Winner: {winner}")
        # Handle game end logic here (cleanup, notify opponent, etc.)
        return
    elif " " not in game["board"]:
        print("🤝 It's a draw!")
        # Handle draw logic here
        return

    game["turn"] += 1
    game["my_turn"] = not game["my_turn"]

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

    if game["my_turn"]:
        print("⏳ Your turn.")
        prompt_move(game_id)
    else:
        print("⏳ Waiting for opponent...")

def receive_opponent_move(game_id, position, symbol):
    """
    Call this when a move message from opponent arrives.
    """
    apply_move(game_id, position, symbol, send_over_network=False)

def check_winner(board):
    winning_lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]
    for a, b, c in winning_lines:
        if board[a] == board[b] == board[c] != " ":
            return board[a]
    return None
