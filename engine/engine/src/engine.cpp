#include <iostream>
#include <string>

#include "../include/engine.hpp"
#include "../include/game_state.hpp"

/**
 * Takes in a serialized representation of an attack and builds an Attack
 * struct. 
 * 
 * @param string_rep - string representation of the attack 
 *        config - json object containing the game configs
 * 
 * @return an Attack struct constructed from the string representation
 */
Attack attack_from_json(std::string string_rep, nlohmann::json config) {
    nlohmann::json json = nlohmann::json::parse(string_rep);
    
    int attack_size = json["attack_size"].get<int>();
    std::vector<AttackUnitData> unit_data;
    
    for (int i = 0; i < attack_size; i++) {
        Location start = Location(json["attack"][i]["start_x"].get<int>(), (int) json["attack"][i]["start_y"].get<int>());

        PlayerType player_index = player_type_from_string(json["attack"][i]["player_index"].get<std::string>());
        UnitType unit_type = unit_type_from_string(json["attack"][i]["unit_type"].get<std::string>());
        ArenaEdge target_edge = arena_edge_from_string(json["attack"][i]["target_edge"].get<std::string>());

        GameUnit unit = GameUnit(unit_type, config, player_index);
        unit.location = start;
        unit_data.push_back({ unit, player_index, start, target_edge, HORIZONTAL, {} });
    }

    return {unit_data};
}

/**
 * External bindings that can be called from python. Note that the result value in get_attack_result
 * is dynamically allocated. This value is return to python, and python is responsible for calling
 * free_string() on that returned value to avoid any memory leaks.
 */
extern "C" {
    char *get_single_attack_result(char *game_state_str, char *attack_str, char *config_str) {
        std::string rep = game_state_str;
        nlohmann::json config = nlohmann::json::parse(config_str);
        GameState state = GameState(rep, config);

        Attack attack = attack_from_json(attack_str, config);
        Engine engine = Engine(state, attack);

        std::unordered_map<std::string, float> result = engine.simulate_round();
        std::stringstream ss;
        ss << "{";
        for (auto& pair: result) {
            ss << "\"" << pair.first << "\"" << ": " << "\"" << pair.second << "\"" << ", ";
        }

        std::string s = ss.str();
        s.pop_back();
        s.pop_back();
        s.append("}");

        char *str_result = (char *) malloc(s.size() + 1);

        strcpy(str_result, s.c_str());
        return str_result;
    }

    void free_string(void *str) {
        free(str);
    }
}

Engine::Engine(GameState _game_state, Attack _attack) : game_state(_game_state) {
    game_state = _game_state;
    attack = _attack;
    navigator = Navigator();
}

std::unordered_map<std::string, float> Engine::simulate_round() {
    for (int i = 0; i < 28; i++) {
        for (int j = 0; j < 28; j++) {
            Location loc = Location(i, j);

            if (!in_arena_bounds(loc, ARENA_SIZE)) {
                continue;
            }

            if (game_state.contains_stationary_unit(loc)) {
                GameUnit& unit = game_state.get_units(loc)[0];
                stationary_unit_locations.insert(loc);

                if (unit.unit_type == SUPPORT) {
                    support_locations.insert(loc);
                }

                if (unit.unit_type == DESTRUCTOR) {
                    destructor_locations.insert(loc);
                }
            }
        }
    }

    for (AttackUnitData& unit_data : attack.attack_data) {
        if (unit_data.owner_type == PLAYER) {
            opponent_only_attack = false;
        } else {
            player_only_attack = false;
        }
    }

    while (attack.attack_data.size() > 0) {
        step_next_frame();
    }

    std::unordered_map<std::string, float> result;

    // Aggregate the results of the round into a single dictionary to
    // be returned.
    result["player_points_scored"] = player_points_scored;
    result["opponent_points_scored"] = opponent_points_scored;
    result["player_total_damage_caused"] = player_total_damage_caused;
    result["opponent_total_damage_caused"] = opponent_total_damage_caused;
    result["player_destroyed_damage_caused"] = player_destroyed_damage_caused;
    result["opponent_destroyed_damage_caused"] = opponent_destroyed_damage_caused;

    return result;
}

/**
 * Step forwards a single frame. This updates the current state of the Engine
 * by causing all units to move, attack, and score (if relevent). 
 */
