from game import Game

import socket
import threading

from protocol import READY, WAITING, START, ATTACK, TURN, WAIT_TURN, WAIT_ACTION, NAME, format_message, normalize_message


HOST = "0.0.0.0"
PORT = 5000

clients = []
ready_players = set()
player_names = {}

game = Game()

lock = threading.Lock()


def reset_match_state():
    global game
    game = Game()
    ready_players.clear()


def send_message(client, message):
    try:
        client.send(format_message(message).encode("utf-8"))
    except (BrokenPipeError, ConnectionResetError, OSError):
        try:
            client.close()
        except Exception:
            pass
        raise


def get_player_label(conn, fallback_index):
    return player_names.get(conn, f"Jogador {fallback_index + 1}")


def send_player_status(client, player_index):
    if not game.started or player_index >= len(game.players):
        return

    current = game.players[player_index]
    opponent_index = 1 - player_index
    opponent = game.players[opponent_index]

    payload = (
        f"STATUS:{current.hp}:{current.stamina}:{opponent.hp}:{opponent.stamina}"
    )
    send_message(client, payload)


def broadcast(message):
    for client in clients:
        try:
            send_message(client, message)
        except Exception:
            pass


def broadcast_status():
    for index, client in enumerate(clients):
        try:
            send_player_status(client, index)
        except Exception:
            pass


def handle_client(conn, addr):
    print(f"Cliente conectado: {addr}")

    with lock:
        clients.append(conn)
        player_index = len(clients) - 1

    try:
        buffer = ""

        while True:
            data = conn.recv(1024)

            if not data:
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1)
                message = normalize_message(message)

                if not message:
                    continue

                print(f"Jogador {player_index + 1}: {message}")

                if message.startswith(f"{NAME}:"):
                    chosen_name = message.split(":", 1)[1].strip() or f"Jogador {player_index + 1}"
                    with lock:
                        player_names[conn] = chosen_name
                    print(f"Nome do jogador {player_index + 1}: {chosen_name}")
                    continue

                if message == READY:
                    with lock:
                        if conn in ready_players:
                            print(f"Jogador {player_index + 1} já está pronto.")
                            continue

                        ready_players.add(conn)

                        print(f"Jogadores prontos: {len(ready_players)}/{len(clients)}")

                        if len(ready_players) == 1:
                            send_message(conn, WAITING)
                        elif len(ready_players) == 2:
                            names = [
                                get_player_label(client, idx)
                                for idx, client in enumerate(clients[:2])
                            ]

                            reset_match_state()
                            game.add_player(names[0])
                            game.add_player(names[1])
                            game.start()
                            ready_players.clear()

                            print("Partida iniciada!")

                            broadcast(START)
                            broadcast_status()
                        else:
                            send_message(conn, WAITING)

                elif message.startswith(f"{ATTACK}:"):
                    try:
                        attack_key = int(message.split(":", 1)[1])
                    except (IndexError, ValueError):
                        print("Ataque inválido.")
                        continue

                    with lock:
                        if not game.started:
                            print("A partida ainda não começou")
                            continue

                        if attack_key not in game.attacks:
                            print("Ataque inexistente.")
                            continue

                        if not game.can_attack(player_index, attack_key):
                            try:
                                send_message(conn, "Stamina insuficiente!")
                            except Exception:
                                pass
                            continue

                        action_ready = game.submit_action(player_index, attack_key)

                    if not action_ready:
                        try:
                            send_message(conn, WAIT_ACTION)
                        except Exception:
                            break
                        print(f"Jogador {player_index + 1} aguardando o oponente escolher ataque.")
                        continue

                    resolved = False
                    with lock:
                        if len(game.pending_actions) >= 2:
                            resolved = game.resolve_round()

                    if resolved:
                        print("Rodada resolvida simultaneamente.")
                        try:
                            broadcast_status()
                        except Exception:
                            pass

                        if game.is_game_over():
                            try:
                                broadcast("GAME_OVER")
                            except Exception:
                                pass
                            print("Partida terminou")
                            break

                        for client in list(clients):
                            try:
                                send_message(client, START)
                            except Exception:
                                pass
                else:
                    print("Mensagem desconhecida")

    except ConnectionResetError:
        print(f"Cliente desconectado: {addr}")

    finally:
        if conn in clients:
            clients.remove(conn)
        player_names.pop(conn, None)
        ready_players.discard(conn)

        if len(clients) < 2:
            reset_match_state()

        conn.close()
        print(f"Conexão encerrada: {addr}")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((HOST, PORT))
server.listen()

print(f"Servidor iniciado na porta {PORT}")
print("Aguardando conexões...")

while True:
    conn, addr = server.accept()

    thread = threading.Thread(
        target=handle_client,
        args=(conn, addr)
    )

    thread.start()
