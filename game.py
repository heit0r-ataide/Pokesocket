class Player:
    def __init__(self, name):
        self.name = name
        self.hp = 100
        self.stamina = 100
        self.max_stamina = 100


class Game:
    def __init__(self):
        self.players = []
        self.turn = 0
        self.started = False
        self.pending_actions = {}
        self.attacks = {
            1: {"name": "Ataque rápido", "damage": 10, "stamina": 0},
            2: {"name": "Ataque normal", "damage": 20, "stamina": 15},
            3: {"name": "Ataque forte", "damage": 30, "stamina": 30},
            4: {"name": "Ataque devastador", "damage": 40, "stamina": 50}
        }

    def add_player(self, name):
        player = Player(name)
        self.players.append(player)

    def start(self):
        if len(self.players) == 2:
            self.started = True
            self.turn = 0
            self.pending_actions = {}

    def get_current_player(self):
        return self.players[self.turn]

    def get_player_state(self, player_index):
        player = self.players[player_index]
        return {
            "hp": player.hp,
            "stamina": player.stamina,
        }

    def can_attack(self, attacker_index, attack_key):
        if not self.started:
            return False

        if not 0 <= attacker_index < len(self.players):
            return False

        if attack_key not in self.attacks:
            return False

        attacker = self.players[attacker_index]
        stamina_cost = self.attacks[attack_key]["stamina"]

        return attacker.stamina >= stamina_cost

    def submit_action(self, player_index, attack_key):
        if not self.started:
            return False

        if player_index in self.pending_actions:
            return False

        if not self.can_attack(player_index, attack_key):
            return False

        self.pending_actions[player_index] = attack_key
        return len(self.pending_actions) == 2

    def resolve_round(self):
        if len(self.pending_actions) < 2:
            return False

        selected_actions = dict(self.pending_actions)
        self.pending_actions.clear()

        for player_index in range(2):
            attack_key = selected_actions.get(player_index)
            if attack_key is None:
                continue

            attack = self.attacks[attack_key]
            self.players[player_index].stamina -= attack["stamina"]
            if self.players[player_index].stamina < 0:
                self.players[player_index].stamina = 0

        for player_index in range(2):
            attack_key = selected_actions.get(player_index)
            if attack_key is None:
                continue

            defender_index = 1 - player_index
            damage = self.attacks[attack_key]["damage"]
            self.players[defender_index].hp -= damage

            if self.players[defender_index].hp < 0:
                self.players[defender_index].hp = 0

        for player in self.players:
            player.stamina += 15
            if player.stamina > player.max_stamina:
                player.stamina = player.max_stamina

        return True

    def attack(self, attacker_index, attack_key):
        if not self.can_attack(attacker_index, attack_key):
            print("Stamina insuficiente.")
            return None

        defender_index = 1 - attacker_index
        defender = self.players[defender_index]

        attack = self.attacks[attack_key]
        stamina_cost = attack["stamina"]

        self.players[attacker_index].stamina -= stamina_cost

        damage = attack["damage"]
        defender.hp -= damage

        if defender.hp < 0:
            defender.hp = 0

        return defender.hp

    def next_turn(self):
        self.turn = 1 - self.turn
        player = self.players[self.turn]
        player.stamina += 15

        if player.stamina > player.max_stamina:
            player.stamina = player.max_stamina

    def is_game_over(self):
        for player in self.players:
            if player.hp <= 0:
                return True

        return False
