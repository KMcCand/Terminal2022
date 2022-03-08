from tests.base import *
import unittest
from tests import gamelib

class SmallAttackManyDefenses(unittest.TestCase):
    def test_all_locs_filled_with_walls(self):
        state = gamelib.GameState(CONFIG, turn_0)

        for j in range(14, 28):
            for i in range(j - 14, 28 - (j - 14)):
                state.game_map.add_unit(WALL, [i, j])

        for _ in range(30):
            attack = []
            for i in range(3):
                attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 4, 9, "TOP_RIGHT"))
            
            serializer = gamelib.Serializer(CONFIG)

            serialized_state = serializer.serialize_game_state(state)
            serialized_attack = serializer.serialize_attack(attack)

            result = get_single_attack_result(serialized_state, serialized_attack, config_string)

    def test_small_path_through_walls(self):
        state = gamelib.GameState(CONFIG, turn_0)

        for j in range(14, 28):
            for i in range(j - 14, 28 - (j - 14)):
                if i != 14:
                    state.game_map.add_unit(WALL, [i, j])

        for _ in range(30):
            attack = []
            for i in range(3):
                attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 4, 9, "TOP_RIGHT"))
            
            serializer = gamelib.Serializer(CONFIG)

            serialized_state = serializer.serialize_game_state(state)
            serialized_attack = serializer.serialize_attack(attack)

            result = get_single_attack_result(serialized_state, serialized_attack, config_string)

    def test_single_path_through_board(self):
        state = gamelib.GameState(CONFIG, turn_0)

        for j in range(0, 14):
            for i in range(14 - j - 1, 28 - (14 - j - 1)):
                if i != 14:
                    state.game_map.add_unit(WALL, [i, j])

        for j in range(14, 28):
            for i in range(j - 14, 28 - (j - 14)):
                if i != 14:
                    state.game_map.add_unit(WALL, [i, j])

        for _ in range(30):
            attack = []
            for i in range(3):
                attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 14, 0, "TOP_LEFT"))
            
            serializer = gamelib.Serializer(CONFIG)

            serialized_state = serializer.serialize_game_state(state)
            serialized_attack = serializer.serialize_attack(attack)

            result = get_single_attack_result(serialized_state, serialized_attack, config_string)