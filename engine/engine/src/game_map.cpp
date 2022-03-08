#include <iostream>
#include <assert.h>
#include <unordered_map>

#include "../include/common.hpp"
#include "../include/constants.hpp"
#include "../include/game_map.hpp"

GameMap::GameMap() {

}

bool GameMap::is_player_edge_location(Location loc, int arena_size) {
    assert(arena_size % 2 == 0);

    int x = loc.x;
    int y = loc.y;

    if (y < 0 || y >= arena_size / 2) {
        return false;
    }

    if (x < 0 || x >= arena_size) {
        return false;
    }

    if (x < arena_size / 2) {
        return y == (arena_size / 2 - x - 1);
    } else {
        return y == (x - arena_size / 2);
    }
}

bool GameMap::is_opponent_edge_location(Location loc, int arena_size) {
    assert(arena_size % 2 == 0);

    int x = loc.x;
    int y = loc.y;

    if (y < 0 || y < arena_size / 2) {
        return false;
    }

    if (x < 0 || x >= arena_size) {
        return false;
    }

    if (x < arena_size / 2) {
        return y == (arena_size / 2 + x);
    } else {
        return y == (arena_size / 2 + (arena_size - x - 1));
    }
}

std::vector<GameUnit>& GameMap::get_units(Location loc) {
    if (units.find(loc) == units.end()) {
        std::vector<GameUnit> new_units;
        units[loc] = new_units;
    }

    return units[loc];
}

void GameMap::add_unit(GameUnit& unit, Location loc) {
    if (units.find(loc) == units.end()) {
        std::vector<GameUnit> new_vector = {};

        units[loc] = new_vector;
    }

    units[loc].push_back(unit);
}

void GameMap::remove_units(Location loc) {
    if (units.find(loc) == units.end()) {
        return;
    }

    units.erase(loc);
}