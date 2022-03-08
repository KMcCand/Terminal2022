from tests.base import *
import unittest
from tests import gamelib

class DemolisherLineStrategies(unittest.TestCase):
    def test_standard_line_strategy_from_left(self):
        state = gamelib.GameState(CONFIG, turn_0)

        turret_locs = [[3, 12], [8, 12], [13, 12], [18, 12], [22, 12], [23, 12], [26, 12],
                        [5, 15], [8, 15], [11, 15], [14, 15], [17, 15], [20, 15], [23, 15]]

        wall_locs = [[0, 13], [1, 13], [2, 13], [3, 13], [8, 13], [13, 13], [18, 13], [22, 13], 
                    [23, 13], [26, 13], [27, 13], [4, 12], [5, 12], [6, 12], [7, 12], [9, 12], 
                    [10, 12], [11, 12], [12, 12], [14, 12], [15, 12], [16, 12], [17, 12], 
                    [19, 12], [20, 12], [21, 12],
                    [5, 14], [8, 14], [11, 14], [14, 14], [17, 14], [20, 14], [23, 14]]

        for loc in turret_locs:
            state.game_map.add_unit(TURRET, loc)

        for loc in wall_locs:
            state.game_map.add_unit(WALL, loc)

        deploy_locs = [[1, 12], [2, 11], [3, 10], [4, 9]]

        for _ in range(20):
            for loc in deploy_locs:
                attack = []
                for i in range(4):
                    attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_RIGHT"))
                
                serializer = gamelib.Serializer(CONFIG)

                serialized_state = serializer.serialize_game_state(state)
                serialized_attack = serializer.serialize_attack(attack)

                result = get_single_attack_result(serialized_state, serialized_attack, config_string)

    def test_standard_line_strategy_from_right(self):
        state = gamelib.GameState(CONFIG, turn_0)

        turret_locs = [[3, 12], [8, 12], [13, 12], [18, 12], [22, 12], [23, 12], [26, 12],
                        [5, 15], [8, 15], [11, 15], [14, 15], [17, 15], [20, 15], [23, 15]]

        wall_locs = [[0, 13], [1, 13], [2, 13], [3, 13], [8, 13], [13, 13], [18, 13], [22, 13], 
                    [23, 13], [26, 13], [27, 13], [5, 12], [6, 12], [7, 12], [9, 12], 
                    [10, 12], [11, 12], [12, 12], [14, 12], [15, 12], [16, 12], [17, 12], 
                    [19, 12], [20, 12], [21, 12], [24, 12], [25, 12],
                    [5, 14], [8, 14], [11, 14], [14, 14], [17, 14], [20, 14], [23, 14]]

        for loc in turret_locs:
            state.game_map.add_unit(TURRET, loc)

        for loc in wall_locs:
            state.game_map.add_unit(WALL, loc)

        deploy_locs = [[25, 11], [24, 10], [23, 9]]

        for _ in range(20):
            for loc in deploy_locs:
                attack = []
                for i in range(4):
                    attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_LEFT"))
                
                serializer = gamelib.Serializer(CONFIG)

                serialized_state = serializer.serialize_game_state(state)
                serialized_attack = serializer.serialize_attack(attack)

                result = get_single_attack_result(serialized_state, serialized_attack, config_string)