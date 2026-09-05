import os
import queue
import socket
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox

from protocol import READY, WAITING, START, ATTACK, CHAT, TURN, WAIT_TURN, WAIT_ACTION, NAME, format_message, normalize_message

HOST = "127.0.0.1"
PORT = 5000


class BattleClient:
    ATTACKS = {
        1: {"name": "Ataque rápido", "stamina": 0},
        2: {"name": "Ataque normal", "stamina": 15},
        3: {"name": "Ataque forte", "stamina": 30},
        4: {"name": "Ataque devastador", "stamina": 50},
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Batalha por Turnos")
        self.root.geometry("780x560")
        self.root.configure(bg="#111827")

        self.client = None
        self.connected = False
        self.state = "WAITING_NAME"
        self.buffer = ""

        self.player_name = "Jogador"
        self.player_hp = 100
        self.player_stamina = 100
        self.opponent_hp = 100
        self.opponent_stamina = 100
        self.speech_queue = queue.Queue()

        self.setup_ui()
        self.speech_thread = threading.Thread(target=self.speech_loop, daemon=True)
        self.speech_thread.start()
        self.update_ui()

    def setup_ui(self):
        self.main = tk.Frame(self.root, bg="#111827", padx=20, pady=20)
        self.main.pack(fill="both", expand=True)

        self.title = tk.Label(
            self.main,
            text="Batalha por Turnos",
            font=("Arial", 20, "bold"),
            fg="#f3f4f6",
            bg="#111827",
        )
        self.title.pack(pady=(0, 10))

        self.name_frame = tk.Frame(self.main, bg="#111827")
        self.name_frame.pack(fill="x", pady=(0, 12))

        tk.Label(self.name_frame, text="Seu nome:", fg="#f3f4f6", bg="#111827").pack(side="left")
        self.name_var = tk.StringVar(value="Jogador")
        self.name_entry = tk.Entry(self.name_frame, textvariable=self.name_var, width=28, font=("Arial", 12))
        self.name_entry.pack(side="left", padx=(8, 8))

        self.connect_btn = tk.Button(
            self.name_frame,
            text="Entrar na partida",
            command=self.connect_and_join,
            bg="#2563eb",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=16,
            pady=8,
        )
        self.connect_btn.pack(side="left")

        self.ready_btn = tk.Button(
            self.main,
            text="Estou pronto",
            command=self.send_ready,
            bg="#16a34a",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=16,
            pady=8,
            state="disabled",
        )
        self.ready_btn.pack(pady=(0, 16))

        self.chat_frame = tk.Frame(self.main, bg="#111827")
        self.chat_frame.pack(fill="x", pady=(0, 12))

        self.chat_var = tk.StringVar()
        self.chat_entry = tk.Entry(self.chat_frame, textvariable=self.chat_var, font=("Arial", 11))
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.chat_entry.bind("<Return>", self.send_chat)

        self.chat_btn = tk.Button(
            self.chat_frame,
            text="Enviar mensagem",
            command=self.send_chat,
            bg="#0891b2",
            fg="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=12,
            pady=8,
            state="disabled",
        )
        self.chat_btn.pack(side="left")

        self.status_container = tk.Frame(self.main, bg="#1f2937", padx=16, pady=12)
        self.status_container.pack(fill="x", pady=(0, 12))

        self.player_status = tk.StringVar(value="Você: HP 100 | Stamina 100")
        self.opponent_status = tk.StringVar(value="Adversário: HP 100 | Stamina 100")

        tk.Label(self.status_container, textvariable=self.player_status, fg="#d1fae5", bg="#1f2937", font=("Arial", 12, "bold")).pack(anchor="w")
        tk.Label(self.status_container, textvariable=self.opponent_status, fg="#fee2e2", bg="#1f2937", font=("Arial", 12, "bold")).pack(anchor="w", pady=(6, 0))

        self.attack_frame = tk.LabelFrame(self.main, text="Escolha seu ataque", bg="#1f2937", fg="#f3f4f6", font=("Arial", 11, "bold"))
        self.attack_frame.pack(fill="x", pady=(0, 10))

        self.attack_grid = tk.Frame(self.attack_frame, bg="#1f2937")
        self.attack_grid.pack(fill="x", padx=8, pady=8)

        self.attack_buttons = {}
        for row in range(2):
            for col in range(2):
                attack_key = (row * 2) + col + 1
                attack_data = self.ATTACKS.get(attack_key)
                if attack_data is None:
                    continue

                button = tk.Button(
                    self.attack_grid,
                    text=f"{attack_data['name']}\n({attack_data['stamina']} stamina)",
                    command=lambda key=attack_key: self.send_attack(key),
                    bg="#374151",
                    fg="white",
                    font=("Arial", 11, "bold"),
                    relief="flat",
                    width=18,
                    height=3,
                    state="disabled",
                    padx=10,
                    pady=10,
                    justify="center",
                )
                button.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
                self.attack_buttons[attack_key] = button

        for col in range(2):
            self.attack_grid.grid_columnconfigure(col, weight=1)
        for row in range(2):
            self.attack_grid.grid_rowconfigure(row, weight=1)

        self.log_box = tk.Text(self.main, height=10, state="disabled", bg="#0f172a", fg="#e2e8f0", font=("Arial", 10))
        self.log_box.pack(fill="both", expand=True)

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")

    def speech_loop(self):
        while True:
            message = self.speech_queue.get()
            if sys.platform != "win32":
                continue

            environment = os.environ.copy()
            environment["BATTLE_CHAT_TEXT"] = message
            speech_script = (
                "$voice = New-Object -ComObject SAPI.SpVoice; "
                "$voice.Volume = 100; "
                "$voice.Rate = 0; "
                "$voice.Speak($env:BATTLE_CHAT_TEXT)"
            )
            try:
                result = subprocess.run(
                    ["powershell.exe", "-NoProfile", "-STA", "-Command", speech_script],
                    env=environment,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    check=False,
                )
                if result.returncode != 0:
                    self.root.after(0, self.log, "Não foi possível reproduzir a voz.")
            except OSError:
                self.root.after(0, self.log, "PowerShell não está disponível para reproduzir a voz.")

    def update_status(self):
        self.player_status.set(f"Você: HP {self.player_hp} | Stamina {self.player_stamina}")
        self.opponent_status.set(f"Adversário: HP {self.opponent_hp} | Stamina {self.opponent_stamina}")

    def update_ui(self):
        connected_ready = self.connected and self.state in {"WAITING_PLAYER", "WAITING_READY"}
        self.ready_btn.config(state="normal" if connected_ready else "disabled")

        can_attack = self.connected and self.state in {"READY", "MY_TURN"}
        for button in self.attack_buttons.values():
            button.config(state="normal" if can_attack else "disabled")

        can_chat = self.connected and self.state in {"READY", "MY_TURN", "WAITING_ACTION"}
        self.chat_entry.config(state="normal" if can_chat else "disabled")
        self.chat_btn.config(state="normal" if can_chat else "disabled")

    def connect_and_join(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Nome obrigatório", "Digite um nome para continuar.")
            return

        self.player_name = name

        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((HOST, PORT))
            self.client.settimeout(0.2)
            self.connected = True
            self.log(f"Conectado ao servidor como {self.player_name}.")
            self.send_message(f"{NAME}:{self.player_name}")
            self.state = "WAITING_READY"
            self.update_ui()

            self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
            self.receive_thread.start()
        except OSError as exc:
            messagebox.showerror("Erro de conexão", f"Não foi possível conectar ao servidor: {exc}")

    def send_message(self, message):
        if self.client is None:
            return
        self.client.send(format_message(message).encode("utf-8"))

    def send_ready(self):
        if not self.connected:
            return
        self.send_message(READY)
        self.state = "WAITING_PLAYER"
        self.log("Você entrou na fila. Aguardando outro jogador...")
        self.update_ui()

    def send_attack(self, attack_key):
        if self.state not in {"READY", "MY_TURN"}:
            return

        self.send_message(f"{ATTACK}:{attack_key}")
        self.state = "WAITING_ACTION"
        self.log(f"Ataque enviado: {self.ATTACKS[attack_key]['name']}")
        self.update_ui()

    def send_chat(self, _event=None):
        if not self.connected:
            return "break"

        text = self.chat_var.get().strip()
        if not text:
            return "break"

        self.send_message(f"{CHAT}:{text[:200]}")
        self.chat_var.set("")
        return "break"

    def receive_loop(self):
        while True:
            try:
                data = self.client.recv(1024)
            except socket.timeout:
                continue
            except ConnectionResetError:
                self.log("Conexão encerrada pelo servidor.")
                self.state = "DISCONNECTED"
                self.update_ui()
                break

            if not data:
                self.log("Servidor desconectou.")
                self.state = "DISCONNECTED"
                self.update_ui()
                break

            self.buffer += data.decode("utf-8")

            while "\n" in self.buffer:
                message, self.buffer = self.buffer.split("\n", 1)
                message = normalize_message(message)

                if not message:
                    continue

                self.handle_message(message)

    def handle_message(self, message):
        if message == WAITING:
            self.state = "WAITING_PLAYER"
            self.log("Aguardando o outro jogador...")
        elif message == START:
            self.state = "READY"
            self.log("Batalha iniciada! Escolha seu ataque.")
        elif message == TURN:
            self.state = "READY"
            self.log("Nova rodada iniciada. Escolha seu ataque.")
        elif message == WAIT_ACTION:
            self.state = "WAITING_ACTION"
            self.log("Você enviou o ataque. Aguardando o oponente...")
        elif message == WAIT_TURN:
            self.state = "WAITING_ACTION"
            self.log("Aguardando a ação do oponente...")
        elif message.startswith("STATUS:"):
            parts = message.split(":")
            if len(parts) >= 5:
                self.player_hp = int(parts[1])
                self.player_stamina = int(parts[2])
                self.opponent_hp = int(parts[3])
                self.opponent_stamina = int(parts[4])
                self.update_status()
                if self.state != "GAME_OVER":
                    self.state = "READY"
        elif message.startswith("MISS:"):
            attacker_name = message.split(":", 1)[1]
            self.log(f"{attacker_name} errou o ataque! Nenhum dano foi causado.")
        elif message.startswith(f"{CHAT}:"):
            chat_parts = message.split(":", 2)
            if len(chat_parts) == 3:
                sender_name, chat_text = chat_parts[1], chat_parts[2]
                self.log(f"{sender_name}: {chat_text}")
                self.speech_queue.put(f"{sender_name} disse: {chat_text}")
        elif message == "Stamina insuficiente!":
            self.state = "READY"
            self.log("Stamina insuficiente! Escolha outro ataque.")
        elif message == "GAME_OVER":
            self.state = "GAME_OVER"
            self.log("Partida encerrada! O jogo acabou.")
        else:
            self.log(f"Servidor: {message}")

        self.update_ui()


if __name__ == "__main__":
    root = tk.Tk()
    app = BattleClient(root)
    root.mainloop()
