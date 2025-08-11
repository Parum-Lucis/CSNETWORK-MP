import sys
import time
import os
import questionary
import queue
import random
from queue import Queue
from ui.cli import process_pending_game_invites

import config
from models.peer import Profile
from utils.base64_utils import encode_image_to_base64
from utils.network_utils import get_local_ip
from storage.peer_directory import get_peers
from utils.printer import clear_screen
from utils.time_utils import wait_for_enter
from models.file_transfer import FileTransfer
from models.file_transfer import FileTransferResponder
from models.game_session import GameSession
from storage.game_directory import create_session, get_session, list_sessions, remove_session
from senders.game_responder import GameResponder
from storage import game_directory

# ===============================
# Queues shared with background handlers
# ===============================
pending_file_offers = Queue()  # For file offers requiring user action
pending_logs = Queue()         # For async logs (ACKs, file saved, warnings, etc.)

def launch_cli() -> Profile:
    """
    CLI prompt to create a new profile.
    """
    print("No saved profile found. Let's create one!\n")

    display_name = questionary.text("Enter your display name:").ask()
    user_id = f"{display_name.lower()}@{get_local_ip()}"

    avatar_type = None
    avatar_data = None

    use_avatar = questionary.confirm("Would you like to add an avatar?").ask()
    if use_avatar:
        avatar_path = questionary.path("Enter path to image file (PNG, JPG under 10KB):").ask()
        result = encode_image_to_base64(avatar_path)
        if result:
            avatar_type, avatar_data = result
        else:
            print("Failed to load avatar. Proceeding without it.")

    return Profile(
        user_id=user_id,
        ip=get_local_ip(),
        display_name=display_name,
        status="Online",
        avatar_type=avatar_type,
        avatar_data=avatar_data
    )

def file_form():
    """
    Prompts user for file location, name override, and description.
    """
    answers = {}
    try:
        while True:
            file_loc = questionary.text("Enter the file location").ask()

            if os.path.isfile(file_loc):
                answers["file_location"] = file_loc
                answers["file_name"] = questionary.text("Enter the file name to use (empty to use the default)").ask()
                answers["description"] = questionary.text("Enter the file description: ").ask()
            else:
                questionary.print("❌ The file entered does not exist.", style="bold fg:red")
                continue
            return answers
    except KeyboardInterrupt:
        return None

def flush_pending_logs():
    """Flush any logs from the pending_logs queue to the terminal immediately."""
    while not pending_logs.empty():
        log = pending_logs.get()
        questionary.print(log, style="fg:yellow")

def process_file_offer(msg, addr, udp):
    """
    Handles a pending file offer from the queue.
    """
    from_user = msg.get("FROM")
    file_name = msg.get("FILENAME")
    file_size = msg.get("FILESIZE")
    ip = addr[0]

    print(f"\n📥 File offer from {from_user}: {file_name} ({file_size} bytes)")

    accept = questionary.confirm("Accept file?").ask()
    if accept:
        from models.file_transfer import FileTransferResponder
        responder = FileTransferResponder(udp)
        responder.accept_file_offer(
            to_ip=ip,
            original_message_id=msg["MESSAGE_ID"]
        )
    else:
        print("❌ File offer declined.")

    # Flush any logs that may have appeared during this process
    flush_pending_logs()

def launch_main_menu(profile: Profile, udp):
    while True:
        # ✅ Flush background logs
        flush_pending_logs()
        process_pending_game_invites(udp, profile)

        # ✅ Process pending file offers before showing menu
        while not pending_file_offers.empty():
            msg, addr = pending_file_offers.get()
            process_file_offer(msg, addr, udp)

        status_note = "(Verbose ON)" if config.VERBOSE else ""

        choice = questionary.select(
            "Select an option:",
            choices=[
                "Post",
                "Check Feed",
                "Peer",
                "Group",
                "Notifications",
                "Terminate"
            ]
        ).ask()

        if choice == "Terminate":
            questionary.print("👋 Goodbye.", style="bold fg:green")
            time.sleep(1)
            sys.exit(0)

        elif choice == "Peer":
            selected = select_peer(profile)
            if selected:
                choice = peer_menu()

                if choice == "Send File":
                    file_result = file_form()
                    file_transfer = FileTransfer(
                        profile,
                        selected,
                        file_result["file_location"],
                        file_result["description"],
                        udp,
                        file_result["file_name"]
                    )
                    file_transfer.file_offer()

        else:
            continue

