"""
embedding_model.py

This module handles the conversion of text to embeddings using sentence transformers.
It provides functionality to convert sentence-transformers models to ONNX format for
high-performance inference and integrates with the C++ FAISS indexing system.

Key features:
- Convert text to embeddings using sentence-transformers
- Export sentence-transformers models to ONNX format
- Batch processing for efficient embedding generation
- Integration with FAISS indexing via C++ bindings
"""

import os
import numpy as np
import torch
from typing import List, Dict, Union, Optional
from sentence_transformers import SentenceTransformer
import onnxruntime as ort
import logging
from transformers import AutoTokenizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmbeddingModel:
    """
    Class to handle text to embedding conversion using sentence-transformers
    with support for ONNX export and optimization.
    """
    
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2", 
        use_onnx: bool = True,
        onnx_path: Optional[str] = None,
        device: str = "cpu"
    ):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model to use
            use_onnx: Whether to use ONNX for inference
            onnx_path: Path to save/load the ONNX model (default: derived from model_name)
            device: Device to run the model on ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.use_onnx = use_onnx
        self.device = device
        
        # Set up default ONNX path if not provided
        if onnx_path is None:
            # Create directory if it doesn't exist
            os.makedirs("models", exist_ok=True)
            self.onnx_path = os.path.join("models", f"{model_name.replace('/', '_')}.onnx")
        else:
            self.onnx_path = onnx_path
        
        # Load the model
        self._load_model()
    
    def _load_model(self):
        """Load the appropriate model based on configuration"""
        if self.use_onnx:
            if os.path.exists(self.onnx_path):
                logger.info(f"Loading ONNX model from {self.onnx_path}")
                self._load_onnx_model()
            else:
                logger.info(f"ONNX model not found at {self.onnx_path}, creating one...")
                self._load_pytorch_model()
                self._export_to_onnx()
                self._load_onnx_model()
        else:
            logger.info(f"Loading PyTorch model {self.model_name}")
            self._load_pytorch_model()
    
    def _load_pytorch_model(self):
        """Load the PyTorch sentence-transformers model"""
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.tokenizer = self.model.tokenizer
            
            # Store the model's embedding dimension
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"PyTorch model loaded with embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load PyTorch model: {str(e)}")
            raise
    
    def _export_to_onnx(self):
        """Export the PyTorch model to ONNX format"""
        try:
            logger.info(f"Exporting model to ONNX format at {self.onnx_path}")
            
            # Sample input for tracing
            sample_text = ["This is a sample sentence for ONNX export."]
            
            # Create a dummy batch
            inputs = self.tokenizer(
                sample_text,
                padding=True,
                truncation=True,
                return_tensors="pt"
            ).to(self.device)
            
            # Get the model components
            encoder = self.model._modules['0']
            pooling = self.model._modules['1']
            
            # Trace and export
            with torch.no_grad():
                torch.onnx.export(
                    encoder,                                # PyTorch model
                    (inputs['input_ids'], 
                     inputs['attention_mask'],
                     inputs.get('token_type_ids', None)),  # Model inputs
                    self.onnx_path,                         # Output file
                    export_params=True,                     # Store model weights
                    opset_version=11,                       # ONNX version
                    do_constant_folding=True,               # Optimize constants
                    input_names=['input_ids',               # Input names
                                 'attention_mask', 
                                 'token_type_ids'],
                    output_names=['token_embeddings'],      # Output names
                    dynamic_axes={                          # Dynamic axes
                        'input_ids': {0: 'batch_size', 1: 'sequence_length'},
                        'attention_mask': {0: 'batch_size', 1: 'sequence_length'},
                        'token_type_ids': {0: 'batch_size', 1: 'sequence_length'},
                        'token_embeddings': {0: 'batch_size', 1: 'sequence_length'}
                    }
                )
            
            logger.info("ONNX export completed successfully")
        except Exception as e:
            logger.error(f"Failed to export model to ONNX: {str(e)}")
            raise
    
    def _load_onnx_model(self):
        """Load the ONNX model for inference"""
        try:
            # Set up ONNX runtime session
            providers = ['CUDAExecutionProvider'] if self.device == 'cuda' else ['CPUExecutionProvider']
            self.onnx_session = ort.InferenceSession(self.onnx_path, providers=providers)
            
            # Load tokenizer from original model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Determine embedding dimension from ONNX model outputs
            model_outputs = self.onnx_session.get_outputs()
            self.embedding_dim = model_outputs[0].shape[2]  # Should match the embedding dimension
            
            logger.info(f"ONNX model loaded with embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load ONNX model: {str(e)}")
            raise
    
    def embed_text(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings with shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])
            
        # Process in batches for memory efficiency
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            if self.use_onnx:
                batch_embeddings = self._embed_with_onnx(batch_texts)
            else:
                batch_embeddings = self._embed_with_pytorch(batch_texts)
                
            all_embeddings.append(batch_embeddings)
        
        # Concatenate all batches
        return np.vstack(all_embeddings)
    
    def _embed_with_pytorch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using PyTorch model"""
        with torch.no_grad():
            embeddings = self.model.encode(
                texts, 
                convert_to_numpy=True,
                normalize_embeddings=True
            )
        return embeddings
    
    def _embed_with_onnx(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using ONNX model"""
        # Tokenize the input texts
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="np"
        )
        
        # Prepare inputs for ONNX session
        onnx_inputs = {
            'input_ids': inputs['input_ids'],
            'attention_mask': inputs['attention_mask']
        }
        
        # Add token_type_ids if present
        if 'token_type_ids' in inputs:
            onnx_inputs['token_type_ids'] = inputs['token_type_ids']
        
        # Run inference
        token_embeddings = self.onnx_session.run(
            None,  # Output names, none means all outputs
            onnx_inputs
        )[0]  # First output is token embeddings
        
        # Apply mean pooling (similar to sentence-transformers)
        input_mask_expanded = np.expand_dims(
            inputs['attention_mask'], axis=-1
        ).astype(np.float32)
        
        # Multiply token embeddings by attention mask and sum
        sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
        
        # Sum attention mask for proper averaging
        sum_mask = np.sum(input_mask_expanded, axis=1)
        
        # Avoid division by zero
        sum_mask = np.clip(sum_mask, a_min=1e-9, a_max=None)
        
        # Average embeddings
        embeddings = sum_embeddings / sum_mask
        
        # Normalize
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embeddings.
        
        Returns:
            Dimension of the embedding vectors
        """
        return self.embedding_dim

    def save_configuration(self, config_path: str):
        """
        Save model configuration to a file.
        
        Args:
            config_path: Path to save configuration
        """
        config = {
            'model_name': self.model_name,
            'use_onnx': self.use_onnx,
            'embedding_dim': self.embedding_dim,
            'onnx_path': self.onnx_path,
        }
        
        import json
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    @classmethod
    def from_configuration(cls, config_path: str, device: str = 'cpu'):
        """
        Load model from a saved configuration.
        
        Args:
            config_path: Path to load configuration from
            device: Device to run the model on
            
        Returns:
            Initialized EmbeddingModel instance
        """
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return cls(
            model_name=config['model_name'],
            use_onnx=config['use_onnx'],
            onnx_path=config['onnx_path'],
            device=device
        )


# Text chunking utilities for document processing
def chunk_text(
    text: str, 
    chunk_size: int = 256, 
    chunk_overlap: int = 64
) -> List[str]:
    """
    Split text into overlapping chunks for embedding.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum number of characters per chunk
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # If text is shorter than chunk_size, return it as a single chunk
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Find the end of the current chunk
        end = start + chunk_size
        
        # Adjust end to not cut words
        if end < len(text):
            # Look for a space or punctuation to end the chunk
            while end > start + chunk_size - 50 and end < len(text) and text[end] not in ' .,:;!?\n':
                end += 1
            
            # If we went too far, just cut at the max chunk size
            if end >= start + chunk_size + 50:
                end = start + chunk_size
        else:
            end = len(text)
        
        # Add the chunk
        chunks.append(text[start:end].strip())
        
        # Move to next chunk with overlap
        start = end - chunk_overlap
    
    return chunks


