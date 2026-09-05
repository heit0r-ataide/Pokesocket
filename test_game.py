import unittest
from unittest.mock import patch

from game import Game


class GameStaminaTests(unittest.TestCase):
    def test_attack_rejects_insufficient_stamina(self):
        game = Game()
        game.add_player("A")
        game.add_player("B")
        game.start()

        game.players[0].stamina = 10

        self.assertFalse(game.can_attack(0, 2))
        self.assertIsNone(game.attack(0, 2))
        self.assertEqual(game.players[0].stamina, 10)

    @patch("game.random.random", return_value=0.99)
    def test_attack_consumes_stamina_when_valid(self, _random):
        game = Game()
        game.add_player("A")
        game.add_player("B")
        game.start()

        game.players[0].stamina = 20

        self.assertTrue(game.can_attack(0, 2))
        self.assertEqual(game.attack(0, 2), 80)
        self.assertEqual(game.players[0].stamina, 5)

    def test_get_player_state_returns_hp_and_stamina(self):
        game = Game()
        game.add_player("A")
        game.add_player("B")
        game.start()

        game.players[0].hp = 75
        game.players[0].stamina = 40

        self.assertEqual(game.get_player_state(0), {"hp": 75, "stamina": 40})

    @patch("game.random.random", return_value=0.99)
    def test_simultaneous_round_applies_both_attacks(self, _random):
        game = Game()
        game.add_player("A")
        game.add_player("B")
        game.start()

        self.assertFalse(game.submit_action(0, 2))
        self.assertTrue(game.submit_action(1, 1))
        self.assertTrue(game.resolve_round())
        self.assertEqual(game.players[0].hp, 90)
        self.assertEqual(game.players[1].hp, 80)

    @patch("game.random.random", side_effect=[0.01, 0.99])
    def test_missed_attack_consumes_stamina_without_damage(self, _random):
        game = Game()
        game.add_player("A")
        game.add_player("B")
        game.start()

        self.assertFalse(game.submit_action(0, 2))
        self.assertTrue(game.submit_action(1, 1))
        self.assertTrue(game.resolve_round())
        self.assertEqual(game.players[0].hp, 90)
        self.assertEqual(game.players[0].stamina, 100)
        self.assertEqual(game.players[1].hp, 100)
        self.assertEqual(game.players[1].stamina, 100)
        self.assertEqual(game.last_round_misses, [0])


if __name__ == "__main__":
    unittest.main()
