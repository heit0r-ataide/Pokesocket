from game import Game

import socket
import threading

from protocol import READY, WAITING, START, ATTACK, TURN, WAIT_TURN



HOST = "0.0.0.0"
PORT = 5000

clients = []
ready_players = set()

game = Game()

lock = threading.Lock()

def send_message(client, message):
    client.send(message.encode("utf-8"))

def broadcast(message):
    for client in clients:
        try:
            send_message(client, message)
        except:
            pass

def handle_client(conn, addr):
    print(f"Cliente conectado: {addr}")

    with lock:
        clients.append(conn)
        player_index = len(clients) - 1

    try:
        while True:
            data = conn.recv(1024)

            if not data:
                break

            message = data.decode("utf-8")

            print(f"Jogador {player_index + 1}: {message}")

            if message == READY:

                with lock:
                    if conn in ready_players:
                        print(f"Jogador {player_index + 1} já está pronto.")
                        continue

                    ready_players.add(conn)

                    print("Jogadores prontos:"
                           f"{len(ready_players)}/{len(clients)}"
                    )
                    
                    if len(ready_players) == 1:
                        send_message(conn, WAITING)

                    elif len(ready_players) == 2:
                        game.add_player("Jogador 1")
                        game.add_player("Jogador 2")

                        game.start()

                        print("Partida iniciada!")

                        broadcast(START)

                        send_message(clients[game.turn], TURN)
                        send_message(clients[1 - game.turn], WAIT_TURN)

                    else:
                        conn.send(WAITING.encode("utf-8"))

            elif message.startswith(ATTACK+":"):

                with lock:
                    if not game.started:
                        print("A partida ainda não começou")
                        continue
                    if player_index != game.turn:

                        print(
                            f"Jogador {player_index + 1}"
                            f"Tentou o atacar fora do turno"
                        )
                        continue
                    try:
                        attack_key = int(message.split(":")[1])

                    except (IndexError, ValueError):
                        print("Ataque inválido.")
                        continue

                    if attack_key not in game.attacks:
                        print("Ataque inexistente.")
                        continue

                hp = game.attack(player_index, attack_key)

                if hp is None:
                    send_message(conn, "Stamina insuficiente!")
                    continue

                attack_name = game.attacks[attack_key]["name"]
                damage = game.attacks[attack_key]["damage"]

                print("Dano causado:", damage)
                print(
                    f"Jogador {player_index + 1} usou {attack_name}"
                )
                print(f"HP do adversário: {hp}")

                if game.is_game_over():
                    broadcast("GAME_OVER")
                    print("Partida terminou")
                    break

                game.next_turn()

                send_message(clients[game.turn], TURN)
                send_message(clients[1 - game.turn], WAIT_TURN)
            
            else:
                print("Mensagem desconhecida")

    except ConnectionResetError:
        print(f"Cliente desconectado: {addr}")

    finally:
        if conn in clients:
            clients.remove(conn)

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
