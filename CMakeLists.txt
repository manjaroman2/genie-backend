cmake_minimum_required(VERSION 3.11)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

project(genie-backend)

set(CMAKE_CXX_FLAGS "-Wall -Wno-sign-compare")

set(GUTILS_TOOLS FALSE)
set(GUTILS_TEST FALSE)
set(STATIC_COMPILE TRUE)

set(EXTERN_DIR ${CMAKE_SOURCE_DIR}/Source)

include_directories(${EXTERN_DIR}/genieutils/include)

add_subdirectory(${EXTERN_DIR}/genieutils extern/genieutils)

add_executable(genie-backend main.cpp)
target_link_libraries(genie-backend genieutils)
