#include <unordered_map>

#include "../include/common.hpp"
#include "../include/game_unit.hpp"

GameUnit::GameUnit(UnitType _unit_type, nlohmann::json _config,
                        PlayerType _player_index) {
    nlohmann::json unit_info = 
        _config["unitInformation"][UNIT_INDEX_CONFIG[_unit_type]];

    unit_type = _unit_type;
    config = _config;
    health = unit_info["startHealth"];
    max_health = health;

    if (unit_info.contains("attackDamageTower")) {
        attack_damage_tower = unit_info["attackDamageTower"];
    } else {
        attack_damage_tower = 0;
    }

    if (unit_info.contains("attackDamageWalker")) {
        attack_damage_walker = unit_info["attackDamageWalker"];
    } else {
        attack_damage_walker = 0;
    }

    if (unit_info.contains("playerBreachDamage")) {
        player_breach_damage = unit_info["playerBreachDamage"];
    } else {
        player_breach_damage = 0;
    }

    if (unit_info.contains("cost1")) {
        cost = unit_info["cost1"];
    } else {
        cost = unit_info["cost2"];
    }
    
    if (unit_info.contains("attackRange")) {
        attack_range = unit_info["attackRange"];
    } else {
        attack_range = 0;
    }

    if (unit_info.contains("speed")) {
        speed = unit_info["speed"];
    } else {
        speed = 0;
    }

    if (unit_info.contains("selfDestructDamageWalker")) {
        self_destruct_damage_walker = unit_info["selfDestructDamageWalker"];
    } else {
        self_destruct_damage_walker = 0;
    }

    if (unit_info.contains("selfDestructDamageTower")) {
        self_destruct_damage_tower = unit_info["selfDestructDamageTower"];
    } else {
        self_destruct_damage_tower = 0;
    }

    if (unit_info.contains("selfDestructRange")) {
        self_destruct_range = unit_info["selfDestructRange"];
    } else {
        self_destruct_range = 0;
    }

    if (unit_info.contains("selfDestructStepsRequired")) {
        self_destruct_steps_required = unit_info["selfDestructStepsRequired"];
    } else {
        self_destruct_steps_required = 0;
    }

    if (unit_info.contains("shieldRange")) {
        shield_range = unit_info["shieldRange"];
    } else {
        shield_range = 0;
    }

    if (unit_info.contains("shieldPerUnit")) {
        shield_per_unit = unit_info["shieldPerUnit"];
    } else {
        shield_per_unit = 0;
    }

    if (unit_info.contains("shieldBonusPerY")) {
        shield_bonus_per_y = unit_info["shieldBonusPerY"];
    } else {
        shield_bonus_per_y = 0;
    }
    
    player_index = _player_index;
    pending_removal = false;
    upgraded = false;
    location = Location(-1, -1);
}

void GameUnit::upgrade() {
    nlohmann::json upgrade_info = 
        config["unitInformation"][UNIT_INDEX_CONFIG[unit_type]]["upgrade"];

    if (upgrade_info.contains("startHealth")) {
        health = (float) upgrade_info["startHealth"] - (max_health - health);
        max_health = upgrade_info["startHealth"];
    }

    if (upgrade_info.contains("attackDamageTower")) {
        attack_damage_tower = upgrade_info["attackDamageTower"];
    }

    if (upgrade_info.contains("attackDamageWalker")) {
        attack_damage_walker = upgrade_info["attackDamageWalker"];
    }

    if (upgrade_info.contains("cost1")) {
        cost += (float) upgrade_info["cost1"];
    } else {
        cost += cost;
    }
    
    if (upgrade_info.contains("attackRange")) {
        attack_range = upgrade_info["attackRange"];
    }

    if (upgrade_info.contains("shieldRange")) {
        shield_range = upgrade_info["shieldRange"];
    }

    if (upgrade_info.contains("shieldPerUnit")) {
        shield_per_unit = upgrade_info["shieldPerUnit"];
    } else {
        shield_per_unit = 0;
    }

    if (upgrade_info.contains("shieldBonusPerY")) {
        shield_bonus_per_y = upgrade_info["shieldBonusPerY"];
    }

    upgraded = true;
}

void GameUnit::update_health(float _health) {
    health = _health;
}