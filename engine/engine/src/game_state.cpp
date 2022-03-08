#include <iostream>
#include <assert.h>
#include <list>

#include "../include/common.hpp"
#include "../include/constants.hpp"
#include "../include/game_state.hpp"
#include "../include/game_map.hpp"

GameState::GameState(std::string string_rep, nlohmann::json _config) {
    if (string_rep.size() != 0) {
        nlohmann::json json_rep = nlohmann::json::parse(string_rep);
        int num_units = json_rep["num_stationary_units"];

        for (int i = 0; i < num_units; i++) {
            UnitType unit_type = unit_type_from_string(json_rep["units"][i]["unit_type"].get<std::string>());
            Location loc = Location(json_rep["units"][i]["x"].get<int>(), json_rep["units"][i]["y"].get<int>());
            float health = json_rep["units"][i]["health"].get<float>();
            bool upgraded = json_rep["units"][i]["upgraded"].get<bool>();

            PlayerType player_index;
            if (loc.y < ARENA_SIZE / 2) {
                player_index = PLAYER;
            } else {
                player_index = OPPONENT;
            }

            GameUnit unit = GameUnit(unit_type, _config, player_index);
            unit.location = loc;
            
            if (upgraded) {
                unit.upgrade();
            }

            unit.health = health;
            game_map.add_unit(unit, loc);
        }
    }

    config = _config;
}

int GameState::get_value() {
    return 5;
}

bool GameState::contains_stationary_unit(Location loc) {
    std::vector<GameUnit>& units = game_map.get_units(loc);

    if (units.size() == 1 && (units[0].unit_type == WALL || units[0].unit_type == SUPPORT || units[0].unit_type == DESTRUCTOR)) {
        return true;
    }

    return false;
}

std::vector<GameUnit>& GameState::get_units(Location loc) {
    return game_map.get_units(loc);
}

float GameState::get_resource(ResourceType resource, PlayerType player) {
    if (resource == SP) {
        if (player == PLAYER) {
            return player_zero_sp;
        } else if (player == OPPONENT) {
            return player_one_sp;
        } else {
            assert(false);
        }
    } else if (resource == MP) {
        if (player == PLAYER) {
            return player_zero_mp;
        } else if (player == OPPONENT) {
            return player_one_mp;
        } else {
            assert(false);
        }
    } else {
        assert(false);
    }
}

bool GameState::attempt_spawn(UnitType unit_type, Location loc, PlayerType player_index) {
    if (!in_arena_bounds(loc, ARENA_SIZE)) {
        return false;
    }

    std::vector<GameUnit>& units = game_map.get_units(loc);

    if (contains_stationary_unit(loc)) {
        return false;
    }

    GameUnit new_unit = GameUnit(unit_type, config, player_index);
    new_unit.location = loc;
    game_map.add_unit(new_unit, loc);

    return true;
}

bool GameState::attempt_remove(Location loc) {
    std::vector<GameUnit>& units = game_map.get_units(loc);

    if (units.size() == 0) {
        return false;
    }

    if (units[0].unit_type == WALL || units[0].unit_type == DESTRUCTOR || units[0].unit_type == SUPPORT) {
        game_map.remove_units(loc);
        return true;
    }
    
    game_map.remove_units(loc);
    return false;
}

bool GameState::attempt_upgrade(Location loc) {
    if (!in_arena_bounds(loc, ARENA_SIZE)) {
        return false;
    }

    std::vector<GameUnit>& units = game_map.get_units(loc);

    if (units.size() != 1) {
        return false;
    }

    for (GameUnit& unit: units) {
        if (unit.unit_type != WALL && unit.unit_type != DESTRUCTOR && unit.unit_type != SUPPORT) {
            return false;
        }
    }
    
    units[0].upgrade();
    return true;
}