void Engine::step_next_frame() {
    // Computing paths is the most computationally expensive part of the
    // Engine. Thus, they are cached each time they are generated, and only
    // updated when a stationary unit is destroyed.
    if (paths_outdated) {
        update_all_paths();

        for (AttackUnitData& unit_data : attack.attack_data) {
            unit_data.next_index_along_path = 0;
        }

        paths_outdated = false;
    }
    
    // Move all units. This needs to take place before units attack.
    for (int i = 0; i < attack.attack_data.size(); i++) {
        AttackUnitData& unit_data = attack.attack_data[i];
        Location loc = unit_data.unit.location;
        ArenaEdge target_edge = unit_data.target_edge;

        unit_data.frames_since_move += 1;

        std::vector<Location>& path = cached_paths[unit_data];

        if (unit_data.frames_since_move >= 1 / unit_data.unit.speed) {
            std::vector<Location>& edge_locations = edge_location_mapping[target_edge];
            if (std::find(edge_locations.begin(), edge_locations.end(), loc) != edge_locations.end()) {
                // If this unit is ready to move but is currently on the target
                // edge, it needs to be removed as it scores immediately and
                // cannot attack on this turn. We add its index into a list to
                // be removed later - this way we avoid modifying the units
                // list while iterating through it.
                if (unit_data.owner_type == PLAYER) {
                    player_points_scored += 1;
                } else {
                    opponent_points_scored += 1;
                }

                unit_data.reached_edge = true;
                attack_indices_to_delete.insert(i);
            } else {
                if (path.size() == 0 || unit_data.next_index_along_path == path.size()) {
                    // If no path exists or we have reached the end of the path
                    // but not the target edge, this unit needs to self-destruct.
                    attack_self_destruct_indices.insert(i);
                } else {
                    // Normal movement forwards. Take a single step along the
                    // generated path.
                    Location new_loc = path[unit_data.next_index_along_path];
                    unit_data.next_index_along_path += 1;

                    unit_data.unit.location = new_loc;
                    unit_data.frames_since_move = 0;
                    unit_data.last_direction_type = DIRECTION_TYPE_MAP[get_direction_to_loc(loc, new_loc)];
                }
            }
        }
    }
    
    // Apply shielding if relevent
    apply_shielding_to_relevent_units();

    // Have all destructors units attack
    all_destructors_attack();

    // Have all mobile units attack
    all_mobile_units_attack();

    // Self destruct if relevent
    for (int index : attack_self_destruct_indices) {
        if (attack.attack_data[index].unit.health > 0) {
            cause_self_destruct(index);
        }
        
        attack_indices_to_delete.insert(index);
    }

    attack_self_destruct_indices.clear();

    // Remove all mobile units that have scored or died as a result of a self
    // destruct.
    if (attack_indices_to_delete.size() > 0) {
        std::vector<int> indices_to_remove1;
        indices_to_remove1.assign(attack_indices_to_delete.begin(), attack_indices_to_delete.end());
        std::sort(indices_to_remove1.begin(), indices_to_remove1.end());

        for (int i = indices_to_remove1.size() - 1; i >= 0; i--) {
            attack.attack_data.erase(attack.attack_data.begin() + indices_to_remove1[i]);
        }

        attack_indices_to_delete.clear();
    }

    // Remove all dead stationary units
    if (structure_locations_to_delete.size() > 0) {
        paths_outdated = true;
    }

    for (const Location &loc : structure_locations_to_delete) {
        GameUnit& unit = game_state.get_units(loc)[0];
        
        if (unit.player_index == PLAYER) {
            opponent_destroyed_damage_caused += unit.cost;
        } else {
            player_destroyed_damage_caused += unit.cost;
        }

        bool result = game_state.attempt_remove(loc);

        stationary_unit_locations.erase(loc);
        support_locations.erase(loc);
        destructor_locations.erase(loc);
    }

    structure_locations_to_delete.clear();

    // Remove all dead mobile units
    if (attack_indices_to_delete.size() > 0) {
        std::vector<int> indices_to_remove2;
        indices_to_remove2.assign(attack_indices_to_delete.begin(), attack_indices_to_delete.end());
        std::sort(indices_to_remove2.begin(), indices_to_remove2.end());

        for (int i = indices_to_remove2.size() - 1; i >= 0; i--) {
            attack.attack_data.erase(attack.attack_data.begin() + indices_to_remove2[i]);
        }

        attack_indices_to_delete.clear();
    }
}

