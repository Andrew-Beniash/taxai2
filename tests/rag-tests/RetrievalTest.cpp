#include <gtest/gtest.h>
#include <faiss/IndexFlat.h>
#include <vector>
#include <string>
#include <chrono>
#include <iostream>
#include <fstream>
#include <sstream>
#include <random>
#include <filesystem>

/**
 * Test suite for evaluating FAISS retrieval performance and accuracy
 * for the Tax Law Assistant's RAG system.
 * 
 * This test validates vector search capabilities, including:
 * - Indexing performance
 * - Search accuracy 
 * - Search performance under load
 * - Handling edge cases
 */

namespace fs = std::filesystem;

// Helper class to manage test data
class TestData {
public:
    // Create a synthetic test dataset with tax-related embeddings
    static std::vector<float> generateRandomEmbedding(int dim, unsigned int seed) {
        std::vector<float> embedding(dim);
        std::mt19937 gen(seed);
        std::uniform_real_distribution<float> dis(-1.0, 1.0);
        
        for (int i = 0; i < dim; i++) {
            embedding[i] = dis(gen);
        }
        
        // Normalize the vector
        float norm = 0.0f;
        for (float val : embedding) {
            norm += val * val;
        }
        norm = std::sqrt(norm);
        
        for (float& val : embedding) {
            val /= norm;
        }
        
        return embedding;
    }
    
    static void generateTestDataset(
        int numVectors, 
        int dim, 
        std::vector<std::vector<float>>& embeddings,
        std::vector<std::string>& metadata
    ) {
        embeddings.clear();
        metadata.clear();
        
        for (int i = 0; i < numVectors; i++) {
            embeddings.push_back(generateRandomEmbedding(dim, i));
            
            // Generate fake tax law document metadata
            std::ostringstream ss;
            ss << "Tax Code Section " << (1000 + i) << ": ";
            
            // Alternate between different types of tax documents
            switch (i % 5) {
                case 0: ss << "Income Tax Provision"; break;
                case 1: ss << "Capital Gains Regulation"; break;
                case 2: ss << "Deduction Eligibility"; break;
                case 3: ss << "Tax Credit Rules"; break;
                case 4: ss << "Filing Requirements"; break;
            }
            
            metadata.push_back(ss.str());
        }
    }
};

class FAISSRetrievalTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup test parameters
        dim = 128;  // Embedding dimension
        numDocs = 1000;  // Number of test documents
        
        // Generate test data
        TestData::generateTestDataset(numDocs, dim, embeddings, metadata);
        
        // Initialize FAISS index
        index = new faiss::IndexFlatL2(dim);
        
        // Add vectors to the index
        for (const auto& embedding : embeddings) {
            index->add(1, embedding.data());
        }
    }
    
    void TearDown() override {
        delete index;
    }
    
    int dim;
    int numDocs;
    faiss::IndexFlatL2* index;
    std::vector<std::vector<float>> embeddings;
    std::vector<std::string> metadata;
};

// Test basic indexing functionality
TEST_F(FAISSRetrievalTest, BasicIndexing) {
    EXPECT_EQ(index->ntotal, numDocs) << "Index should contain all documents";
    EXPECT_EQ(index->d, dim) << "Index dimension should match embedding dimension";
}

// Test search functionality
TEST_F(FAISSRetrievalTest, BasicSearch) {
    // Search for a known vector - should return itself as the nearest neighbor
    int queryIdx = 42;  // Choose any index within range
    std::vector<float> queryVec = embeddings[queryIdx];
    
    int k = 5;  // Number of neighbors to retrieve
    std::vector<float> distances(k);
    std::vector<faiss::idx_t> indices(k);
    
    // Perform the search
    index->search(1, queryVec.data(), k, distances.data(), indices.data());
    
    // The closest result should be the query vector itself with near-zero distance
    EXPECT_EQ(indices[0], queryIdx) << "First result should be the query vector itself";
    EXPECT_NEAR(distances[0], 0.0f, 1e-5) << "Distance to self should be close to zero";
}

// Test search performance
TEST_F(FAISSRetrievalTest, SearchPerformance) {
    // Generate a new random query vector
    std::vector<float> queryVec = TestData::generateRandomEmbedding(dim, 12345);
    
    int k = 10;  // Number of neighbors to retrieve
    std::vector<float> distances(k);
    std::vector<faiss::idx_t> indices(k);
    
    // Measure search time
    auto start = std::chrono::high_resolution_clock::now();
    
    // Perform the search
    index->search(1, queryVec.data(), k, distances.data(), indices.data());
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    
    // Search should be fast (typically under 1ms for this index size)
    std::cout << "Search time: " << duration << " microseconds" << std::endl;
    EXPECT_LT(duration, 1000) << "Search should take less than 1ms";
    
    // Results should be sorted by distance
    for (int i = 1; i < k; i++) {
        EXPECT_LE(distances[i-1], distances[i]) 
            << "Results should be sorted by increasing distance";
    }
}