# Utility function for processing documents into chunks and embeddings
def process_document(
    embedding_model: EmbeddingModel,
    doc_id: str,
    title: str,
    text: str,
    chunk_size: int = 256,
    chunk_overlap: int = 64
) -> Dict[str, Union[List[str], np.ndarray]]:
    """
    Process a document into chunks and embeddings.
    
    Args:
        embedding_model: EmbeddingModel instance
        doc_id: Document identifier
        title: Document title
        text: Document text
        chunk_size: Maximum number of characters per chunk
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        Dictionary with chunks and their embeddings
    """
    # Chunk the document
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    
    # Skip empty documents
    if not chunks:
        return {
            'doc_id': doc_id,
            'title': title,
            'chunks': [],
            'embeddings': np.array([])
        }
    
    # Generate embeddings for chunks
    embeddings = embedding_model.embed_text(chunks)
    
    return {
        'doc_id': doc_id,
        'title': title,
        'chunks': chunks,
        'embeddings': embeddings
    }


# Main function for testing
def main():
    """Test the embedding model functionality"""
    # Test texts
    texts = [
        "Income tax is imposed on individuals and entities by governments.",
        "Tax deductions reduce taxable income, while tax credits reduce taxes owed.",
        "The Internal Revenue Service (IRS) is responsible for collecting federal taxes in the U.S."
    ]
    
    # Initialize the model
    model = EmbeddingModel(
        model_name="all-MiniLM-L6-v2",
        use_onnx=True,
        device="cpu"
    )
    
    # Generate embeddings
    embeddings = model.embed_text(texts)
    
    # Print results
    print(f"Generated {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
    print(f"First embedding: {embeddings[0][:5]}...")  # Print first 5 dimensions of first embedding
    
    # Test document processing
    doc = {
        'doc_id': 'IRS-2023-01',
        'title': 'Tax Treatment of Cryptocurrency',
        'text': '''
        Virtual currency transactions are taxable by law just like transactions in any other property. 
        Taxpayers transacting in virtual currency may have to report those transactions on their tax returns.
        
        Virtual currency, as generally defined, is a digital representation of value that functions as a medium 
        of exchange, a unit of account, and/or a store of value. Virtual currency that has an equivalent 
        value in real currency, or that acts as a substitute for real currency, is referred to as 
        "convertible" virtual currency.
        
        The sale or exchange of convertible virtual currency, or the use of convertible virtual currency 
        to pay for goods or services in a real-world economy transaction, has tax consequences that may 
        result in a tax liability.
        '''
    }
    
    processed_doc = process_document(
        embedding_model=model,
        doc_id=doc['doc_id'],
        title=doc['title'],
        text=doc['text']
    )
    
    print(f"Processed document into {len(processed_doc['chunks'])} chunks")
    print(f"First chunk: {processed_doc['chunks'][0][:50]}...")
    print(f"Embedding shape: {processed_doc['embeddings'].shape}")


if __name__ == "__main__":
    main()
