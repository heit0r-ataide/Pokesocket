import socket
import threading
from time import sleep

from protocol import READY, WAITING, START, ATTACK, TURN, WAIT_TURN

HOST = "127.0.0.1"
PORT = 5000

state = "WAITING_READY"


def receive_messages(client):

    global state

    while True:
        try:
            data = client.recv(1024)

            if not data:
                print("Servidor desconectou.")
                break

            message = data.decode("utf-8")

            if message == WAITING:

                state = "WAITING_PLAYER"

            elif message == START:

                state = "STARTING"

            elif message == TURN:

                state = "MY_TURN"

            elif message == WAIT_TURN:

                state = "OPPONENT_TURN"

            else:

                print(f"\nServidor: {message}")

        except ConnectionResetError:

            print("Conexão encerrada.")

            break


client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((HOST, PORT))

print("Conectado ao servidor!")

receive_thread = threading.Thread(
    target=receive_messages,
    args=(client,)
)

receive_thread.daemon = True
receive_thread.start()


while True:

    if state == "WAITING_READY":

        print("\n==============================")
        print("       AGUARDANDO INÍCIO")
        print("==============================")

        print("\n1 - Estou pronto")
        print("2 - Sair")

        option = input("> ")

        if option == "1":

            client.send(READY.encode("utf-8"))
            state = "WAITING_PLAYER"

        elif option == "2":

            break

        else:

            print("Opção inválida.")

    elif state == "WAITING_PLAYER":

        print("\n==============================")
        print("      AGUARDANDO JOGADOR")
        print("==============================")

        print("Aguardando o outro jogador...")

        while state == "WAITING_PLAYER":
            sleep(0.1)

    elif state == "STARTING":

        print("\n==============================")
        print("      BATALHA INICIANDO!")
        print("==============================")

        sleep(1)

        state = "WAITING_PLAYER"


    elif state == "MY_TURN":

        print("\n==============================")
        print("          SUA VEZ!")
        print("==============================")

        print("\nEscolha seu ataque:")

        print("\n1 - Ataque rápido (10 de dano)")
        print("2 - Ataque normal (20 de dano)")
        print("3 - Ataque forte (30 de dano)")
        print("4 - Ataque devastador (40 de dano)")
        print("\n5 - Sair")

        option = input("> ")

        if option in ["1", "2", "3", "4"]:
            client.send(f"{ATTACK}:{option}".encode("utf-8"))
            state = "OPPONENT_TURN"

        elif option == "5":
            break

        else:
            print("Opção inválida.")

    elif state == "OPPONENT_TURN":

        print("\n==============================")
        print("       VEZ DO ADVERSÁRIO")
        print("==============================")

        print("Aguardando o adversário...")

        while state == "OPPONENT_TURN":
            sleep(0.1)

client.close()
