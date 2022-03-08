#include <iostream>
#include <list>

#include "constants.hpp"
#include "common.hpp"
#include "game_state.hpp"

#ifndef NAVIGATOR_H
#define NAVIGATOR_H

class Navigator {
public:
    std::vector<Location> get_shortest_path_to_edge(GameState& game_state, 
                                                    Location start,
                                                    ArenaEdge target_edge,
                                                    DirectionType last_direction_type);
private:
    bool is_better_move(Location origin, Location neighbor1, Location neighbor2, 
                        DirectionType last_direction_type, ArenaEdge target_edge);

    // Constant values used throughout lifetime of the navigation.
    // Because these are used extremely frequently, it is most efficient
    // to pre-compute them. 
    std::vector<Location> top_left_edge_locations = get_edge_locations(TOP_LEFT, ARENA_SIZE);
    std::vector<Location> top_right_edge_locations = get_edge_locations(TOP_RIGHT, ARENA_SIZE);
    std::vector<Location> bottom_right_edge_locations = get_edge_locations(BOTTOM_RIGHT, ARENA_SIZE);
    std::vector<Location> bottom_left_edge_locations = get_edge_locations(BOTTOM_LEFT, ARENA_SIZE);

    std::unordered_map<ArenaEdge, std::vector<Location>> edge_location_mapping {
        { TOP_LEFT, top_left_edge_locations }, { TOP_RIGHT, top_right_edge_locations },
        { BOTTOM_LEFT, bottom_left_edge_locations },
        { BOTTOM_RIGHT, bottom_right_edge_locations }
    };
};

#endif