void Engine::update_all_paths() {
    cached_paths.clear();

    for (AttackUnitData& unit_data : attack.attack_data) {
        Location loc = unit_data.unit.location;
        ArenaEdge target_edge = unit_data.target_edge;
        DirectionType last_direction_type = unit_data.last_direction_type;

        if (cached_paths.find(unit_data) == cached_paths.end()) {
            cached_paths[unit_data] = navigator.get_shortest_path_to_edge(game_state, loc, target_edge, last_direction_type);
        }
    }
}

/**
 * Cause a self destruct event.
 */
void Engine::cause_self_destruct(int self_destruct_index) {
    GameUnit& unit = attack.attack_data[self_destruct_index].unit;

    Location loc = unit.location;
    float self_destruct_range = unit.self_destruct_range;

    for (int i = loc.x - self_destruct_range; i <= loc.x + self_destruct_range; i++) {
        for (int j = loc.y - self_destruct_range; j <= loc.y + self_destruct_range; j++) {
            Location considering = Location(i, j);

            if (!in_arena_bounds(considering, ARENA_SIZE)) {
                continue;
            }

            if (distance(loc, considering) > self_destruct_range) {
                continue;
            }

            if (!game_state.contains_stationary_unit(considering)) {
                continue;
            }

            if (game_state.get_units(considering)[0].health <= 0) {
                continue;
            }

            // Never self-destruct friendly units
            if (game_state.get_units(considering)[0].player_index == attack.attack_data[self_destruct_index].owner_type) {
                continue;
            }
            
            GameUnit& stationary_unit = game_state.get_units(considering)[0];
            float caused_damage = std::min(stationary_unit.health, unit.self_destruct_damage_tower);
            stationary_unit.health -= unit.self_destruct_damage_tower;

            if (stationary_unit.player_index == OPPONENT) {
                player_total_damage_caused += caused_damage / stationary_unit.max_health * stationary_unit.cost;
            } else {
                opponent_total_damage_caused += caused_damage / stationary_unit.max_health * stationary_unit.cost;
            }

            if (stationary_unit.health <= 0) {
                structure_locations_to_delete.insert(considering);
            }
        }
    }

    for (int i = 0; i < attack.attack_data.size(); i++) {
        AttackUnitData& unit_data = attack.attack_data[i];

        // Never self destruct friendly units
        if (unit_data.unit.player_index == attack.attack_data[self_destruct_index].owner_type) {
            continue;
        }

        if (distance(unit_data.unit.location, loc) > self_destruct_range) {
            continue;
        }

        unit_data.unit.health -= unit.self_destruct_damage_walker;

        if (unit_data.unit.health <= 0) {
            attack_indices_to_delete.insert(i);
        }
    }
}

void Engine::apply_shielding_to_relevent_units() {
    for (const Location& loc : support_locations) {
        GameUnit& support_unit = game_state.get_units(loc)[0];

        for (AttackUnitData& unit_data : attack.attack_data) {
            if (distance(loc, unit_data.unit.location) > support_unit.shield_range) {
                continue;
            }

            // We don't receive shielding from our opponent's supports
            if (support_unit.player_index != unit_data.owner_type) {
                continue;
            }

            // Each mobile unit can only receive shielding one time from each support
            if (unit_data.shielded_by_locations.find(loc) != unit_data.shielded_by_locations.end()) {
                continue;
            }

            unit_data.shielded_by_locations.insert(loc);
            unit_data.unit.health += support_unit.shield_per_unit;

            // Apply bonus shielding based on y-position
            if (unit_data.owner_type == PLAYER) {
                unit_data.unit.health += loc.y * support_unit.shield_bonus_per_y;
            } else {
                unit_data.unit.health += (27 - loc.y) * support_unit.shield_bonus_per_y;
            }
        }
    }
}

