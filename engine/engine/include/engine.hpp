#include <iostream>
#include <algorithm>
#include <string>

#include "constants.hpp"

#include "game_unit.hpp"
#include "game_map.hpp"
#include "game_state.hpp"
#include "navigation.hpp"

extern "C" char *get_single_attack_result(char *input, char *attack, char *config);
extern "C" void free_string(void *str);

/**
 * Struct containing all the necessary information about an attacking unit.
 * Note that units of the same type at the same location will be represented
 * by distinct structs.
 */
struct AttackUnitData {
    GameUnit unit;
    PlayerType owner_type;
    Location start;
    ArenaEdge target_edge;
    DirectionType last_direction_type;
    std::unordered_set<Location> shielded_by_locations;
    int frames_since_move = 0;
    int next_index_along_path = 0;
    bool reached_edge = false;

    // We can take advantage that two units spawned in the same location,
    // with the same target edge, last direction type, and unit type
    // will take exactly the same path. Note that for two different unit
    // types this might not be true because their speeds might differ.
    bool operator==(const AttackUnitData& other) const {
        return other.unit.unit_type == unit.unit_type &&
               other.target_edge == target_edge &&
               other.start == start;
    }
};

/**
 * Implement a very sketchy hash function for AttackUnitData for now -
 * this can be improved later if needed.
 */
namespace std {
    template<>
    struct hash<AttackUnitData> {
        size_t operator()(const AttackUnitData &unit_data) const {
            return unit_data.unit.unit_type * 39 + unit_data.start.x * 53 + unit_data.start.y * 67;
        }
    };
}

/**
 * Struct representing an attack. This is simply a vector of AttackUnitData structs
 * associated with each attacking unit. Both the player and opponent attacking units
 * are contained within this vector.
 */
struct Attack {
    std::vector<AttackUnitData> attack_data;
};

class Engine {
public:
    Engine(GameState _game_state, Attack _attack);

    /**
     * Simulate the round of the game engine. This function runs the attack
     * in the current game state of the engine, returning the results as
     * a map. The resulting map will contain the following keys.
     * 
     *   - player_points_scored: total number of points scored by the player
     * 
     *   - opponent_points_scored: total number of points scored by the opponent
     * 
     *   - player_total_damage_caused: total damage (including structures not fully
     *                                 destroyed) caused by the player. This essentially
     *                                 represents the cost for the opponent to rebuild
     *                                 their defenses to their prior state.
     * 
     *   - opponent_total_damage_caused: total damage caused by the opponent.
     * 
     *   - player_destroyed_damage_caused: damaged caused by the player, counting only
     *                                     defenses that were fully destroyed.
     * 
     *   - opponent_destroyed_damage_caused: damaged caused by the opponent, counting
     *                                       only defenses that were fully destroyed.
     * 
     * Note that the "damage" fields are calculated based on the cost of
     * defensive units, and will depend on the particular game configs
     * of the game state.
     */
    std::unordered_map<std::string, float> simulate_round();
private:
    /**
     * Step forward a single frame of the game in the engine. This functino is
     * responsible for moving/attacking units, handling scoring, self-destructing,
     * etc. Mutates the internal state of the Engine.
     */
    void step_next_frame();

    /**
     * Updates the cached_paths field of the Engine. This function is called
     * whenever required by step_next_frame.
     */
    void update_all_paths();

    /**
     * Helper function to cause the self destruct of the attacking unit
     * corresponding to self_destruct_index in the attack (an Attack is
     * composed of a vector of AttackUnitData structs). Notably, self-
     * destructing does not currently damage enemy mobile units, and
     * will need to be implemented in the future. Stationary units will
     * however be damaged if they are in range.
     */
    void cause_self_destruct(int self_destruct_index);

    /**
     * Updates the health of mobile units within range of a support.
     * Recall that each mobile unit can only be shielded one time by
     * each support (but shielding stacks for multiple supports).
     */
    void apply_shielding_to_relevent_units();

    /**
     * Causes all mobile units to attack. They will target both stationary
     * and mobile units according to the rules laid out on the terminal
     * website.
     */
    void all_mobile_units_attack();

    /**
     * Causes all destructors to attack according to the rules laid out on
     * the terminal website.
     */
    void all_destructors_attack();

    // If we know that the attack consists only of offensive units from a single
    // player, we can speed up the simulation function significantly.
    bool player_only_attack = true;
    bool opponent_only_attack = true;

    // Game state associated with this engine instance
    GameState game_state;

    // Attack associated with this engine instance
    Attack attack;

    // Each engine has its own navigator, which is used to compute paths for
    // attacking units. As stationary structures are destroyed, paths will
    // need to be recomputed for each attack unit.
    Navigator navigator;

    // Indicates that we need to recompute the paths for attack units. This
    // is used within the step_next_frame function.
    bool paths_outdated = true;

    // We maintain a set of key locations used throughout the engine. Because
    // defensive structures form a small percentage of the total squares on the
    // board, it is more efficient to maintain a set of the current locations
    // than to iterate through every tile on the board.
    std::unordered_set<Location> stationary_unit_locations;
    std::unordered_set<Location> destructor_locations;
    std::unordered_set<Location> support_locations;

    // Mapping from a Location and ArenaEdge to a path. Because multiple units are often
    // spawned in the same location, and the path generated from a given location and
    // target edge will always be the same, caching these paths can speed up the navigation 
    // process of the game engine significantly.
    std::unordered_map<AttackUnitData, std::vector<Location>> cached_paths;

    // Set of indices in the attack_data to delete. This field is updated constantly
    // and modified within the step_next_frame() function.
    //
    // It is essential that this be a set and not a vector. There is an edge case where
    // multiple units can self destruct at once, which can add any index to delete
    // multiple times into this container. If a vector is used, this will crash the program.
    std::unordered_set<int> attack_indices_to_delete;

    // Set of indices in the attack_data to self destruct. This field is updated constantly
    // and modified within the step_next_frame() function.
    std::unordered_set<int> attack_self_destruct_indices;

    // Set of locations of stationary structures to delete. This field is updated constantly
    // and modified within the step_next_frame() function.
    std::unordered_set<Location> structure_locations_to_delete;

    // Fields that are adjusted throughout the lifetime of the engine and used to return
    // the results of the simulation in the simulate_round() function.
    int player_points_scored = 0;
    int opponent_points_scored = 0;
    float player_destroyed_damage_caused = 0;
    float opponent_destroyed_damage_caused = 0;
    float player_total_damage_caused = 0;
    float opponent_total_damage_caused = 0;

    // Constant values used throughout lifetime of the engine. These are computed once
    // here at the initialization of the game engine as a small optimization (these
    // values are used very frequently).
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