// Test batch search performance
TEST_F(FAISSRetrievalTest, BatchSearchPerformance) {
    // Generate 100 random query vectors
    int numQueries = 100;
    int k = 5;
    
    std::vector<std::vector<float>> queryVecs;
    for (int i = 0; i < numQueries; i++) {
        queryVecs.push_back(TestData::generateRandomEmbedding(dim, 10000 + i));
    }
    
    // Flatten the query vectors for FAISS
    std::vector<float> flatQueries;
    for (const auto& vec : queryVecs) {
        flatQueries.insert(flatQueries.end(), vec.begin(), vec.end());
    }
    
    std::vector<float> distances(numQueries * k);
    std::vector<faiss::idx_t> indices(numQueries * k);
    
    // Measure batch search time
    auto start = std::chrono::high_resolution_clock::now();
    
    // Perform batch search
    index->search(numQueries, flatQueries.data(), k, distances.data(), indices.data());
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    
    std::cout << "Batch search time for " << numQueries << " queries: " 
              << duration << " milliseconds" << std::endl;
    
    // Calculate average time per query
    double avgTimePerQuery = static_cast<double>(duration) / numQueries;
    std::cout << "Average time per query: " << avgTimePerQuery << " milliseconds" << std::endl;
    
    // Batch search should be efficient (typically under 10ms per query for this index size)
    EXPECT_LT(avgTimePerQuery, 10.0) 
        << "Average search time should be less than 10ms per query";
}

// Test handling of large indices
TEST_F(FAISSRetrievalTest, LargeIndexHandling) {
    // Only run this test if we have enough memory
    // Create a larger index
    int largeDim = dim;
    int largeNumDocs = 10000;  // 10x more documents
    
    // Generate larger test data
    std::vector<std::vector<float>> largeEmbeddings;
    std::vector<std::string> largeMetadata;
    TestData::generateTestDataset(largeNumDocs, largeDim, largeEmbeddings, largeMetadata);
    
    // Create a new index
    faiss::IndexFlatL2 largeIndex(largeDim);
    
    // Add vectors to the index
    auto start = std::chrono::high_resolution_clock::now();
    
    // Flatten the vectors for batch addition
    std::vector<float> flatVectors;
    for (const auto& vec : largeEmbeddings) {
        flatVectors.insert(flatVectors.end(), vec.begin(), vec.end());
    }
    
    // Add all vectors at once
    largeIndex.add(largeNumDocs, flatVectors.data());
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start).count();
    
    std::cout << "Time to index " << largeNumDocs << " vectors: " 
              << duration << " milliseconds" << std::endl;
    
    EXPECT_EQ(largeIndex.ntotal, largeNumDocs) 
        << "Large index should contain all documents";
    
    // Test search on the large index
    std::vector<float> queryVec = TestData::generateRandomEmbedding(largeDim, 12345);
    int k = 10;
    std::vector<float> distances(k);
    std::vector<faiss::idx_t> indices(k);
    
    auto searchStart = std::chrono::high_resolution_clock::now();
    largeIndex.search(1, queryVec.data(), k, distances.data(), indices.data());
    auto searchEnd = std::chrono::high_resolution_clock::now();
    auto searchDuration = std::chrono::duration_cast<std::chrono::milliseconds>(searchEnd - searchStart).count();
    
    std::cout << "Search time on large index: " << searchDuration << " milliseconds" << std::endl;
    
    // Search should be reasonably fast even with a large index (typically under 20ms)
    EXPECT_LT(searchDuration, 20) 
        << "Search on large index should take less than 20ms";
}

// Test FAISS index serialization and loading
TEST_F(FAISSRetrievalTest, IndexSerializationAndLoading) {
    // Create a temporary file to store the index
    std::string tempFile = "temp_index.faiss";
    
    // Write index to file
    try {
        std::ofstream out(tempFile, std::ios::binary);
        if (!out.is_open()) {
            FAIL() << "Could not open file for writing: " << tempFile;
        }
        
        // Use faiss::write_index to serialize the index
        faiss::write_index(index, out);
        out.close();
        
        // Verify file was created
        ASSERT_TRUE(fs::exists(tempFile)) << "Index file should have been created";
        
        // Load index from file
        std::ifstream in(tempFile, std::ios::binary);
        if (!in.is_open()) {
            FAIL() << "Could not open file for reading: " << tempFile;
        }
        
        // Read the index
        faiss::Index* loadedIndex = faiss::read_index(in.rdbuf());
        in.close();
        
        // Check the loaded index
        EXPECT_EQ(loadedIndex->ntotal, index->ntotal) 
            << "Loaded index should have the same number of vectors";
        EXPECT_EQ(loadedIndex->d, index->d) 
            << "Loaded index should have the same dimension";
        
        // Test search on the loaded index
        std::vector<float> queryVec = TestData::generateRandomEmbedding(dim, 12345);
        int k = 5;
        
        std::vector<float> distancesOriginal(k);
        std::vector<faiss::idx_t> indicesOriginal(k);
        index->search(1, queryVec.data(), k, distancesOriginal.data(), indicesOriginal.data());
        
        std::vector<float> distancesLoaded(k);
        std::vector<faiss::idx_t> indicesLoaded(k);
        loadedIndex->search(1, queryVec.data(), k, distancesLoaded.data(), indicesLoaded.data());
        
        // The loaded index should return the same results as the original
        for (int i = 0; i < k; i++) {
            EXPECT_EQ(indicesOriginal[i], indicesLoaded[i]) 
                << "Loaded index should return same indices as original";
            EXPECT_NEAR(distancesOriginal[i], distancesLoaded[i], 1e-5) 
                << "Loaded index should return same distances as original";
        }
        
        // Clean up
        delete loadedIndex;
    } catch (const std::exception& e) {
        FAIL() << "Exception during index serialization test: " << e.what();
    }
    
    // Clean up temporary file
    if (fs::exists(tempFile)) {
        fs::remove(tempFile);
    }
}

// Main function to run the tests
int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
