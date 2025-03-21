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

# Add source files for the main service
set(SOURCES
    src/main.cpp
    src/server.cpp
    src/vector_search.cpp
)

# Create executable for the main RAG service
add_executable(rag-engine-service ${SOURCES})

# Link libraries for the main service
target_link_libraries(rag-engine-service
    OpenMP::OpenMP_CXX
    ${Boost_LIBRARIES}
    -lfaiss
    -lopenblas
)

# Add FAISS wrapper library
set(FAISS_WRAPPER_SOURCES
    src/vectorstore/faiss_index.cpp
)

# Create FAISS wrapper shared library for Python binding
add_library(faiss_wrapper SHARED ${FAISS_WRAPPER_SOURCES})

# Link FAISS wrapper library
target_link_libraries(faiss_wrapper
    -lfaiss
    -lopenblas
)

# Install targets
install(TARGETS rag-engine-service DESTINATION bin)
install(TARGETS faiss_wrapper DESTINATION lib)

# Create a standalone test executable for FAISS index
add_executable(faiss_index_test src/vectorstore/faiss_index.cpp)
target_compile_definitions(faiss_index_test PRIVATE STANDALONE_TEST)
target_link_libraries(faiss_index_test
    -lfaiss
    -lopenblas
)
