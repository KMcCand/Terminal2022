from tests.base import *
import unittest
from tests import gamelib

class LargeAttackManyDefenses(unittest.TestCase):
    def test_all_locs_filled_with_walls(self):
        state = gamelib.GameState(CONFIG, turn_0)

        for j in range(14, 28):
            for i in range(j - 14, 28 - (j - 14)):
                state.game_map.add_unit(WALL, [i, j])

        for _ in range(30):
            attack = []
            for i in range(20):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 4, 9, "TOP_RIGHT"))
            
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
            for i in range(20):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 4, 9, "TOP_RIGHT"))
            
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
            for i in range(20):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 14, 0, "TOP_LEFT"))
            
            serializer = gamelib.Serializer(CONFIG)

            serialized_state = serializer.serialize_game_state(state)
            serialized_attack = serializer.serialize_attack(attack)

            result = get_single_attack_result(serialized_state, serialized_attack, config_string)

    def test_large_attack_many_turrets(self):
        state = gamelib.GameState(CONFIG, turn_0)

        turret_locs = [[5, 16], [6, 16], [7, 16], [12, 16], [13, 16], [14, 16], [15, 16], 
                       [20, 16], [21, 16], [22, 16], [5, 15], [6, 15], [7, 15], [12, 15], 
                       [13, 15], [14, 15], [15, 15], [20, 15], [21, 15], [22, 15]]

        for loc in turret_locs:
            state.game_map.add_unit(TURRET, loc)

        start_locs_left = [[13 - j, j] for j in range(0, 14)]
        start_locs_right = [[14 + j, j] for j in range(0, 14)]

        for _ in range(10):
            for loc in start_locs_left + start_locs_right:
                attack = []
                for i in range(10):
                    if loc[0] < 14:
                        attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_RIGHT"))
                    else:
                        attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_LEFT"))
                
                serializer = gamelib.Serializer(CONFIG)

                serialized_state = serializer.serialize_game_state(state)
                serialized_attack = serializer.serialize_attack(attack)

                result = get_single_attack_result(serialized_state, serialized_attack, config_string)