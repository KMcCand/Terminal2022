#include <iostream>
#include <fstream>
#include <sstream>

#include "common.hpp"
#include "constants.hpp"

#ifndef GAME_UNIT_H
#define GAME_UNIT_H

class GameUnit {
public:
    UnitType unit_type;
    nlohmann::json config;
    float health;
    float max_health;
    float attack_damage_tower;
    float attack_damage_walker;
    float player_breach_damage;
    float cost;
    float attack_range;
    float speed;
    float self_destruct_damage_walker;
    float self_destruct_damage_tower;
    float self_destruct_range;
    float self_destruct_steps_required;
    float shield_range;
    float shield_per_unit;
    float shield_bonus_per_y;
    PlayerType player_index;
    bool pending_removal;
    bool upgraded;
    Location location = Location(-1, -1);
    
    GameUnit(UnitType _unit_type, nlohmann::json _config, PlayerType _player_index);

    void update_health(float _health);
    void upgrade(void);

    bool operator==(const GameUnit &other) const {
        return (unit_type   == other.unit_type &&
                health      == other.health &&
                location    == other.location);
    }
};

#endif