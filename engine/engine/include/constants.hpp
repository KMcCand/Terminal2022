#include <unordered_map>
#include <string>

// Defines the size of the arena - this will never change over the course of
// the game
#define ARENA_SIZE 28

// Defines constants for all the unit types that are present in the game.
#ifndef UNIT_TYPE_H
#define UNIT_TYPE_H

enum UnitType { SCOUT, INTERCEPTOR, DEMOLISHER, WALL, DESTRUCTOR, SUPPORT };

inline std::unordered_map<UnitType, int> UNIT_INDEX_CONFIG {
    { UnitType::WALL, 0 }, { UnitType::SUPPORT, 1 },
    { UnitType::DESTRUCTOR, 2}, { UnitType::SCOUT, 3 },
    { UnitType::DEMOLISHER, 4 }, {UnitType::INTERCEPTOR, 5}
};

#endif

// Defines the edges of the arena
#ifndef ARENA_EDGES_H
#define ARENA_EDGES_H

enum ArenaEdge { TOP_LEFT, TOP_RIGHT, BOTTOM_LEFT, BOTTOM_RIGHT };

#endif

// Defines all the resource types that are available in the game
#ifndef RESOURCE_TYPE_H
#define RESOURCE_TYPE_H

enum ResourceType { MP, SP };

#endif

// Defines the players in the game
#ifndef PLAYER_TYPE_H
#define PLAYER_TYPE_H

enum PlayerType { PLAYER, OPPONENT };

#endif

// Defines all directions that a mobile unit can move in
#ifndef DIRECTION_TYPE_H
#define DIRECTION_TYPE_H

enum Direction { UP, RIGHT, DOWN, LEFT };
enum DirectionType {VERTICAL, HORIZONTAL};

inline std::unordered_map<Direction, DirectionType> DIRECTION_TYPE_MAP {
    { UP, VERTICAL }, { DOWN, VERTICAL },
    { LEFT, HORIZONTAL }, { RIGHT, HORIZONTAL }
};

#endif