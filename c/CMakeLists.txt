cmake_minimum_required(VERSION 3.10)
project(katherine)

# Find HDF5 library
find_package(HDF5 REQUIRED)

# Add HDF5 include directories
include_directories(${HDF5_INCLUDE_DIRS})

set(KATHERINE_SOURCES
    "src/acquisition.c"
    "src/px_config.c"
    "src/config.c"
    "src/device.c"
    "src/status.c"
    "src/udp_nix.c"
    "src/udp_win.c"
    "src/crd.h"
    "src/bitfields.h"
    "src/command_interface.h"
    "src/md.h"
)

set(KATHERINE_HEADERS
    "include/katherine/acquisition.h"
    "include/katherine/config.h"
    "include/katherine/device.h"
    "include/katherine/global.h"
    "include/katherine/katherine.h"
    "include/katherine/px_config.h"
    "include/katherine/px.h"
    "include/katherine/status.h"
    "include/katherine/udp.h"
    "include/katherine/udp_nix.h"
    "include/katherine/udp_win.h"
)

# Create the Katherine library
add_library(katherine SHARED ${KATHERINE_SOURCES} ${KATHERINE_HEADERS})

# Set include directories for the Katherine library
target_include_directories(katherine
    PUBLIC
        $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Link HDF5 to the Katherine library
target_link_libraries(katherine ${HDF5_LIBRARIES})

# On Windows, link to ws2_32
if(WIN32 OR MINGW)
  target_link_libraries(katherine ws2_32)
endif()

# Configure and install the pkg-config file
configure_file(${CMAKE_CURRENT_SOURCE_DIR}/katherine.pc.in katherine.pc @ONLY)

# Install the library, headers, and pkg-config file
install(TARGETS katherine LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES ${KATHERINE_HEADERS} DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/katherine)
install(FILES ${CMAKE_CURRENT_BINARY_DIR}/katherine.pc DESTINATION ${CMAKE_INSTALL_DATAROOTDIR}/pkgconfig)

# Build examples if enabled
if(BUILD_EXAMPLES)
    add_subdirectory(examples)
endif(BUILD_EXAMPLES)