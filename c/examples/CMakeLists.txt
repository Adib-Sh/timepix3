add_executable(THLrun THLrun.c)
target_link_libraries(THLrun katherine)

add_executable(THLrun2 THLrun2.c)
target_link_libraries(THLrun2 katherine)

add_executable(THLrun2_exclude800 THLrun2_exclude800.c)
target_link_libraries(THLrun2_exclude800 katherine)

add_executable(THLrun_frame_exclude800 THLrun_frame_exclude800.c)
target_link_libraries(THLrun_frame_exclude800 katherine)

