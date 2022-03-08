import ctypes
import gamelib
import random
import math
import warnings
from sys import maxsize
import json
import copy
import ast
import time

WALL_COST = 1
TURRET_COST = 2
SUPPORT_COST = 4
WALL_UPGRADE_COST = 1
TURRET_UPGRADE_COST = 4
SUPPORT_UPGRADE_COST = 4

handle = ctypes.CDLL("./engine-linux.so")

handle.get_attack_result.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
handle.get_attack_result.restype = ctypes.c_void_p

handle.free_string.argtypes = [ctypes.c_void_p]
handle.free_string.restype = None

with open('./game-configs.json', 'r') as file:
    config_string = file.read().replace('\n', '')

def get_attack_result(game_state_str, attack_str, config_str):    
    res = handle.get_attack_result(ctypes.c_char_p(str.encode(game_state_str)), 
                                ctypes.c_char_p(str.encode(attack_str)), 
                                ctypes.c_char_p(str.encode(config_str)))
    result = ctypes.cast(res, ctypes.c_char_p).value.decode("utf-8")
    handle.free_string(res)
    return result

class AttackStrategy:
    def __init__(self, attack, remove_walls, add_walls):
        self.attack = attack
        self.remove_walls = remove_walls
        self.add_walls = add_walls

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

        self.opponent_removed_locations = []
        self.countered_last_turn = False

        self.last_turn_opponent_interceptor_spawns = set()
        self.last_two_turns_opponent_interceptor_spawns = []

        self.attacked_last_turn = False
        self.last_turn_game_state = None

        self.current_strategy = None
        self.forbidden_locations = []
        self.add_walls = []

        self.num_times_countered = 0
        self.stop_countering = False

        self.start_time = 0

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        self.start_time = time.time()
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        interceptor_spawns = []
        for loc in self.last_turn_opponent_interceptor_spawns:
            interceptor_spawns.append(loc)

        if len(self.last_two_turns_opponent_interceptor_spawns) == 2:
            del self.last_two_turns_opponent_interceptor_spawns[-1]

        self.last_two_turns_opponent_interceptor_spawns.insert(0, interceptor_spawns)
        self.last_turn_opponent_interceptor_spawns = set()

        self.starter_strategy(game_state)
        self.last_turn_game_state = None
        self.opponent_removed_locations = []

        game_state.submit_turn()

    def launch_attack(self, game_state, strategy):
        result = self.get_result_of_attack_strategy(copy.deepcopy(game_state), strategy)

        self.forbidden_locations = strategy.remove_walls
        self.add_walls = strategy.add_walls
        self.current_strategy = strategy

        need_to_wait = False
        for loc in strategy.remove_walls:
            if game_state.contains_stationary_unit(loc):
                game_state.attempt_remove(loc)
                need_to_wait = True

        if need_to_wait:
            return

        for loc in strategy.add_walls:
            game_state.attempt_spawn(WALL, loc)
            game_state.attempt_remove(loc)

        for info in strategy.attack:
            game_state.attempt_spawn(info.unit_type, [info.start_x, info.start_y])

        self.current_strategy = None
        self.forbidden_locations = []
        self.add_walls = []

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        self.build_defenses(game_state, self.forbidden_locations, len(self.add_walls))

        if self.current_strategy != None:
            self.launch_attack(game_state, self.current_strategy)
            return

        if game_state.turn_number <= 2:
            game_state.attempt_spawn(INTERCEPTOR, [[3, 10], [6, 7], [20, 6], [24, 10]], 1)
            return

        if self.num_times_countered >= 4:
            self.stop_countering = True

        if game_state.get_resource(MP, player_index=1) >= 10 and game_state.get_resource(SP, player_index=1) >= 20 and \
            self.stop_countering == False:
            self.num_times_countered += 1
            game_state.attempt_spawn(INTERCEPTOR, [[5, 8]], 2)
            return

        demolisher_strategy, total_damage = self.get_best_demolisher_rush_attack(game_state)
        scout_strategy, points_scored = self.get_best_scout_rush_attack(game_state)

        if game_state.get_resource(MP) <= 6:
            if demolisher_strategy != None and total_damage >= 6:
                self.launch_attack(game_state, demolisher_strategy)
                return
        elif game_state.get_resource(MP) <= 9:
            if scout_strategy and points_scored >= 5:
                self.launch_attack(game_state, scout_strategy)
                return

            if demolisher_strategy and total_damage >= 8:
                self.launch_attack(game_state, demolisher_strategy)
                return
        else:
            if scout_strategy and points_scored >= 8:
                self.launch_attack(game_state, scout_strategy)
                return

            if demolisher_strategy and total_damage >= min(4 * len(demolisher_strategy.attack), 16):
                self.launch_attack(game_state, demolisher_strategy)
                return


    def build_defenses(self, game_state, forbidden_locs, leftover_sp):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download
        def remove_low_health_defenses(game_state):
            for i in range(0, 28):
                for j in range(0, 14):
                    if not game_state.game_map.in_arena_bounds([i, j]):
                        continue

                    unit = game_state.contains_stationary_unit([i, j])

                    if unit == False:
                        continue

                    if unit.health / unit.max_health <= 0.8:
                        game_state.attempt_remove([i, j])

        remove_low_health_defenses(game_state)

        # Bait
        if game_state.turn_number >= 2:
            game_state.attempt_remove([18, 6])
            game_state.attempt_spawn(WALL, [18, 6])

        walls = [[0, 13], [1, 13], [2, 13], [3, 12], [5, 11], [6, 9],
                 [21, 9], [22, 11], [24, 12], [25, 13], [26, 13], [27, 13]]

        for loc in walls:
            if loc in forbidden_locs:
                continue

            if game_state.get_resource(SP) - leftover_sp < WALL_COST:
                return

            game_state.attempt_spawn(WALL, loc)

        turrets = [[2, 12], [5, 10], [22, 10], [25, 12]]

        for loc in turrets:
            if loc in forbidden_locs:
                continue

            if game_state.get_resource(SP) - leftover_sp < TURRET_COST:
                return

            game_state.attempt_spawn(TURRET, loc)

        walls = [[7, 8], [8, 7], [9, 6], [10, 5], [11, 4], [12, 3], [13, 3], [14, 3],
                 [15, 3], [16, 4], [17, 5], [18, 6], [19, 7], [20, 8]]

        for loc in walls:
            if loc in forbidden_locs:
                continue

            if game_state.get_resource(SP) - leftover_sp < WALL_COST:
                return

            game_state.attempt_spawn(WALL, loc)

        # Upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_UPGRADE_COST:
            return

        game_state.attempt_upgrade([2, 12])

        # Upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_UPGRADE_COST:
            return

        game_state.attempt_upgrade([25, 12])

        # Upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_UPGRADE_COST:
            return

        game_state.attempt_upgrade([5, 10])

       # Upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_UPGRADE_COST:
            return

        game_state.attempt_upgrade([22, 10])

        # Build a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_COST:
            return

        if [23, 11] not in forbidden_locs:
            game_state.attempt_spawn(WALL, [23, 11])

        # Upgrade a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_UPGRADE_COST:
            return

        game_state.attempt_upgrade([5, 11])

        # Upgrade a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_UPGRADE_COST:
            return

        game_state.attempt_upgrade([22, 11])

        # Build a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_COST:
            return

        game_state.attempt_spawn(TURRET, [6, 10])

        # Build a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_COST:
            return

        game_state.attempt_spawn(TURRET, [21, 10])

        # Upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_UPGRADE_COST:
            return

        game_state.attempt_upgrade([6, 10])

        # Upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_UPGRADE_COST:
            return

        game_state.attempt_upgrade([21, 10])

        # Upgrade a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_UPGRADE_COST:
            return

        game_state.attempt_upgrade([0, 13])

        # Upgrade a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_UPGRADE_COST:
            return

        game_state.attempt_upgrade([27, 13])

        # Upgrade a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_UPGRADE_COST:
            return

        game_state.attempt_upgrade([1, 13])

        # Upgrade a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_UPGRADE_COST:
            return

        game_state.attempt_upgrade([26, 13])

        # Upgrade a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_UPGRADE_COST:
            return

        game_state.attempt_upgrade([2, 13])

        # Upgrade a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_UPGRADE_COST:
            return

        game_state.attempt_upgrade([25, 13])

        # Upgrade a wall
        if game_state.get_resource(SP) - leftover_sp < WALL_UPGRADE_COST:
            return

        game_state.attempt_upgrade([24, 12])

        # Build and upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_COST + TURRET_UPGRADE_COST:
            return

        game_state.attempt_spawn(TURRET, [2, 11])
        game_state.attempt_upgrade([2, 11])

        # Build and upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_COST + TURRET_UPGRADE_COST:
            return

        game_state.attempt_spawn(TURRET, [3, 11])
        game_state.attempt_upgrade([3, 11])

        # Build and upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_COST + TURRET_UPGRADE_COST:
            return

        game_state.attempt_spawn(TURRET, [1, 12])
        game_state.attempt_upgrade([1, 12])

        # Build and upgrade a turret
        if game_state.get_resource(SP) - leftover_sp < TURRET_COST + TURRET_UPGRADE_COST:
            return

        game_state.attempt_spawn(TURRET, [26, 12])
        game_state.attempt_upgrade([26, 12])

        supports = [[9, 7], [10, 7], [11, 7], [12, 7]]
        for loc in supports:
            if loc in forbidden_locs:
                continue

            if game_state.get_resource(SP) - leftover_sp < SUPPORT_COST:
                return

            game_state.attempt_spawn(SUPPORT, loc)

            if game_state.get_resource(SP) - leftover_sp < SUPPORT_UPGRADE_COST:
                return

            game_state.attempt_upgrade(loc)

        turrets = [[7, 10], [7, 9]]
        for loc in turrets:
            if loc in forbidden_locs:
                continue

            if game_state.get_resource(SP) - leftover_sp < TURRET_COST:
                return

            game_state.attempt_spawn(TURRET, loc)

            if game_state.get_resource(SP) - leftover_sp < TURRET_UPGRADE_COST:
                return

            game_state.attempt_upgrade(loc)

        supports = [[13, 7], [14, 7], [10, 6], [11, 6], [12, 6],
                    [13, 6], [14, 6], [11, 5], [12, 5], [13, 5], [14, 5]]

        for loc in supports:
            if loc in forbidden_locs:
                continue

            if game_state.get_resource(SP) - leftover_sp < SUPPORT_COST:
                return

            game_state.attempt_spawn(SUPPORT, loc)

            if game_state.get_resource(SP) - leftover_sp < SUPPORT_UPGRADE_COST:
                return

            game_state.attempt_upgrade(loc)

    def get_best_scout_rush_attack(self, game_state):
        attack_strategies = []

        # From left
        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11], [5, 11]], [[23, 11], [4, 12], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11], [5, 11]], [[23, 11], [4, 12], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)


        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11], [5, 11]], [[23, 11], [4, 12], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11], [5, 11]], [[23, 11], [4, 12], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        # From right
        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13], [18, 13], [17, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11], [23, 12]], [[4, 11], [22, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13], [18, 13], [17, 13]])
        attack_strategies.append(strategy)


        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13], [18, 13], [17, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP))):
            attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11], [23, 12]], [[4, 11], [22, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13], [18, 13], [17, 13]])
        attack_strategies.append(strategy)

        if game_state.get_resource(MP) >= 12:
            attack = []
            for i in range(10):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 10, 3, "TOP_RIGHT"))

            for i in range(math.floor(game_state.get_resource(MP)) - 10):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 11, 2, "TOP_RIGHT"))

            strategy = AttackStrategy(attack, [[4, 11]], [[23, 11]])
            attack_strategies.append(strategy)

            attack = []
            for i in range(10):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 16, 2, "TOP_LEFT"))

            for i in range(math.floor(game_state.get_resource(MP)) - 10):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 17, 3, "TOP_LEFT"))

            strategy = AttackStrategy(attack, [[4, 11]], [[23, 11]])
            attack_strategies.append(strategy)

            attack = []
            for i in range(10):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 11, 2, "TOP_RIGHT"))

            for i in range(math.floor(game_state.get_resource(MP)) - 10):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 10, 3, "TOP_RIGHT"))

            strategy = AttackStrategy(attack, [[23, 11]], [[4, 11]])
            attack_strategies.append(strategy)

            attack = []
            for i in range(10):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 17, 3, "TOP_LEFT"))

            for i in range(math.floor(game_state.get_resource(MP)) - 10):
                attack.append(gamelib.AttackInfo(SCOUT, "PLAYER", 16, 2, "TOP_LEFT"))

            strategy = AttackStrategy(attack, [[23, 11]], [[4, 11]])
            attack_strategies.append(strategy)

        game_state_copy = copy.deepcopy(game_state)
        most_points_scored = 0
        best_strategy = None
        for strategy in attack_strategies:
            result = self.get_result_of_attack_strategy(game_state_copy, strategy)

            if float(result['player_points_scored']) > most_points_scored:
                most_points_scored = float(result['player_points_scored'])
                best_strategy = strategy

        if most_points_scored >= 2:
            return best_strategy, most_points_scored

        return None, 0

    def get_best_demolisher_rush_attack(self, game_state):
        attack_strategies = []

        # From left
        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11], [5, 11], [6, 11]], [[23, 11], [4, 12], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 3, 10, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11], [5, 11], [6, 11]], [[23, 11], [4, 12], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)


        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11]], [[23, 11], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11], [5, 11], [6, 11]], [[23, 11], [4, 12], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 12, 1, "TOP_RIGHT"))
        strategy = AttackStrategy(attack, [[4, 11], [5, 11], [6, 11]], [[23, 11], [4, 12], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13]])
        attack_strategies.append(strategy)

        # From right
        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13], [18, 13], [17, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 24, 10, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11], [22, 11], [21, 11]], [[4, 11], [22, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13], [18, 13], [17, 13]])
        attack_strategies.append(strategy)


        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11]], [[4, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13], [18, 13], [17, 13]])
        attack_strategies.append(strategy)

        attack = []
        for i in range(math.floor(game_state.get_resource(MP) / 3)):
            attack.append(gamelib.AttackInfo(DEMOLISHER, "PLAYER", 15, 1, "TOP_LEFT"))
        strategy = AttackStrategy(attack, [[23, 11], [22, 11], [21, 11]], [[4, 11], [22, 11], [23, 13], [22, 13], [21, 13], [20, 13], [19, 13], [18, 13], [17, 13]])
        attack_strategies.append(strategy)

        game_state_copy = copy.deepcopy(game_state)
        most_total_damage = 0
        best_strategy = None
        for strategy in attack_strategies:
            result = self.get_result_of_attack_strategy(game_state_copy, strategy)

            if float(result['player_total_damage_caused']) > most_total_damage:
                most_total_damage = float(result['player_total_damage_caused'])
                best_strategy = strategy

        if most_total_damage >= 4:
            return best_strategy, most_total_damage

        return None, 0

    def get_result_of_attack_strategy(self, game_state, attack_strategy):
        locs_to_remove = []
        walls_to_add = []

        # Add opponent units that were previously removed/destroyed in the last turn
        for i in range(28):
            for j in range(14, 28):
                if not game_state.game_map.in_arena_bounds([i, j]):
                    continue

                if not self.last_turn_game_state:
                    continue

                old_unit = self.last_turn_game_state.contains_stationary_unit([i, j])

                if old_unit != False and not \
                    game_state.contains_stationary_unit([i, j]):
                    game_state.game_map.add_unit(old_unit.unit_type, [i, j], player_index=1)
                    locs_to_remove.append([i, j])

        for loc in self.get_probable_opponent_interceptor_spawns():
            if game_state.contains_stationary_unit(loc):
                continue

            if loc[0] < 14:
                attack_strategy.attack.append(gamelib.AttackInfo(INTERCEPTOR, "OPPONENT", loc[0], loc[1], "BOTTOM_RIGHT"))
            else:
                attack_strategy.attack.append(gamelib.AttackInfo(INTERCEPTOR, "OPPONENT", loc[0], loc[1], "BOTTOM_LEFT"))
            

        for loc in attack_strategy.remove_walls:
            game_state.game_map.remove_unit(loc)
            walls_to_add.append(loc)

        for loc in attack_strategy.add_walls:
            if loc[1] < 14:
                game_state.game_map.add_unit(WALL, loc, 0)
            else:
                game_state.game_map.add_unit(WALL, loc, 1)

            locs_to_remove.append(loc)

        for info in attack_strategy.attack:
            if game_state.contains_stationary_unit([info.start_x, info.start_y]):
                gamelib.debug_write("Warning: tried to launch from " + str([info.start_x, info.start_y]))
        
        serializer = gamelib.Serializer(self.config)
        serialized_state = serializer.serialize_game_state(game_state)
        serialized_attack = serializer.serialize_attack(attack_strategy.attack)

        result = get_attack_result(serialized_state, serialized_attack, config_string)
        to_return = ast.literal_eval(result)

        for loc in locs_to_remove:
            game_state.game_map.remove_unit(loc)

        for loc in walls_to_add:
            game_state.game_map.add_unit(WALL, loc)

        return to_return

    def get_probable_opponent_interceptor_spawns(self):
        spawn_counts = set()

        for i in range(len(self.last_two_turns_opponent_interceptor_spawns)):
            for loc in self.last_two_turns_opponent_interceptor_spawns[i]:
                spawn_counts.add(loc)

        result = list(spawn_counts)

        if len(result) > 3:
            return result[:3]
        else:
            return result

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        state = json.loads(turn_string)

        if not self.last_turn_game_state:
            self.last_turn_game_state = gamelib.GameState(self.config, turn_string)

            for i in range(28):
                for j in range(14, 28):
                    if not self.last_turn_game_state.game_map.in_arena_bounds([i, j]):
                        continue
                        
                    unit = self.last_turn_game_state.contains_stationary_unit([i, j])

                    if unit == False:
                        continue

                    if unit.pending_removal:
                        self.opponent_removed_locations.append([i, j])


        events = state["events"]
        spawns = events["spawn"]
        deaths = events["death"]

        for spawn in spawns:
            if int(spawn[1]) == 5 and str(spawn[3]) == '2':
                self.last_turn_opponent_interceptor_spawns.add((spawn[0][0], spawn[0][1]))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
