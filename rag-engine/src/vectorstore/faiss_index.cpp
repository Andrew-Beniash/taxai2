/**
 * faiss_index.cpp
 * 
 * Implements the FAISS (Facebook AI Similarity Search) vector indexing and search
 * for the tax law RAG system. This file provides high-performance similarity search
 * capabilities for retrieving relevant tax law documents based on query embeddings.
 * 
 * Key features:
 * - Fast vector similarity search using FAISS C++ library
 * - Support for multiple index types (Flat L2, HNSW, IVF)
 * - Thread-safe search and index operations
 * - Memory-mapped index for large datasets
 */

#include <faiss/IndexFlat.h>
#include <faiss/IndexHNSW.h>
#include <faiss/IndexIVFFlat.h>
#include <faiss/index_io.h>
#include <faiss/gpu/GpuIndexFlat.h>
#include <faiss/gpu/StandardGpuResources.h>
#include <vector>
#include <string>
#include <iostream>
#include <mutex>
#include <fstream>
#include <unordered_map>
#include <memory>

/**
 * Class that wraps FAISS to provide vector search capabilities
 * for the tax law retrieval system.
 */
class VectorSearch {
public:
    /**
     * Constructor for VectorSearch
     * 
     * @param dim The dimensionality of vectors to be indexed
     * @param index_type Type of index: "flat", "hnsw", or "ivf"
     * @param use_gpu Whether to use GPU acceleration if available
     */
    VectorSearch(int dim, const std::string& index_type = "flat", bool use_gpu = false) 
        : dimension(dim), index_type(index_type), use_gpu(use_gpu) {
        
        initialize();
    }

    /**
     * Destructor to clean up resources
     */
    ~VectorSearch() {
        if (index != nullptr) {
            delete index;
        }
        
        if (gpu_index != nullptr) {
            delete gpu_index;
        }
        
        if (gpu_resources != nullptr) {
            delete gpu_resources;
        }
    }

    /**
     * Initialize the FAISS index based on specified parameters
     */
    void initialize() {
        std::lock_guard<std::mutex> lock(mutex_);
        
        // Create appropriate index based on type
        if (index_type == "flat") {
            index = new faiss::IndexFlatL2(dimension);
        } 
        else if (index_type == "hnsw") {
            // HNSW parameters: dimension, M (connections per layer), efConstruction
            faiss::IndexFlatL2* quantizer = new faiss::IndexFlatL2(dimension);
            index = new faiss::IndexHNSW2Level(quantizer, dimension, 32, 64);
        } 
        else if (index_type == "ivf") {
            // IVF parameters: quantizer, dimension, number of centroids
            faiss::IndexFlatL2* quantizer = new faiss::IndexFlatL2(dimension);
            index = new faiss::IndexIVFFlat(quantizer, dimension, 100, faiss::METRIC_L2);
            
            // IVF requires training
            trained = false;
        } 
        else {
            std::cerr << "Unknown index type: " << index_type << ". Using flat index instead." << std::endl;
            index = new faiss::IndexFlatL2(dimension);
        }
        
        // Set up GPU resources if requested and available
        if (use_gpu) {
            try {
                gpu_resources = new faiss::gpu::StandardGpuResources();
                gpu_index = faiss::gpu::index_cpu_to_gpu(gpu_resources, 0, index);
                
                // Clean up CPU index if GPU conversion successful
                delete index;
                index = nullptr;
                
                std::cout << "Using GPU acceleration for vector search" << std::endl;
            } catch (const std::exception& e) {
                std::cerr << "Failed to initialize GPU resources: " << e.what() << std::endl;
                std::cerr << "Falling back to CPU implementation" << std::endl;
                use_gpu = false;
                
                // Keep using CPU index
                if (gpu_resources != nullptr) {
                    delete gpu_resources;
                    gpu_resources = nullptr;
                }
                
                if (gpu_index != nullptr) {
                    delete gpu_index;
                    gpu_index = nullptr;
                }
            }
        }
    }

    /**
     * Train the index if required (IVF indices need training)
     * 
     * @param training_vectors Vector of training data as flat float array
     * @param n Number of training vectors
     * @return True if training succeeded, false otherwise
     */
    bool train(const float* training_vectors, size_t n) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if (index_type != "ivf") {
            // Only IVF indices need training
            trained = true;
            return true;
        }
        
