cmake_minimum_required(VERSION 3.10)
project(rag_engine)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(OpenMP REQUIRED)
find_package(Boost REQUIRED COMPONENTS system filesystem thread)

# Include directories
include_directories(
    ${Boost_INCLUDE_DIRS}
    src
)

# Add source files
set(SOURCES
    src/main.cpp
    src/server.cpp
    src/vector_search.cpp
)

# Create executable
add_executable(rag-engine-service ${SOURCES})

# Link libraries
target_link_libraries(rag-engine-service
    OpenMP::OpenMP_CXX
    ${Boost_LIBRARIES}
    -lfaiss
    -lopenblas
)

# Install target
install(TARGETS rag-engine-service DESTINATION bin)
