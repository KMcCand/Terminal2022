#include <iostream>
#include <string>

#include "constants.hpp"

#include "game_unit.hpp"
#include "game_map.hpp"

#ifndef GAME_STATE_H
#define GAME_STATE_H

class GameState {
public:
    float temp;

    GameState(std::string string_rep, nlohmann::json _config);
    bool contains_stationary_unit(Location loc);
    std::vector<GameUnit>& get_units(Location loc);
    float get_resource(ResourceType resource, PlayerType player);
    bool attempt_spawn(UnitType unit_type, Location loc, PlayerType player_index);
    bool attempt_remove(Location loc);
    bool attempt_upgrade(Location loc);

    int get_value();
private:
    GameMap game_map;
    nlohmann::json config;

    float player_zero_sp;
    float player_one_sp;
    float player_zero_mp;
    float player_one_mp;
};

#endif