        try {
            if (use_gpu && gpu_index != nullptr) {
                faiss::gpu::GpuIndexIVFFlat* gpu_ivf_index = 
                    dynamic_cast<faiss::gpu::GpuIndexIVFFlat*>(gpu_index);
                if (gpu_ivf_index) {
                    gpu_ivf_index->train(n, training_vectors);
                }
            } else if (index != nullptr) {
                faiss::IndexIVFFlat* ivf_index = dynamic_cast<faiss::IndexIVFFlat*>(index);
                if (ivf_index) {
                    ivf_index->train(n, training_vectors);
                }
            }
            
            trained = true;
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Training failed: " << e.what() << std::endl;
            return false;
        }
    }

    /**
     * Add vectors to the index
     * 
     * @param vectors Flat array of vectors to add
     * @param n Number of vectors to add
     * @param ids Optional vector IDs (if not provided, sequential IDs are assigned)
     * @return True if vectors were added successfully, false otherwise
     */
    bool addVectors(const float* vectors, size_t n, const int64_t* ids = nullptr) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if (index_type == "ivf" && !trained) {
            std::cerr << "IVF index needs training before adding vectors" << std::endl;
            return false;
        }
        
        try {
            if (use_gpu && gpu_index != nullptr) {
                if (ids != nullptr) {
                    gpu_index->add_with_ids(n, vectors, ids);
                } else {
                    gpu_index->add(n, vectors);
                }
            } else if (index != nullptr) {
                if (ids != nullptr) {
                    index->add_with_ids(n, vectors, ids);
                } else {
                    index->add(n, vectors);
                }
            }
            
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Failed to add vectors: " << e.what() << std::endl;
            return false;
        }
    }

    /**
     * Search for similar vectors
     * 
     * @param query Query vector
     * @param k Number of results to return
     * @param distances Output vector to store distances
     * @param indices Output vector to store indices
     * @return True if search succeeded, false otherwise
     */
    bool search(const float* query, size_t k, float* distances, int64_t* indices) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        if ((use_gpu && gpu_index == nullptr) || (!use_gpu && index == nullptr)) {
            std::cerr << "No valid index for search" << std::endl;
            return false;
        }
        
        // IVF specific settings - nprobe controls search accuracy vs speed
        if (index_type == "ivf") {
            if (use_gpu) {
                faiss::gpu::GpuIndexIVFFlat* gpu_ivf_index = 
                    dynamic_cast<faiss::gpu::GpuIndexIVFFlat*>(gpu_index);
                if (gpu_ivf_index) {
                    gpu_ivf_index->nprobe = 10; // Adjust based on performance needs
                }
            } else {
                faiss::IndexIVFFlat* ivf_index = dynamic_cast<faiss::IndexIVFFlat*>(index);
                if (ivf_index) {
                    ivf_index->nprobe = 10; // Adjust based on performance needs
                }
            }
        }
        
        try {
            if (use_gpu && gpu_index != nullptr) {
                gpu_index->search(1, query, k, distances, indices);
            } else if (index != nullptr) {
                index->search(1, query, k, distances, indices);
            }
            
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Search failed: " << e.what() << std::endl;
            return false;
        }
    }

    /**
     * Save the index to a file
     * 
     * @param filename Path to save the index
     * @return True if save succeeded, false otherwise
     */
    bool saveIndex(const std::string& filename) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        try {
            if (use_gpu && gpu_index != nullptr) {
                // Convert GPU index to CPU for saving
                faiss::Index* cpu_index = faiss::gpu::index_gpu_to_cpu(gpu_index);
                faiss::write_index(cpu_index, filename.c_str());
                delete cpu_index;
            } else if (index != nullptr) {
                faiss::write_index(index, filename.c_str());
            } else {
                return false;
            }
            
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Failed to save index: " << e.what() << std::endl;
            return false;
        }
    }

    /**
     * Load an index from a file
     * 
     * @param filename Path to the index file
     * @return True if load succeeded, false otherwise
     */
    bool loadIndex(const std::string& filename) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        try {
            // Clean up existing indices
            if (index != nullptr) {
                delete index;
                index = nullptr;
            }
            
            if (gpu_index != nullptr) {
                delete gpu_index;
                gpu_index = nullptr;
            }
            
            // Load index from file
            index = faiss::read_index(filename.c_str());
            
            // Convert to GPU if needed
            if (use_gpu) {
                gpu_resources = new faiss::gpu::StandardGpuResources();
                gpu_index = faiss::gpu::index_cpu_to_gpu(gpu_resources, 0, index);
                
                delete index;
                index = nullptr;
            }
            
            // Determine index type based on the loaded index
            if (dynamic_cast<faiss::IndexFlatL2*>(use_gpu ? nullptr : index)) {
                index_type = "flat";
            } else if (dynamic_cast<faiss::IndexHNSW2Level*>(use_gpu ? nullptr : index)) {
                index_type = "hnsw";
            } else if (dynamic_cast<faiss::IndexIVFFlat*>(use_gpu ? nullptr : index)) {
                index_type = "ivf";
            }
            
            trained = true; // Saved index is always trained
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Failed to load index: " << e.what() << std::endl;
            return false;
        }
    }

    /**
     * Get the number of vectors in the index
     * 
     * @return Number of vectors in the index
     */
    size_t getSize() const {
        if (use_gpu && gpu_index != nullptr) {
            return gpu_index->ntotal;
        } else if (index != nullptr) {
            return index->ntotal;
        }
        
        return 0;
    }

    /**
     * Get the dimension of vectors in the index
     * 
     * @return Vector dimension
     */
    int getDimension() const {
        return dimension;
    }

