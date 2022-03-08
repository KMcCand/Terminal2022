ENGINE_FILES =\
	engine/src/engine.cpp \
	engine/src/common.cpp \
	engine/src/game_state.cpp \
	engine/src/navigation.cpp \
	engine/src/game_unit.cpp \
	engine/src/game_map.cpp 

ENGINE_INTEGRATION_TESTS = \
	tests.integration.simple_attacks \
	tests.integration.self_destruct_attacks

PERFORMANCE_TESTS = \
	tests.performance.large_attack_few_defenses \
	tests.performance.small_attack_many_defenses \
	tests.performance.large_attack_many_defenses \
	tests.performance.demolisher_line_strategies \
	tests.performance.very_long_path_interceptors \
	tests.performance.various_real_strategies \

default:
	gcc -std=c++17 -lstdc++ -fPIC -shared -o engine.so $(ENGINE_FILES) -O3

performance-tests:
	@echo Running performance tests...
	python3 -m unittest $(PERFORMANCE_TESTS)

integration-tests:
	@echo Compiling game engine...
	gcc -std=c++17 -lstdc++ -fPIC -shared -o engine.so $(ENGINE_FILES) -O3
	@echo Running engine integration tests...
	python3 -m unittest $(ENGINE_INTEGRATION_TESTS)