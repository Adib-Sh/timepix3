add_executable(kfind kfind.c)
target_link_libraries(kfind katherine)

add_executable(krun krun.c)
target_link_libraries(krun katherine)

add_executable(test test.c)
target_link_libraries(test katherine)