void Engine::all_mobile_units_attack() {
    std::unordered_map<Location, std::vector<Location>> cached_candidate_stationary_targets;

    for (int i = 0; i < attack.attack_data.size(); i++) {
        AttackUnitData& attacker = attack.attack_data[i];
        
        if (attacker.reached_edge) {
            continue;
        }

        if (!player_only_attack || !opponent_only_attack) {
            std::vector<int> mobile_attack_candidates;
            for (int j = 0; j < attack.attack_data.size(); j++) {
                if (i == j) {
                    continue;
                }
                
                AttackUnitData& target = attack.attack_data[j];

                // Never attack friendly units
                if (attacker.owner_type == target.owner_type) {
                    continue;
                }

                // Never attack dead units
                if (target.unit.health <= 0) {
                    continue;
                }

                // If the target is not in range of the attacker, skip over this target
                if (distance(attacker.unit.location, target.unit.location) > attacker.unit.attack_range) {
                    continue;
                }
                
                mobile_attack_candidates.push_back(j);
            }

            // Always target mobile units first, so do so if any candidate target was found
            if (mobile_attack_candidates.size() > 0) {
                // While sorting, place more optimal targets at the beginning of the vector
                std::sort(mobile_attack_candidates.begin(), mobile_attack_candidates.end(), [this, attacker](int left, int right) {
                    AttackUnitData& left_target = attack.attack_data[left];
                    AttackUnitData& right_target = attack.attack_data[right];

                    float left_dist = distance(attacker.unit.location, left_target.unit.location);
                    float right_dist = distance(attacker.unit.location, right_target.unit.location);

                    // Prioritize closer units
                    if (left_dist < right_dist) {
                        return true;
                    } else if (left_dist > right_dist) {
                        return false;
                    }

                    // Prioritize units with lower health
                    if (left_target.unit.health < right_target.unit.health) {
                        return true;
                    }

                    // Prioritize units closer to the attacker's side of the map
                    if (attacker.owner_type == PLAYER) {
                        if (left_target.unit.location.y < right_target.unit.location.y) {
                            return true;
                        } else if (left_target.unit.location.y > right_target.unit.location.y) {
                            return false;
                        }
                    } else {
                        if (left_target.unit.location.y > right_target.unit.location.y) {
                            return true;
                        } else if (left_target.unit.location.y < right_target.unit.location.y) {
                            return false;
                        }
                    }

                    // We almost never reach here, so just return a value satisfying ordering requirements
                    return left_target.unit.location.x < right_target.unit.location.x;
                });

                int attack_index = mobile_attack_candidates[0];

                attack.attack_data[attack_index].unit.health -= attacker.unit.attack_damage_walker;

                // This unit should be deleted if it is dead
                if (attack.attack_data[attack_index].unit.health <= 0) {
                    if (std::find(attack_indices_to_delete.begin(), attack_indices_to_delete.end(), attack_index) == attack_indices_to_delete.end()) {
                        attack_indices_to_delete.insert(attack_index);
                    }
                }

                continue;
            }
        }
    
        std::vector<Location> stationary_attack_candidates;
        float attack_range = attacker.unit.attack_range;

        if (cached_candidate_stationary_targets.find(attacker.unit.location) != cached_candidate_stationary_targets.end()) {
            stationary_attack_candidates = cached_candidate_stationary_targets[attacker.unit.location];
        } else {
            for (int i = (int) (attacker.unit.location.x - attack_range); i < (int) (attacker.unit.location.x + attack_range + 1); i++) {
                for (int j = (int) (attacker.unit.location.y - attack_range); j < (int) (attacker.unit.location.y + attack_range + 1); j++) {
                    Location loc = Location(i, j);

                    if (!in_arena_bounds(loc, ARENA_SIZE)) {
                        continue;
                    }

                    // Skip this stationary unit if it's out of range
                    if (distance(attacker.unit.location, loc) > attacker.unit.attack_range) {
                        continue;
                    }

                    if (stationary_unit_locations.find(loc) == stationary_unit_locations.end()) {
                        continue;
                    }

                    GameUnit& unit = game_state.get_units(loc)[0];
                    
                    // Never attack a dead unit
                    if (unit.health <= 0) {
                        continue;
                    }

                    // Never attack a friendly unit
                    if (attacker.owner_type == unit.player_index) {
                        continue;
                    }

                    stationary_attack_candidates.push_back(loc);
                }
            }
        }

        if (stationary_attack_candidates.size() > 0) {
            Location best_loc = Location(-1, -1);
            float closest_dist = ARENA_SIZE * 3;
            float smallest_health = 100000;
            int best_y = ARENA_SIZE;

            for (Location& loc : stationary_attack_candidates) {
                GameUnit& unit = game_state.get_units(loc)[0];

                if (unit.health <= 0) {
                    continue;
                }

                int y_val;

                if (attacker.owner_type == PLAYER) {
                    y_val = loc.y;
                } else {
                    y_val = ARENA_SIZE - y_val - 1;
                }

                if (distance(attacker.unit.location, loc) < closest_dist) {
                    best_loc = loc;
                    closest_dist = distance(attacker.unit.location, loc);
                    smallest_health = unit.health;
                    
                    best_y = y_val;
                } else if (distance(attacker.unit.location, loc) == closest_dist) {
                    if (unit.health < smallest_health) {
                        best_loc = loc;
                        closest_dist = distance(attacker.unit.location, loc);
                        smallest_health = unit.health;
                        best_y = y_val;
                    } else if (unit.health == smallest_health) {
                        if (y_val < best_y) {
                            best_loc = loc;
                            closest_dist = distance(attacker.unit.location, loc);
                            smallest_health = unit.health;
                            best_y = y_val;
                        }
                    }
                }
            }

            GameUnit& target = game_state.get_units(best_loc)[0];

            float caused_damage = std::min(attacker.unit.attack_damage_tower, target.health);
            target.health -= attacker.unit.attack_damage_tower;

            if (attacker.owner_type == PLAYER) {
                player_total_damage_caused += caused_damage / target.max_health * target.cost;
            } else {
                opponent_total_damage_caused += caused_damage / target.max_health * target.cost;
            }

            // This unit should be deleted if it is dead
            if (game_state.get_units(best_loc)[0].health <= 0) {
                if (structure_locations_to_delete.find(best_loc) == structure_locations_to_delete.end()) {
                    structure_locations_to_delete.insert(best_loc);
                }
            }
        }
    }
}

