#include <iostream>
#include <vector>
#include <list>
#include <unordered_set>

#include <math.h>
#include <assert.h>

#include "constants.hpp"
#include "../lib/json/single_include/nlohmann/json.hpp"

#ifndef LOCATION_H
#define LOCATION_H


class Location {
public:
    int x;
    int y;

    Location(int i, int j) {
        x = i;
        y = j;
    }

    bool operator==(const Location &other) const {
        return (x == other.x && y == other.y);
    }
};

// Define a format for printing out a location object
std::ostream &operator<<(std::ostream &out, Location loc);

/* 
 * Implement a custom hash function for a location object. This uses the Cantor
 * Pairing Function - more details can be found at
 *
 * https://en.wikipedia.org/wiki/Pairing_function#Cantor_pairing_function
 */
namespace std {
    template<>
    struct hash<Location> {
        size_t operator()(const Location &loc) const {
            return (size_t) (1/2 * (loc.x + loc.y) * (loc.x + loc.y + 1) + loc.y);
        }
    };
}

#endif

Direction get_direction_to_loc(Location loc1, Location loc2);

bool in_arena_bounds(Location loc, int arena_size);
float distance(Location loc1, Location loc2);

std::vector<Location> get_edge_locations(ArenaEdge edge, int arena_size);
std::vector<Location> get_all_board_locations(int arena_size);

UnitType unit_type_from_string(std::string unit_type_string);
ArenaEdge arena_edge_from_string(std::string arena_edge_string);
PlayerType player_type_from_string(std::string player_type_string);