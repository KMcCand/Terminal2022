#include <iostream>
#include <list>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <queue>

#include "../include/common.hpp"
#include "../include/navigation.hpp"

std::unordered_map<Location, int> get_distances_from_locations(GameState& game_state, std::vector<Location>& locs, int arena_size);
std::vector<Location> get_valid_neighboring_locations(Location &loc, int arena_size);

int get_idealness(Location loc, std::vector<Location>& target_endpoints, int arena_size);
std::vector<int> get_direction_from_endpoints(std::vector<Location>& endpoints, int arena_size);

struct BFSElement {
    Location loc;
    int distance;
};

std::vector<Location> Navigator::get_shortest_path_to_edge(GameState& game_state, 
                                                          Location start,
                                                          ArenaEdge target_edge,
                                                          DirectionType last_direction_type) {
    if (game_state.contains_stationary_unit(start)) {
        return {};
    }
    
    std::vector<Location> start_as_vector {start};                                                     
    std::unordered_map<Location, int> distances_from_start = get_distances_from_locations(game_state, start_as_vector, ARENA_SIZE);

    std::vector<Location> target_edge_locations = edge_location_mapping[target_edge]; //get_edge_locations(target_edge, ARENA_SIZE);

    std::vector<Location> candidate_targets;
    int closest_edge_dist = ARENA_SIZE * 3;

    for (Location& loc : target_edge_locations) {
        if (distances_from_start.find(loc) == distances_from_start.end()) {
            continue;
        }

        if (distances_from_start[loc] < closest_edge_dist) {
            closest_edge_dist = distances_from_start[loc];
            candidate_targets.clear();
            candidate_targets.push_back(loc);
        } else if (distances_from_start[loc] == closest_edge_dist) {
            candidate_targets.push_back(loc);
        }
    }

    // If there are no candidates that are edge locations, the target becomes the location
    // with the highest idealness value.

    if (candidate_targets.size() == 0) {
        int highest_idealness = -1;

        for (const std::pair<Location, int>& element : distances_from_start) {
            int idealness = get_idealness(element.first, target_edge_locations, ARENA_SIZE);
            if (idealness > highest_idealness) {
                highest_idealness = idealness;
                candidate_targets.clear();
                candidate_targets.push_back(element.first);
            } else if (idealness == highest_idealness) {
                candidate_targets.push_back(element.first);
            }
        }
    }

    // Once we have a vector of potential candidate targets, we can start generating the path.
    std::unordered_map<Location, int> distances_to_targets = get_distances_from_locations(game_state, candidate_targets, ARENA_SIZE);

    std::vector<Location> path;
    Location current = start;
    DirectionType current_direction_type = last_direction_type;

    while (std::find(candidate_targets.begin(), candidate_targets.end(), current) == candidate_targets.end()) {
        Location best_next = current;
        int closest_dist = distances_to_targets[current];

        for (Location& neighbor : get_valid_neighboring_locations(current, ARENA_SIZE)) {
            if (game_state.contains_stationary_unit(neighbor)) {
                continue;
            }

            if (distances_to_targets[neighbor] < closest_dist) {
                closest_dist = distances_to_targets[neighbor];
                best_next = neighbor;
                continue;
            }
            
            if (distances_to_targets[neighbor] > closest_dist) {
                continue;
            }

            if (is_better_move(current, best_next, neighbor, current_direction_type, target_edge)) {
                best_next = neighbor;
            }
        }

        path.push_back(best_next);
        current_direction_type = DIRECTION_TYPE_MAP[get_direction_to_loc(current, best_next)];
        current = best_next;
    }

    return path;
}

