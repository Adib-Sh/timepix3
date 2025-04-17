add_executable(kfind kfind.c)
target_link_libraries(kfind katherine)

add_executable(krun krun.c)
target_link_libraries(krun katherine)

add_executable(Erun Erun.c)
target_link_libraries(Erun katherine)

add_executable(Erun2 Erun2.c)
target_link_libraries(Erun2 katherine)

add_executable(Erun2 Erun3.c)
target_link_libraries(Erun2 katherine)

add_executable(ramping_bias ramping_bias.c)
target_link_libraries(ramping_bias katherine)

add_executable(ramping_bias2 ramping_bias2.c)
target_link_libraries(ramping_bias2 katherine)