private:
    // Index parameters
    int dimension;
    std::string index_type;
    bool use_gpu;
    bool trained = false;
    
    // FAISS indices
    faiss::Index* index = nullptr;
    faiss::gpu::GpuResources* gpu_resources = nullptr;
    faiss::Index* gpu_index = nullptr;
    
    // Thread safety
    std::mutex mutex_;
};

/**
 * Document metadata storage class to maintain the mapping between
 * FAISS vector IDs and document information.
 */
class DocumentStore {
public:
    /**
     * Add document metadata
     * 
     * @param id Vector ID in FAISS
     * @param doc_id Document ID (e.g., IRS publication number)
     * @param title Document title
     * @param section Section or paragraph reference
     * @param snippet Text snippet corresponding to the vector
     */
    void addDocument(int64_t id, const std::string& doc_id, const std::string& title, 
                     const std::string& section, const std::string& snippet) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        DocumentInfo info;
        info.doc_id = doc_id;
        info.title = title;
        info.section = section;
        info.snippet = snippet;
        
        docs[id] = info;
    }
    
    /**
     * Get document metadata by vector ID
     * 
     * @param id Vector ID in FAISS
     * @return Document information or nullptr if not found
     */
    const DocumentInfo* getDocument(int64_t id) const {
        auto it = docs.find(id);
        if (it != docs.end()) {
            return &(it->second);
        }
        
        return nullptr;
    }
    
    /**
     * Save document metadata to a file
     * 
     * @param filename File to save metadata
     * @return True if save succeeded, false otherwise
     */
    bool saveMetadata(const std::string& filename) const {
        std::lock_guard<std::mutex> lock(mutex_);
        
        try {
            std::ofstream file(filename);
            if (!file.is_open()) {
                return false;
            }
            
            // Write header
            file << "id,doc_id,title,section,snippet\n";
            
            // Write each document
            for (const auto& entry : docs) {
                file << entry.first << ",";
                file << entry.second.doc_id << ",";
                
                // Handle commas in fields by quoting
                file << "\"" << entry.second.title << "\",";
                file << "\"" << entry.second.section << "\",";
                file << "\"" << entry.second.snippet << "\"\n";
            }
            
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Failed to save metadata: " << e.what() << std::endl;
            return false;
        }
    }
    
    /**
     * Load document metadata from a file
     * 
     * @param filename File to load metadata from
     * @return True if load succeeded, false otherwise
     */
    bool loadMetadata(const std::string& filename) {
        std::lock_guard<std::mutex> lock(mutex_);
        
        try {
            std::ifstream file(filename);
            if (!file.is_open()) {
                return false;
            }
            
            // Clear existing data
            docs.clear();
            
            // Read header line
            std::string header;
            std::getline(file, header);
            
            // Read document entries
            std::string line;
            while (std::getline(file, line)) {
                // Parse CSV (simple implementation)
                int64_t id;
                DocumentInfo info;
                
                // TODO: Implement proper CSV parsing with quotes handling
                // For now, this is a simplistic approach
                
                size_t pos = line.find(',');
                id = std::stoll(line.substr(0, pos));
                line = line.substr(pos + 1);
                
                pos = line.find(',');
                info.doc_id = line.substr(0, pos);
                line = line.substr(pos + 1);
                
                // Handle quoted fields
                // This is a simplified approach and doesn't handle all CSV edge cases
                if (line[0] == '"') {
                    line = line.substr(1);
                    pos = line.find("\",");
                    info.title = line.substr(0, pos);
                    line = line.substr(pos + 2);
                } else {
                    pos = line.find(',');
                    info.title = line.substr(0, pos);
                    line = line.substr(pos + 1);
                }
                
                if (line[0] == '"') {
                    line = line.substr(1);
                    pos = line.find("\",");
                    info.section = line.substr(0, pos);
                    line = line.substr(pos + 2);
                } else {
                    pos = line.find(',');
                    info.section = line.substr(0, pos);
                    line = line.substr(pos + 1);
                }
                
                if (line[0] == '"') {
                    line = line.substr(1);
                    pos = line.find_last_of('"');
                    info.snippet = line.substr(0, pos);
                } else {
                    info.snippet = line;
                }
                
                docs[id] = info;
            }
            
            return true;
        } catch (const std::exception& e) {
            std::cerr << "Failed to load metadata: " << e.what() << std::endl;
            return false;
        }
    }
    
    /**
     * Get the number of documents in the store
     * 
     * @return Number of documents
     */
    size_t size() const {
        return docs.size();
    }
    
