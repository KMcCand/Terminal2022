import unittest
from tests.base import *
from tests import gamelib
import ast

class SelfDestructAttacks(unittest.TestCase):
    def test_scout_self_destruct(self):
        state = gamelib.GameState(CONFIG, turn_0)

        wall_locations = [[14, 1], [13, 2], [12, 3], [11, 4], [10, 5], [9, 6],
                          [8, 7], [7, 8], [6, 9], [5, 10], [4, 11], [3, 12],
                          [2, 13], [2, 14], [1, 14], [0, 14]]

        for loc in wall_locations:
            state.game_map.add_unit(WALL, loc)
            state.game_map[loc][0].upgrade()
            state.game_map[loc][0].health = 120.0

        attack = []
        for _ in range(8):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 12, 1, "TOP_RIGHT"))

        for _ in range(3):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 13, 0, "TOP_RIGHT"))
        
        serializer = gamelib.Serializer(CONFIG)

        serialized_state = serializer.serialize_game_state(state)
        serialized_attack = serializer.serialize_attack(attack)

        result = get_single_attack_result(serialized_state, serialized_attack, config_string)
        result = ast.literal_eval(result)

        self.assertEqual(float(result['player_points_scored']), 3)
        self.assertEqual(float(result['player_total_damage_caused']), 6.0)
        self.assertEqual(float(result['player_destroyed_damage_caused']), 6.0)

    def test_self_destruct_at_different_times(self):
        state = gamelib.GameState(CONFIG, turn_0)

        wall_locations = [[14, 1], [13, 2], [12, 3], [11, 4], [10, 5], [9, 6],
                          [8, 7], [7, 8], [6, 9], [5, 10], [4, 11], [3, 12],
                          [2, 13], [2, 14], [1, 14], [0, 14]]

        for loc in wall_locations:
            state.game_map.add_unit(WALL, loc)
            state.game_map[loc][0].upgrade()
            state.game_map[loc][0].health = 120.0

        attack = []
        for _ in range(3):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 12, 1, "TOP_RIGHT"))

        for _ in range(8):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 13, 0, "TOP_RIGHT"))
        
        serializer = gamelib.Serializer(CONFIG)

        serialized_state = serializer.serialize_game_state(state)
        serialized_attack = serializer.serialize_attack(attack)

        result = get_single_attack_result(serialized_state, serialized_attack, config_string)
        result = ast.literal_eval(result)

        self.assertEqual(float(result['player_points_scored']), 0)
        self.assertEqual(float(result['player_total_damage_caused']), 6.0)
        self.assertEqual(float(result['player_destroyed_damage_caused']), 6.0)

    def test_self_destruct_spring_config(self):
        state = gamelib.GameState(CONFIG_SPRING, turn_0)

        wall_locations = [[11, 3], [12, 3], [13, 2], [14, 2], [15, 3], [16, 4],
                          [17, 5], [18, 6], [19, 7], [20, 8], [21, 9], [22, 10],
                          [23, 11], [24, 12], [25, 13], [25, 14], [26, 14], [27, 14],
                          [22, 14], [23, 14], [24, 14]]

        for loc in wall_locations:
            state.game_map.add_unit(WALL, loc)
            state.game_map[loc][0].upgrade()
            state.game_map[loc][0].health = 200.0

        state.game_map.add_unit(TURRET, [26, 15])
        state.game_map[[26, 15]][0].upgrade()
        state.game_map[[26, 15]][0].health = 100.0

        state.game_map.add_unit(SUPPORT, [19, 8])
        state.game_map[[19, 8]][0].upgrade()

        state.game_map.add_unit(SUPPORT, [18, 7])
        state.game_map[[18, 7]][0].upgrade()

        attack = []
        for _ in range(12):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 12, 1, "TOP_RIGHT"))

        for _ in range(8):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 11, 2, "TOP_RIGHT"))
        
        serializer = gamelib.Serializer(CONFIG_SPRING)

        serialized_state = serializer.serialize_game_state(state)
        serialized_attack = serializer.serialize_attack(attack)

        result = get_single_attack_result(serialized_state, serialized_attack, config_string_spring)
        result = ast.literal_eval(result)

        self.assertEqual(float(result['player_points_scored']), 0)