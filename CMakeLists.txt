cmake_minimum_required(VERSION 3.3 FATAL_ERROR)

find_package( DD4hep REQUIRED COMPONENTS DDCore DDG4 )
#find_package(Acts REQUIRED COMPONENTS Core PluginIdentification PluginTGeo PluginDD4hep )

# project(cal_prototype)

#-----------------------------------------------------------------------------------
set(lib_name cal_prototype)
dd4hep_add_plugin(${lib_name} SOURCES src/*.cpp)

target_link_libraries(${lib_name}
  PUBLIC DD4hep::DDCore  DD4hep::DDRec
  #ActsCore ActsPluginDD4hep
)

#-----------------------------------------------------------------------------------
install(DIRECTORY compact/
    DESTINATION share/${PROJECT_NAME}/${lib_name}
    FILES_MATCHING PATTERN "*.xml"
)
