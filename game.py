class Player:
    def __init__(self, name):
        self.name = name
        self.hp = 100


class Game:
    def __init__(self):
        self.players = []
        self.turn = 0
        self.started = False

    def add_player(self, name):
        player = Player(name)
        self.players.append(player)

    def start(self):
        if len(self.players) == 2:
            self.started = True
            self.turn = 0

    def get_current_player(self):
        return self.players[self.turn]

    def attack(self, attacker_index, damage=20):
        defender_index = 1 - attacker_index

        attacker = self.players[attacker_index]
        defender = self.players[defender_index]

        defender.hp -= damage

        if defender.hp < 0:
            defender.hp = 0

        return defender.hp

    def next_turn(self):
        self.turn = 1 - self.turn

    def is_game_over(self):
        for player in self.players:
            if player.hp <= 0:
                return True

        return False
    