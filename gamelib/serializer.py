import gamelib
import json
import math

class Serializer:
    def __init__(self, config):
        self.config = config

        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, REMOVE, UPGRADE, STRUCTURE_TYPES, ALL_UNITS, UNIT_TYPE_TO_INDEX
        UNIT_TYPE_TO_INDEX = {}
        WALL = config["unitInformation"][0]["shorthand"]
        UNIT_TYPE_TO_INDEX[WALL] = 0
        SUPPORT = config["unitInformation"][1]["shorthand"]
        UNIT_TYPE_TO_INDEX[SUPPORT] = 1
        TURRET = config["unitInformation"][2]["shorthand"]
        UNIT_TYPE_TO_INDEX[TURRET] = 2
        SCOUT = config["unitInformation"][3]["shorthand"]
        UNIT_TYPE_TO_INDEX[SCOUT] = 3
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        UNIT_TYPE_TO_INDEX[DEMOLISHER] = 4
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        UNIT_TYPE_TO_INDEX[INTERCEPTOR] = 5
        REMOVE = config["unitInformation"][6]["shorthand"]
        UNIT_TYPE_TO_INDEX[REMOVE] = 6
        UPGRADE = config["unitInformation"][7]["shorthand"]
        UNIT_TYPE_TO_INDEX[UPGRADE] = 7
        
    def get_unit_type_string(self, unit_type):
        if unit_type == WALL:
            return "WALL"
        elif unit_type == TURRET:
            return "DESTRUCTOR"
        elif unit_type == SUPPORT:
            return "SUPPORT"
        elif unit_type == SCOUT:
            return "SCOUT"
        elif unit_type == DEMOLISHER:
            return "DEMOLISHER"
        elif unit_type == INTERCEPTOR:
            return "INTERCEPTOR"
        else:
            raise Exception('Error: not a unit')

    def serialize_game_state(self, game_state):
        def serialize_unit_info(info):
            return "{\"unit_type\": \"%s\", \"x\": %s, \"y\": %s, \"upgraded\": %s, \"health\": %s}" % (info)

        num_stationary_units = 0
        stationary_units_info = []

        for i in range(0, 28):
            for j in range(0, 28):
                if not game_state.game_map.in_arena_bounds([i, j]):
                    continue
                unit = game_state.contains_stationary_unit([i, j])

                if unit == False:
                    continue
                
                num_stationary_units += 1

                stationary_units_info.append((self.get_unit_type_string(unit.unit_type), str(i), str(j), "true" if unit.upgraded else "false", str(unit.health)))

        result = "{\"num_stationary_units\": %s, \"units\": [" % (num_stationary_units)

        for info in stationary_units_info:
            result += serialize_unit_info(info) + ","
        
        result = result[:-1] + "]}"

        return result
        
    def serialize_attack(self, attack):
        def serialize_attack_info(info):
            return "{\"unit_type\": \"%s\", \"player_index\": \"%s\", \"start_x\": %s, \"start_y\": %s, \"target_edge\": \"%s\"}" % (info)

        attack_size = len(attack)
        attack_info = []

        for info in attack:
            attack_info.append((self.get_unit_type_string(info.unit_type), info.player_type, info.start_x, info.start_y, info.target_edge))

        result = "{\"attack_size\": %s, \"attack\": [" % (attack_size)
        
        for info in attack_info:
            result += serialize_attack_info(info) + ","
        
        result = result[:-1] + "]}"

        return result