def select_peer(local_profile):
    """
    Shows a list of available peers and allows user to select one.
    """
    try:
        waiting = False
        while True:
            clear_screen()
            questionary.print("📡 Live Peer View (auto-refreshes every 3s)", style="bold")
            peers = get_peers(active_within=300)
            peers = [p for p in peers]

            if not peers:
                if not waiting:
                    waiting = True
                    questionary.print("😕 No other peers online. Waiting...", style="fg:yellow")
                time.sleep(3)
                continue

            waiting = False
            choices = [
                questionary.Choice(
                    title=f"{peer.display_name} ({peer.status}) @ {peer.ip}",
                    value=peer
                ) for peer in peers
            ]
            choices.append("↩ Return to menu")

            selected = questionary.select(
                "📡 Choose a peer to connect:",
                choices=choices
            ).ask()

            if selected == "↩ Return to menu" or selected is None:
                return None
            return selected
    except KeyboardInterrupt:
        return None

def peer_menu():
    """
    Menu for selecting operations for a specific peer.
    """
    while True:
        choice = questionary.select(
            "Select an operation to run:",
            choices=[
                "DM",
                "Follow",
                "Unfollow",
                "Send File",
                "↩ Return to menu"
            ]
        ).ask()

        if choice == "↩ Return to menu" or choice is None:
            return None
        return choice

# TicTacToe notification queues (non-blocking)
pending_game_invites = Queue()
pending_game_logs = Queue()

def _choose_peer_ip(peers):
    if not peers:
        print("No known peers.")
        return None, None
    for i, p in enumerate(peers):
        print(f"{i+1}. {p}")
    idx = input("Select peer number: ").strip()
    if not idx.isdigit() or not (1 <= int(idx) <= len(peers)):
        print("Invalid selection.")
        return None, None
    sel = peers[int(idx) - 1]
    ip = sel.rsplit("@", 1)[1] if "@" in sel else None
    return sel, ip

def _select_game(games):
    if not games:
        print("No active games.")
        return None
    for i, g in enumerate(games):
        gid = g.game_id if hasattr(g, "game_id") else g.get("game_id")
        print(f"{i+1}. {gid} | status={g.status} | turn={g.turn}")
    idx = input("Select game number: ").strip()
    if not idx.isdigit() or not (1 <= int(idx) <= len(games)):
        print("Invalid selection.")
        return None
    chosen = games[int(idx) - 1]
    return chosen.game_id if hasattr(chosen, "game_id") else chosen.get("game_id")

def _prompt_position():
    pos = input("Enter move position (0-8, top-left=0): ").strip()
    if not pos.isdigit():
        print("Invalid position.")
        return None
    pos = int(pos)
    if pos < 0 or pos > 8:
        print("Position must be 0..8")
        return None
    return pos

def process_pending_game_invites(listener, local_profile):
    """Call this periodically from your main UI loop to surface invites to the user."""
    responder = GameResponder(listener, local_profile.user_id, local_profile.ip)

    while not pending_game_invites.empty():
        try:
            msg, addr = pending_game_invites.get_nowait()
        except queue.Empty:
            return
        inviter = msg.get("FROM")
        gameid = msg.get("GAMEID")
        symbol = (msg.get("SYMBOL") or "X").upper()
        print()  # newline for clarity
        print(f"{inviter} is inviting you to play tic-tac-toe (game {gameid}).")
        accept = input("Accept invite? (y/n): ").strip().lower()
        if accept == "y":
            # create local session (assign symbols accordingly)
            if symbol == "X":
                p_x, p_o = inviter, local_profile.user_id
                px_ip, po_ip = addr[0], local_profile.ip
            else:
                p_x, p_o = local_profile.user_id, inviter
                px_ip, po_ip = local_profile.ip, addr[0]
            session = GameSession(game_id=gameid, player_x=p_x, player_o=p_o, player_x_ip=px_ip, player_o_ip=po_ip)
            session.assign_symbols(inviter, symbol)
            create_session(session)
            print("Invite accepted. Game created locally.")
            # Optionally respond (ACK already sent by handler). No extra RFC message required.
        else:
            print("Invite declined.")

