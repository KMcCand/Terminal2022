#include "../include/constants.hpp"
#include "../include/common.hpp"

// Define a format for printing out a location object
std::ostream &operator<<(std::ostream &out, Location loc) {
    return out << "(" + std::to_string(loc.x) + ", " + std::to_string(loc.y) + ")";
}

Direction get_direction_to_loc(Location loc1, Location loc2) {
    /*
     * This check verifies that the two provided locations are actually
     * adjacent to each other. This is essential - if this check fails, it
     * strongly indicates the game engine is buggy. Leaving this in has
     * been very helpful in tracking down some otherwise very tricky vugs.
     */
    if (abs(loc1.x - loc2.x) + abs(loc1.y - loc2.y) != 1) {
        std::cerr << "Error: locations " << loc1 << " and " << loc2 <<
                        " are not adjacent.\n";
        std::exit(1);
    }

    if (loc1.x == loc2.x) {
        if (loc2.y > loc1.y) {
            return UP;
        } else {
            return DOWN;
        }
    } else {
        if (loc2.x > loc1.x) {
            return RIGHT;
        } else {
            return LEFT;
        }
    }
}

std::vector<Location> get_edge_locations(ArenaEdge edge, int arena_size) {
    switch (edge) {
        case TOP_LEFT: {
            return {Location(0, 14), Location(1, 15), Location(2, 16), Location(3, 17),
                    Location(4, 18), Location(5, 19), Location(6, 20), Location(7, 21),
                    Location(8, 22), Location(9, 23), Location(10, 24), Location(11, 25),
                    Location(12, 26), Location(13, 27)};
        } case TOP_RIGHT: {
            return { Location(14, 27), Location(15, 26), Location(16, 25), Location(17, 24),
                     Location(18, 23), Location(19, 22), Location(20, 21), Location(21, 20),
                     Location(22, 19), Location(23, 18), Location(24, 17), Location(25, 16),
                     Location(26, 15), Location(27, 14) };
        } case BOTTOM_LEFT: {
            return {Location(0, 13), Location(1, 12), Location(2, 11), Location(3, 10),
                    Location(4, 9), Location(5, 8), Location(6, 7), Location(7, 6),
                    Location(8, 5), Location(9, 4), Location(10, 3), Location(11, 2),
                    Location(12, 1), Location(13, 0)};
        } case BOTTOM_RIGHT: {
            return {Location(14, 0), Location(15, 1), Location(16, 2), Location(17, 3),
                    Location(18, 4), Location(19, 5), Location(20, 6), Location(21, 7),
                    Location(22, 8), Location(23, 9), Location(24, 10), Location(25, 11),
                    Location(26, 12), Location(27, 13)};  
        } default: {
            std::cout << edge << "\n";
            throw std::invalid_argument("Invalid edge passed to get_edge_locations.");
        }
    }
}

/*
 * Returns a list of all locations on the board. 
 */
std::vector<Location> get_all_board_locations(int arena_size) {
    std::vector<Location> result;

    for (int i = 0; i < arena_size; i++) {
        for (int j = 0; j < arena_size; j++) {
            Location loc = Location(i, j);

            if (in_arena_bounds(loc, arena_size)) {
                result.push_back(Location(i, j));
            }
        }
    }

    return result;
}

/*
 * Returns true if the given location is within the bounds of an arena of size arena_size
 */
bool in_arena_bounds(Location loc, int arena_size) {
    assert(arena_size % 2 == 0);

    int x = loc.x;
    int y = loc.y;

    if (y < arena_size / 2) {
        if (x < (int) (arena_size / 2 - y - 1)) {
            return false;
        }

        if (x > (int) (arena_size / 2) + y) {
            return false;
        }
    } else {
        if (x < y - (int) (arena_size / 2)) {
            return false;
        }

        if (x > arena_size - 1 - (y - (int) (arena_size / 2))) {
            return false;
        }
    }

    return true;
}

float distance(Location loc1, Location loc2) {
    return sqrt((loc1.x - loc2.x) * (loc1.x - loc2.x) + (loc1.y - loc2.y) * (loc1.y - loc2.y));
}

UnitType unit_type_from_string(std::string unit_type_string) {
    if (unit_type_string == "WALL") {
        return WALL;
    } else if (unit_type_string == "DESTRUCTOR") {
        return DESTRUCTOR;
    } else if (unit_type_string == "SUPPORT") {
        return SUPPORT;
    } else if (unit_type_string == "DEMOLISHER") {
        return DEMOLISHER;
    } else if (unit_type_string == "SCOUT") {
        return SCOUT;
    } else if (unit_type_string == "INTERCEPTOR") {
        return INTERCEPTOR;
    } else {
        throw std::invalid_argument("received invalid unit type type");
    }
}

ArenaEdge arena_edge_from_string(std::string arena_edge_string) {
    if (arena_edge_string == "TOP_RIGHT") {
        return TOP_RIGHT;
    } else if (arena_edge_string == "TOP_LEFT") {
        return TOP_LEFT;
    } else if (arena_edge_string == "BOTTOM_LEFT") {
        return BOTTOM_LEFT;
    } else if (arena_edge_string == "BOTTOM_RIGHT") {
        return BOTTOM_RIGHT;
    } else {
        throw std::invalid_argument("received invalid arena edge type");
    }
}

PlayerType player_type_from_string(std::string player_type_string) {
    if (player_type_string == "PLAYER") {
        return PLAYER;
    } else if (player_type_string == "OPPONENT") {
        return OPPONENT;
    } else {
        throw std::invalid_argument("received invalid player type");
    }
}