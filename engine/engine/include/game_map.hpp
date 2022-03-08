#include <iostream>
#include <unordered_map>
#include <list>
#include <vector>

#include "common.hpp"
#include "constants.hpp"
#include "game_unit.hpp"

#ifndef GAME_MAP_H
#define GAME_MAP_H

class GameMap {
public:
    GameMap();

    static bool is_player_edge_location(Location loc, int arena_size=ARENA_SIZE);
    static bool is_opponent_edge_location(Location loc, int arena_size=ARENA_SIZE);
    
    std::vector<GameUnit>& get_units(Location loc);
    void add_unit(GameUnit& unit, Location loc);
    void remove_units(Location loc);
private:
    std::unordered_map<Location, std::vector<GameUnit>> units;
};

#endif