def ttt_menu(listener, local_profile, peers_lookup_fn):
    """
    Interactive TicTacToe submenu.
    - `peers_lookup_fn()` should return a list of peer user_id strings (e.g., ['bob@192.168.1.12']).
    """
    responder = GameResponder(listener, local_profile.user_id, local_profile.ip)

    while True:
        print("\nTicTacToe menu")
        print("1) Invite peer")
        print("2) List my games")
        print("3) Make move")
        print("4) Forfeit game")
        print("0) Back")
        choice = input("Choose: ").strip()

        if choice == "1":
            peers = peers_lookup_fn()
            to_user, to_ip = _choose_peer_ip(peers)
            if not to_user or not to_ip:
                continue
            symbol = input("Choose your symbol (X or O) — this will be the inviter's symbol: ").strip().upper()
            if symbol not in ("X", "O"):
                print("Defaulting to X")
                symbol = "X"
            game_id = f"g{random.randint(0,255)}"
            mid = responder.send_invite(to_ip=to_ip, to_user=to_user, game_id=game_id, symbol=symbol)
            print(f"Sent invite {game_id} (MESSAGE_ID: {mid}) to {to_user}")

        elif choice == "2":
            games = list_sessions()
            if not games:
                print("No active games.")
                continue
            for g in games:
                print(f"- {g.game_id} | status={g.status} | turn={g.turn}")

        elif choice == "3":
            games = list_sessions()
            gid = _select_game(games)
            if not gid:
                continue
            session = get_session(gid)
            if not session:
                print("Selected game not found.")
                continue
            opponent = session.other_player(local_profile.user_id)
            if not opponent:
                print("Cannot determine opponent for this game.")
                continue
            opponent_ip = opponent.rsplit("@", 1)[1] if "@" in opponent else None
            pos = _prompt_position()
            if pos is None:
                continue
            next_turn = session.turn + 1
            my_symbol = session.symbol_of.get(local_profile.user_id)
            if not my_symbol:
                print("Your symbol not assigned — cannot move.")
                continue
            ok = session.apply_move(user_id=local_profile.user_id, position=pos, symbol=my_symbol, turn_number=next_turn)
            if not ok:
                print("Move invalid locally (position occupied or turn mismatch).")
                continue
            mid = responder.send_move(
                to_ip=opponent_ip,
                to_user=opponent,
                game_id=gid,
                position=pos,
                symbol=my_symbol,
                turn=next_turn
            )
            print(f"Sent move (MESSAGE_ID: {mid}) for game {gid} pos {pos} turn {next_turn}")
            outcome = session.check_winner()
            if outcome:
                if outcome.get("result") == "WIN":
                    wl = outcome.get("line")
                    print("You WIN locally — sending RESULT to opponent.")
                    responder.send_result(to_ip=opponent_ip, to_user=opponent, game_id=gid, result="WIN", symbol=my_symbol, winning_line=wl)
                    remove_session(gid)
                elif outcome.get("result") == "DRAW":
                    print("Game DRAW locally — notifying opponent.")
                    responder.send_result(to_ip=opponent_ip, to_user=opponent, game_id=gid, result="DRAW", symbol=my_symbol)
                    remove_session(gid)

        elif choice == "4":
            games = list_sessions()
            gid = _select_game(games)
            if not gid:
                continue
            session = get_session(gid)
            if not session:
                print("Selected game not found.")
                continue
            opponent = session.other_player(local_profile.user_id)
            opponent_ip = opponent.rsplit("@", 1)[1] if "@" in opponent else None
            my_symbol = session.symbol_of.get(local_profile.user_id)
            responder.send_result(to_ip=opponent_ip, to_user=opponent, game_id=gid, result="FORFEIT", symbol=my_symbol)
            remove_session(gid)
            print(f"Sent FORFEIT for game {gid}")

        elif choice == "0":
            break

        else:
            print("Unknown choice. Try again.")
