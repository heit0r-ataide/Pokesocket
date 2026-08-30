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

    def get_current_player(self):
        return self.players[self.turn]

    def attack(self, attacker_index, attack_key):
        defender_index = 1 - attacker_index

        #attacker = self.players[attacker_index]
        defender = self.players[defender_index]

        attack = self.attacks[attack_key]

        stamina_cost = attack["stamina"]

        if self.players[attacker_index].stamina < stamina_cost:
            print("Stamina insuficiente.")
            return None

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
    