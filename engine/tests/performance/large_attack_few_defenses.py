from tests.base import *
import unittest
from tests import gamelib

class LargeAttackFewDefenses(unittest.TestCase):
    def test_huge_demolisher_attack_single_defense(self):
        state = gamelib.GameState(CONFIG, turn_0)

        for _ in range(30):
            attack = []
            for i in range(100):
                attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 4, 9, "TOP_RIGHT"))
            
            serializer = gamelib.Serializer(CONFIG)

            serialized_state = serializer.serialize_game_state(state)
            serialized_attack = serializer.serialize_attack(attack)

            result = get_single_attack_result(serialized_state, serialized_attack, config_string)

    def test_huge_scout_attack_single_defense(self):
        state = gamelib.GameState(CONFIG, turn_0)

        for _ in range(30):
            attack = []
            for i in range(100):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 4, 9, "TOP_RIGHT"))
            
            serializer = gamelib.Serializer(CONFIG)

            serialized_state = serializer.serialize_game_state(state)
            serialized_attack = serializer.serialize_attack(attack)

            result = get_single_attack_result(serialized_state, serialized_attack, config_string)

    def test_scout_from_every_start(self):
        state = gamelib.GameState(CONFIG, turn_0)

        locs = [[0, 13], [1, 12], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7], [7, 6],
                [8, 5], [9, 4], [10, 3], [11, 2], [12, 1], [13, 0],
                [14, 0], [15, 1], [16, 2], [17, 3], [18, 4], [19, 5], [20, 6],
                [21, 7], [22, 8], [23, 9], [24, 10], [25, 11], [26, 12], [27, 13]]

        for _ in range(20):
            attack = []
            for loc in locs:
                if loc[0] < 14:
                    attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", loc[0], loc[1], "TOP_RIGHT"))
                else:
                    attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", loc[0], loc[1], "TOP_LEFT"))
            
            serializer = gamelib.Serializer(CONFIG)

            serialized_state = serializer.serialize_game_state(state)
            serialized_attack = serializer.serialize_attack(attack)

            result = get_single_attack_result(serialized_state, serialized_attack, config_string)

    def test_scout_and_demolisher_from_every_start(self):
        state = gamelib.GameState(CONFIG, turn_0)

        locs = [[0, 13], [1, 12], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7], [7, 6],
                [8, 5], [9, 4], [10, 3], [11, 2], [12, 1], [13, 0],
                [14, 0], [15, 1], [16, 2], [17, 3], [18, 4], [19, 5], [20, 6],
                [21, 7], [22, 8], [23, 9], [24, 10], [25, 11], [26, 12], [27, 13]]

        for _ in range(20):
            attack = []
            for loc in locs:
                if loc[0] < 14:
                    attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", loc[0], loc[1], "TOP_RIGHT"))
                    attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_RIGHT"))
                else:
                    attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", loc[0], loc[1], "TOP_LEFT"))
                    attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_LEFT"))
            
            serializer = gamelib.Serializer(CONFIG)

            serialized_state = serializer.serialize_game_state(state)
            serialized_attack = serializer.serialize_attack(attack)

            result = get_single_attack_result(serialized_state, serialized_attack, config_string)