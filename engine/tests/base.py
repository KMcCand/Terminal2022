import json
import ctypes

# A "fake" turn 0
turn_0 = """{"p2Units":[[],[],[],[],[],[],[]],"turnInfo":[0,0,-1],"p1Stats":[30.0,25.0,5.0,0],"p1Units":[[],[],[],[],[],[],[]],"p2Stats":[30.0,25.0,5.0,0],"events":{"selfDestruct":[],"breach":[],"damage":[],"shield":[],"move":[],"spawn":[],"death":[],"attack":[],"melee":[]}}"""

with open('./tests/config_files/fall-config.json', 'r') as file:
  config_string = file.read().replace('\n', '')

with open('./tests/config_files/spring-config.json', 'r') as file:
  config_string_spring = file.read().replace('\n', '')

global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR
CONFIG = json.loads(config_string)
CONFIG_SPRING = json.loads(config_string_spring)

WALL = CONFIG["unitInformation"][0]["shorthand"]
SUPPORT = CONFIG["unitInformation"][1]["shorthand"]
TURRET = CONFIG["unitInformation"][2]["shorthand"]
SCOUT = CONFIG["unitInformation"][3]["shorthand"]
DEMOLISHER = CONFIG["unitInformation"][4]["shorthand"]
INTERCEPTOR = CONFIG["unitInformation"][5]["shorthand"]

global UNIT_TYPE_TO_INDEX
UNIT_TYPE_TO_INDEX = {}
WALL = CONFIG["unitInformation"][0]["shorthand"]
UNIT_TYPE_TO_INDEX[WALL] = 0
SUPPORT = CONFIG["unitInformation"][1]["shorthand"]
UNIT_TYPE_TO_INDEX[SUPPORT] = 1
TURRET = CONFIG["unitInformation"][2]["shorthand"]
UNIT_TYPE_TO_INDEX[TURRET] = 2
SCOUT = CONFIG["unitInformation"][3]["shorthand"]
UNIT_TYPE_TO_INDEX[SCOUT] = 3
DEMOLISHER = CONFIG["unitInformation"][4]["shorthand"]
UNIT_TYPE_TO_INDEX[DEMOLISHER] = 4
INTERCEPTOR = CONFIG["unitInformation"][5]["shorthand"]
UNIT_TYPE_TO_INDEX[INTERCEPTOR] = 5
REMOVE = CONFIG["unitInformation"][6]["shorthand"]
UNIT_TYPE_TO_INDEX[REMOVE] = 6
UPGRADE = CONFIG["unitInformation"][7]["shorthand"]
UNIT_TYPE_TO_INDEX[UPGRADE] = 7

def add_unit_to_state(state, unit_type, loc, upgraded, health=None):
  state.game_map.add_unit(unit_type, loc)

  if upgraded == True:
    state.game_map[loc][0].upgrade()

    if health == None:
      if unit_type == WALL:
        state.game_map[loc][0].health = CONFIG['unitInformation'][0]['upgrade']['startHealth']
      elif unit_type == SUPPORT:
        state.game_map[loc][0].health = CONFIG['unitInformation'][1]['upgrade']['startHealth']
      elif unit_type == TURRET:
        state.game_map[loc][0].health = CONFIG['unitInformation'][2]['upgrade']['startHealth']

def get_single_attack_result(game_state_str, attack_str, config_str):
    handle = ctypes.CDLL("./engine.so")     

    handle.get_single_attack_result.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
    handle.get_single_attack_result.restype = ctypes.c_void_p

    handle.free_string.argtypes = [ctypes.c_void_p]
    handle.free_string.restype = None
    
    res = handle.get_single_attack_result(ctypes.c_char_p(str.encode(game_state_str)), 
                                   ctypes.c_char_p(str.encode(attack_str)), 
                                   ctypes.c_char_p(str.encode(config_str)))

    result = ctypes.cast(res, ctypes.c_char_p).value.decode("utf-8")
    handle.free_string(res)
    return result