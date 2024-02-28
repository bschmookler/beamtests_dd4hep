
#
# EICrecon stand alone plugin
#
# Before using this, make sure your environment is set up
# for the EICrecon version you are using. The easiest way
# to do this is to source the bin/eicrecon-this.(c)sh
# script.
#

cmake_minimum_required(VERSION 3.16)
project(CALI_project)

find_package(EICrecon REQUIRED)
find_package(spdlog REQUIRED)

set(CMAKE_CXX_STANDARD ${EICrecon_CXX_STANDARD})

# Automatically determine source file list.
file(GLOB mysourcefiles *.cpp *.cc *.c  *.hpp *.hh *.h)
set( CALI_PLUGIN_SOURCES ${mysourcefiles} )

# Create plugin
add_library(CALI SHARED ${CALI_PLUGIN_SOURCES})
target_link_libraries(CALI EICrecon::rootfile_plugin)
set_target_properties(CALI PROPERTIES PREFIX "" OUTPUT_NAME "CALI" SUFFIX ".so")
target_compile_definitions(CALI PUBLIC HAVE_PODIO)

# Install plugin USER_PLUGIN_OUTPUT_DIRECTORY is set depending on EICrecon_MY envar.
install(TARGETS CALI DESTINATION ${USER_PLUGIN_OUTPUT_DIRECTORY} )