bool Navigator::is_better_move(Location origin, Location neighbor1, Location neighbor2, DirectionType last_direction_type, ArenaEdge target_edge) {
    Direction dir1 = get_direction_to_loc(origin, neighbor1);
    Direction dir2 = get_direction_to_loc(origin, neighbor2);

    // If neighbor2 involves moving in a new direction and neighbor1 does not, then neighbor2
    // is by default the better move
    if (DIRECTION_TYPE_MAP[dir2] != last_direction_type &&
        DIRECTION_TYPE_MAP[dir1] == last_direction_type) {
            return true;
    }
    
    if (DIRECTION_TYPE_MAP[dir2] == last_direction_type &&
        DIRECTION_TYPE_MAP[dir1] != last_direction_type) {
            return false;
    }

    // If we get to this point, both moves are on the same axis so we choose the one moving in the
    // direction of the target edge.
    std::vector<Location>& edge_locations = edge_location_mapping[target_edge]; //get_edge_locations(target_edge, ARENA_SIZE);
    std::vector<int> direction_to_edge = get_direction_from_endpoints(edge_locations, ARENA_SIZE);

    if (neighbor2.x == neighbor1.x) {
        if (neighbor2.x > origin.x && direction_to_edge[0] == 1) {
            return true;
        } else if (neighbor2.x < origin.x && direction_to_edge[0] == -1) {
            return true;
        } else {
            return false;
        }
    } else {
        if (neighbor2.y > origin.y && direction_to_edge[1] == 1) {
            return true;
        } else if (neighbor2.y < origin.y && direction_to_edge[1] == -1) {
            return true;
        } else {
            return false;
        }
    }
}

std::unordered_map<Location, int> get_distances_from_locations(GameState& game_state, std::vector<Location>& locs, int arena_size) {
    std::unordered_map<Location, int> result;
    std::queue<BFSElement> bfsQueue;

    for (Location& loc : locs) {
        if (game_state.contains_stationary_unit(loc)) {
            continue;
        }

        bfsQueue.push((struct BFSElement) {.loc = loc, .distance = 0});
    }

    while (bfsQueue.size() > 0) {
        BFSElement& element = bfsQueue.front();
        bfsQueue.pop();

        if (result.find(element.loc) != result.end()) {
            continue;
        }

        result[element.loc] = element.distance;

        for (Location& loc : get_valid_neighboring_locations(element.loc, arena_size)) {
            if (!game_state.contains_stationary_unit(loc)) {
                bfsQueue.push((struct BFSElement) {.loc = loc, .distance = element.distance + 1});
            }
        }
    }

    return result;
}

std::vector<Location> get_valid_neighboring_locations(Location &loc, int arena_size) {
    std::vector<Location> candidates {Location(loc.x + 1, loc.y), Location(loc.x - 1, loc.y),
                                    Location(loc.x, loc.y + 1), Location(loc.x, loc.y - 1)};
    std::vector<Location> result;

    for (Location& loc : candidates) {
        if (in_arena_bounds(loc, arena_size)) {
            result.push_back(loc);
        }
    }

    return result;
}

int get_idealness(Location loc, std::vector<Location>& target_endpoints, int arena_size) {
    // If the location is a target endpoint, return a value that is perfectly ideal
    if (std::find(target_endpoints.begin(), target_endpoints.end(), loc) != target_endpoints.end()) {
        return 1000000;
    }

    std::vector<int> direction = get_direction_from_endpoints(target_endpoints, arena_size);

    int idealness = 0;

    // Idealness calculation is configured such that a more ideal location
    // by y-position always outweights a more ideal x location.

    if (direction[0] == 1) {
        idealness += loc.x;
    } else {
        idealness += (arena_size - loc.x - 1);
    }

    if (direction[1] == 1) {
        idealness += arena_size * loc.y;
    } else {
        idealness += arena_size * (arena_size - loc.y - 1);
    }

    return idealness;
}

/**
 * Returns a direction corresponding to the target endpoints. Top left is [-1, 1],
 * top right is [1, 1], bottom right is [1, -1], and bottom left is [-1, -1].
 */
std::vector<int> get_direction_from_endpoints(std::vector<Location>& endpoints, int arena_size) {
    std::vector<int> result {1, 1};

    if (endpoints[0].x < arena_size / 2) {
        result[0] = -1;
    }

    if (endpoints[0].y < arena_size / 2) {
        result[1] = -1;
    }

    return result;
}