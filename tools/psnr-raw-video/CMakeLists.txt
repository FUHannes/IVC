#===== cmake file =====

set( PROJECT_NAME      psnrRaw )
set( PROJECT_VERSION   1.0     )


#----- minimum required cmake version -----
cmake_minimum_required( VERSION 3.10 FATAL_ERROR )

#----- project name -----
project( ${PROJECT_NAME} VERSION ${PROJECT_VERSION} )

#----- build type -----
set( default_build_type "Release" )
if( NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES )
  message( STATUS "Setting build type to '${default_build_type}' as none was specified." )
  set( CMAKE_BUILD_TYPE "${default_build_type}" CACHE
    STRING "Choose the type of build." FORCE )
  # Set the possible values of build type for cmake-gui
  set_property( CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS
    "Release" "Debug" "MinSizeRel" "RelWithDebInfo" )  
endif()
if( NOT CMAKE_CONFIGURATION_TYPES AND
    NOT CMAKE_BUILD_TYPE STREQUAL "Debug" AND
    NOT CMAKE_BUILD_TYPE STREQUAL "Release" AND
    NOT CMAKE_BUILD_TYPE STREQUAL "MinSizeRel" AND
    NOT CMAKE_BUILD_TYPE STREQUAL "RelWithDebInfo" )
  message( SEND_ERROR
    " Build type '${CMAKE_BUILD_TYPE}' is not supported.\n"
    " Choose one of: 'Debug' 'Release' 'MinSizeRel' 'RelWithDebInfo'"
    )
endif()

#----- executable name -----
if( CMAKE_BUILD_TYPE STREQUAL "Debug" )
  set( EXE_NAME      ${PROJECT_NAME}d  )
elseif( CMAKE_BUILD_TYPE STREQUAL "RelWithDebInfo" )
  set( EXE_NAME      ${PROJECT_NAME}p )
elseif( CMAKE_BUILD_TYPE STREQUAL "MinSizeRel" )
  set( EXE_NAME      ${PROJECT_NAME}m )
else()
  set( EXE_NAME      ${PROJECT_NAME} )
endif()

#----- set c++11 -----
set( CMAKE_CXX_STANDARD          11 )
set( CMAKE_CXX_STANDARD_REQUIRED ON )

#----- compiler options -----
if( MSVC )
  add_compile_options( /W4 /WX )
  add_compile_options( /MP )
  add_compile_options( /arch:AVX2 )
  add_compile_options( $<$<CONFIG:Release>:/Oi> )
  add_compile_options( $<$<CONFIG:Release>:/Ot> )
else()
  add_compile_options( -Wall -Wextra -pedantic -Werror )
  add_compile_options( -mavx2 )
  add_compile_options( $<$<CONFIG:Release>:-Ofast> )
  add_compile_options( $<$<CONFIG:Release>:-funroll-loops> )
endif()

#----- source files -----
file( GLOB SRC_FILES "src/*.cpp" )
file( GLOB INC_FILES "src/*.h" )

#----- executable -----
add_executable( ${EXE_NAME} ${SRC_FILES} ${INC_FILES} )

#----- executable folder -----
set_target_properties( ${EXE_NAME}
  PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/bin/${CMAKE_CXX_COMPILER_ID}-${CMAKE_CXX_COMPILER_VERSION}" )

#----- use ccache -----
find_program( CCACHE_FOUND ccache )
if( CCACHE_FOUND )
  message( STATUS "ccache found. using it." )
  set_property( GLOBAL PROPERTY RULE_LAUNCH_COMPILE ccache )
  set_property( GLOBAL PROPERTY RULE_LAUNCH_LINK    ccache )
endif()

#----- use folders in IDEs for projects -----
set_property( GLOBAL PROPERTY USE_FOLDERS ON )


