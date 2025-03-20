FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    python3 \
    python3-pip \
    libopenblas-dev \
    liblapack-dev \
    libssl-dev \
    libcurl4-openssl-dev \
    rapidjson-dev \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy CMakeLists.txt and source files
COPY CMakeLists.txt .
COPY src/ src/

# Build the RAG Engine
RUN mkdir -p build && cd build && \
    cmake .. && \
    make -j$(nproc)

# Expose the port for the RAG Engine
EXPOSE 5000

# Run the RAG Engine
CMD ["./build/rag-engine-service"]