void Engine::all_destructors_attack() {
    for (const Location& loc : destructor_locations) {
        GameUnit& stationary_unit = game_state.get_units(loc)[0];
        std::vector<int> mobile_attack_candidates;

        for (int i = 0; i < attack.attack_data.size(); i++) {
            AttackUnitData& target = attack.attack_data[i];

            // Never attack friendly units
            if (stationary_unit.player_index == target.owner_type) {
                continue;
            }

            // Never attack dead units
            if (target.unit.health <= 0) {
                continue;
            }

            // If the target is not in range of the attacker, skip over this target
            if (distance(stationary_unit.location, target.unit.location) > stationary_unit.attack_range) {
                continue;
            }

            mobile_attack_candidates.push_back(i);
        }

        if (mobile_attack_candidates.size() > 0) {
            std::sort(mobile_attack_candidates.begin(), mobile_attack_candidates.end(), [this, stationary_unit](int left, int right) {
                AttackUnitData& left_target = attack.attack_data[left];
                AttackUnitData& right_target = attack.attack_data[right];

                float left_dist = distance(stationary_unit.location, left_target.unit.location);
                float right_dist = distance(stationary_unit.location, right_target.unit.location);

                // Prioritize closer units
                if (left_dist < right_dist) {
                    return true;
                } else if (left_dist > right_dist) {
                    return false;
                }

                // Prioritize units with lower health
                if (left_target.unit.health < right_target.unit.health) {
                    return true;
                }

                // Prioritize units closer to the attacker's side of the map
                if (stationary_unit.player_index == PLAYER) {
                    if (left_target.unit.location.y < right_target.unit.location.y) {
                        return true;
                    } else if (left_target.unit.location.y > right_target.unit.location.y) {
                        return false;
                    }
                } else {
                    if (left_target.unit.location.y > right_target.unit.location.y) {
                        return true;
                    } else if (left_target.unit.location.y < right_target.unit.location.y) {
                        return false;
                    }
                }

                // We almost never reach here, so just return a value satisfying ordering requirements
                return left_target.unit.location.x < right_target.unit.location.x;
            });

            int target_index = mobile_attack_candidates[0];
            attack.attack_data[target_index].unit.health -= stationary_unit.attack_damage_walker;

            // This unit should be deleted if it is dead
            if (attack.attack_data[target_index].unit.health <= 0) {
                if (std::find(attack_indices_to_delete.begin(), attack_indices_to_delete.end(), target_index) == attack_indices_to_delete.end()) {
                    attack_indices_to_delete.insert(target_index);
                }
            }
        }
    }
}