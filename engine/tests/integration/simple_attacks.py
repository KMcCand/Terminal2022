import unittest
from tests.base import *
from tests import gamelib
import ast

class SimpleAttacks(unittest.TestCase):
    def test_single_demolisher_attack_single_turret(self):
        state = gamelib.GameState(CONFIG, turn_0)
        state.game_map.add_unit(TURRET, [0, 14])

        attack_info1 = gamelib.AttackInfo(DEMOLISHER, "PLAYER", 14, 0, "TOP_LEFT")
        attack = [attack_info1]
        
        serializer = gamelib.Serializer(CONFIG)

        serialized_state = serializer.serialize_game_state(state)
        serialized_attack = serializer.serialize_attack(attack)

        result = get_single_attack_result(serialized_state, serialized_attack, config_string)
        result = ast.literal_eval(result)

        self.assertEqual(float(result['player_points_scored']), 0)
        self.assertEqual(float(result['player_destroyed_damage_caused']), 0)
        self.assertEqual(float(result['player_total_damage_caused']), 3.84)

    def test_real_scenario1(self):
        state = gamelib.GameState(CONFIG, turn_0)

        wall_locations = [[0, 13], [1, 13], [2, 12], [3, 11], [4, 11], [5, 10], [6, 9], [7, 8],
                          [8, 8], [9, 8], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], [15, 8],
                          [16, 8], [17, 8], [18, 8], [19, 8], [20, 9], [21, 10], [20, 11], [21, 12],
                          [23, 12], [24, 13], [25, 13], [26, 13], [27, 13],
                          [3, 16], [4, 16], [5, 17], [6, 18], [7, 19], [8, 20], [9, 21]]
        
        turret_locations = [[1, 12], [2, 11], [21, 11], [24, 12]]

        support_locations = [[11, 17], [12, 17], [13, 17], [14, 17], [15, 17],
                             [11, 16], [12, 16], [13, 16], [14, 16], [15, 16],
                             [11, 15], [12, 15], [13, 15], [14, 15], [15, 15]]

        for loc in wall_locations:
            state.game_map.add_unit(WALL, loc)
            state.game_map[loc][0].upgrade()
            state.game_map[loc][0].health = 120.0

        for loc in turret_locations:
            state.game_map.add_unit(TURRET, loc)
            state.game_map[loc][0].upgrade()

        for loc in support_locations:
            state.game_map.add_unit(SUPPORT, loc)
            state.game_map[loc][0].upgrade()

        attack = []
        for i in range(5):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "OPPONENT", 9, 23, "BOTTOM_RIGHT"))

        for i in range(8):
            attack.append(gamelib.AttackInfo(SCOUT, "OPPONENT", 4, 18, "BOTTOM_RIGHT"))

        serializer = gamelib.Serializer(CONFIG)

        serialized_state = serializer.serialize_game_state(state)
        serialized_attack = serializer.serialize_attack(attack)
        
        result = get_single_attack_result(serialized_state, serialized_attack, config_string)
        result = ast.literal_eval(result)

        self.assertEqual(float(result['opponent_points_scored']), 11)
        self.assertEqual(float(result['opponent_destroyed_damage_caused']), 34)
        self.assertTrue(float(result['opponent_total_damage_caused']) > 34)

    def test_real_scenario2(self):
        state = gamelib.GameState(CONFIG, turn_0)

        turret_locations = [[2, 11], [5, 11], [6, 11], [21, 11], [22, 11], [25, 11],
                            [2, 16], [5, 16], [6, 16], [21, 16], [22, 16], [25, 16]]

        wall_locations = [[0, 13], [27, 13], [1, 12], [5, 12], [6, 12], [21, 12], [22, 12], 
                          [26, 12], [6, 10], [21, 10], [7, 9], [20, 9], [8, 8], [9, 8], [10, 8], 
                          [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8], 
                          [19, 8], [8, 19], [9, 19], [10, 19], [11, 19], [12, 19], [13, 19], [14, 19], 
                          [15, 19], [16, 19], [17, 19], [18, 19], [19, 19], [7, 18], [20, 18], [6, 17], 
                          [21, 17], [1, 15], [5, 15], [6, 15], [21, 15], [22, 15], [26, 15], [0, 14], 
                          [27, 14]]

        wall_upgrades = [[0, 13], [1, 12], [5, 12], [6, 12], [21, 12], [22, 12], [26, 12], [27, 13],
                         [0, 14], [1, 15], [5, 15], [6, 15], [21, 15], [22, 15], [26, 15], [27, 14]]

        for loc in wall_locations:
            state.game_map.add_unit(WALL, loc)

        for loc in turret_locations:
            state.game_map.add_unit(TURRET, loc)

        for loc in wall_upgrades:
            state.game_map[loc][0].upgrade()
            state.game_map[loc][0].health = 120.0

        attack = []
        for i in range(50):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 4, 9, "TOP_RIGHT"))

        serializer = gamelib.Serializer(CONFIG)

        serialized_state = serializer.serialize_game_state(state)
        serialized_attack = serializer.serialize_attack(attack)

        result = get_single_attack_result(serialized_state, serialized_attack, config_string)
        result = ast.literal_eval(result)

        self.assertEqual(float(result['player_points_scored']), 45)