private:
    struct DocumentInfo {
        std::string doc_id;  // Document identifier (e.g., IRS publication number)
        std::string title;   // Document title
        std::string section; // Section or paragraph reference
        std::string snippet; // Text snippet
    };
    
    std::unordered_map<int64_t, DocumentInfo> docs;
    mutable std::mutex mutex_;
};

/**
 * Main entry point for testing the FAISS index
 */
#ifdef STANDALONE_TEST
int main() {
    // Test vector dimensionality
    const int dim = 768; // Typical for sentence-transformers
    
    // Create a vector search instance
    VectorSearch search(dim, "flat", false);
    
    // Example vectors (random data for testing)
    const int num_vectors = 1000;
    std::vector<float> vectors(num_vectors * dim);
    for (int i = 0; i < num_vectors * dim; i++) {
        vectors[i] = static_cast<float>(rand()) / RAND_MAX;
    }
    
    // Add vectors to the index
    std::cout << "Adding vectors..." << std::endl;
    search.addVectors(vectors.data(), num_vectors);
    
    // Create a test query vector
    std::vector<float> query(dim);
    for (int i = 0; i < dim; i++) {
        query[i] = static_cast<float>(rand()) / RAND_MAX;
    }
    
    // Search for similar vectors
    const int k = 5; // Number of results to return
    std::vector<float> distances(k);
    std::vector<int64_t> indices(k);
    
    std::cout << "Searching..." << std::endl;
    search.search(query.data(), k, distances.data(), indices.data());
    
    // Print results
    std::cout << "Search results:" << std::endl;
    for (int i = 0; i < k; i++) {
        std::cout << "Result " << i << ": Vector ID " << indices[i] 
                  << ", Distance: " << distances[i] << std::endl;
    }
    
    // Save the index to a file
    std::cout << "Saving index..." << std::endl;
    search.saveIndex("tax_law_index.faiss");
    
    // Document store test
    DocumentStore docs;
    docs.addDocument(1, "IRS-2023-01", "Tax Treatment of Cryptocurrency", 
                     "Section 1.2", "Cryptocurrency is treated as property for tax purposes.");
    docs.addDocument(2, "IRS-2023-02", "Small Business Deductions", 
                     "Section A", "Small businesses may deduct certain expenses.");
    
    std::cout << "Saving document metadata..." << std::endl;
    docs.saveMetadata("tax_law_docs.csv");
    
    return 0;
}
#endif
