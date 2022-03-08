from tests.base import *
import unittest
from tests import gamelib

class VariousRealStrategies(unittest.TestCase):
    def test_real_strategy1(self):
        state = gamelib.GameState(CONFIG, turn_0)

        turret_locs = [[3, 12], [24, 12], [6, 10], [9, 10], [12, 10], 
                       [15, 10], [18, 10], [21, 10],
                       [3, 16], [5, 16], [6, 16], [7, 16], [3, 15]]

        wall_locs = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], 
                     [26, 13], [27, 13], [4, 12], [23, 12], [6, 11], [9, 11], 
                     [12, 11], [15, 11], [18, 11], [21, 11],
                     [11, 23], [12, 23], [13, 23], [14, 23], [15, 23], [16, 23], 
                     [10, 22], [17, 22], [9, 21], [18, 21], [8, 20], [19, 20], 
                     [7, 19], [20, 19], [6, 18], [21, 18], [5, 17], [22, 17], 
                     [23, 16], [5, 15], [6, 15], [7, 15], [23, 15], [0, 14], 
                     [1, 14], [2, 14], [3, 14], [24, 14], [25, 14], [26, 14], 
                     [27, 14]]

        for loc in turret_locs:
            state.game_map.add_unit(TURRET, loc)

        for loc in wall_locs:
            state.game_map.add_unit(WALL, loc)

        for loc in turret_locs:
            state.game_map[loc][0].upgrade()

        for loc in wall_locs:
            state.game_map[loc][0].upgrade()
            state.game_map[loc][0].health = 120

        deploy_locs = [[0, 13], [1, 12], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7], [7, 6],
                       [8, 5], [9, 4], [10, 3], [11, 2], [12, 1], [13, 0],
                       [14, 0], [15, 1], [16, 2], [17, 3], [18, 4], [19, 5], [20, 6],
                       [21, 7], [22, 8], [23, 9], [24, 10], [25, 11], [26, 12], [27, 13]]

        deploy_counts = [[20, 7], [9, 3], [27, 9]]

        # Only player deploys
        for counts in deploy_counts:
            # Scouts
            for loc in deploy_locs:
                attack = []
                if loc[0] < 14:
                    for i in range(counts[0]):
                        attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", loc[0], loc[1], "TOP_RIGHT"))
                else:
                    for i in range(counts[0]):
                        attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", loc[0], loc[1], "TOP_LEFT"))

                serializer = gamelib.Serializer(CONFIG)

                serialized_state = serializer.serialize_game_state(state)
                serialized_attack = serializer.serialize_attack(attack)

                result = get_single_attack_result(serialized_state, serialized_attack, config_string)

            # Demolishers
            for loc in deploy_locs:
                attack = []
                if loc[0] < 14:
                    for i in range(counts[1]):
                        attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_RIGHT"))
                else:
                    for i in range(counts[1]):
                        attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_LEFT"))

                serializer = gamelib.Serializer(CONFIG)

                serialized_state = serializer.serialize_game_state(state)
                serialized_attack = serializer.serialize_attack(attack)

                result = get_single_attack_result(serialized_state, serialized_attack, config_string)

        # Player and opponent both deploy
        for counts in deploy_counts:
            # Scouts
            for loc in deploy_locs:
                attack = []
                if loc[0] < 14:
                    for i in range(counts[0]):
                        attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", loc[0], loc[1], "TOP_RIGHT"))
                else:
                    for i in range(counts[0]):
                        attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", loc[0], loc[1], "TOP_LEFT"))

                attack.append(gamelib.AttackInfo(SCOUT, "OPPONENT", 0, 23, "BOTTOM_RIGHT"))

                serializer = gamelib.Serializer(CONFIG)

                serialized_state = serializer.serialize_game_state(state)
                serialized_attack = serializer.serialize_attack(attack)

                result = get_single_attack_result(serialized_state, serialized_attack, config_string)

            # Demolishers
            for loc in deploy_locs:
                attack = []
                if loc[0] < 14:
                    for i in range(counts[1]):
                        attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_RIGHT"))
                else:
                    for i in range(counts[1]):
                        attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", loc[0], loc[1], "TOP_LEFT"))

                attack.append(gamelib.AttackInfo(SCOUT, "OPPONENT", 0, 23, "BOTTOM_RIGHT"))

                serializer = gamelib.Serializer(CONFIG)

                serialized_state = serializer.serialize_game_state(state)
                serialized_attack = serializer.serialize_attack(attack)

                result = get_single_attack_result(serialized_state, serialized_attack, config_string)