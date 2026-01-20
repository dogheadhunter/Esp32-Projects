"""
ChromaDB End-to-End Tests

Tests real ChromaDB functionality:
- Collection creation and management
- Document ingestion with embeddings
- Semantic search queries
- Metadata filtering
- Relevance scoring
- Performance benchmarks

Run with: pytest tests/e2e/test_chromadb_e2e.py --run-chromadb -v
"""

import pytest
import time


@pytest.mark.e2e
@pytest.mark.requires_chromadb
class TestChromaDBInitialization:
    """Test ChromaDB initialization and setup"""
    
    def test_chromadb_initialization(self, chromadb_client, e2e_capture_output):
        """Create and persist collection"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "chromadb_initialization",
            "description": "Test ChromaDB client initialization"
        })
        
        # List collections (should be empty or contain only test collections)
        collections = chromadb_client.list_collections()
        
        print(f"✓ ChromaDB client initialized")
        print(f"  Existing collections: {len(collections)}")
        
        # Create a test collection
        collection_name = f"test_init_{int(time.time() * 1000)}"
        collection = chromadb_client.create_collection(
            name=collection_name,
            metadata={"description": "Test collection for E2E tests"}
        )
        
        assert collection is not None, "Failed to create collection"
        assert collection.name == collection_name, "Collection name mismatch"
        
        print(f"  ✓ Created collection: {collection_name}")
        
        # Verify it's in the list
        collections = chromadb_client.list_collections()
        collection_names = [c.name for c in collections]
        assert collection_name in collection_names, "Collection not in list"
        
        print(f"  ✓ Collection appears in list")
        
        # Cleanup
        chromadb_client.delete_collection(collection_name)
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "chromadb_initialization",
            "result": "success"
        })


@pytest.mark.e2e
@pytest.mark.requires_chromadb
class TestChromaDBDocumentIngestion:
    """Test document ingestion and storage"""
    
    def test_chromadb_document_ingestion(
        self,
        chromadb_collection,
        sample_documents,
        e2e_capture_output
    ):
        """Add documents with embeddings"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "chromadb_document_ingestion",
            "description": "Test adding documents to collection"
        })
        
        # Add documents
        ids = [doc["id"] for doc in sample_documents]
        documents = [doc["text"] for doc in sample_documents]
        metadatas = [doc["metadata"] for doc in sample_documents]
        
        print(f"Adding {len(documents)} documents...")
        
        start_time = time.time()
        chromadb_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        duration = time.time() - start_time
        
        print(f"  ✓ Added {len(documents)} documents in {duration:.3f}s")
        
        # Verify count
        count = chromadb_collection.count()
        assert count == len(documents), f"Expected {len(documents)} documents, got {count}"
        
        print(f"  ✓ Collection count: {count}")
        
        # Get all documents
        results = chromadb_collection.get()
        
        assert len(results["ids"]) == len(documents), "Document count mismatch"
        assert set(results["ids"]) == set(ids), "Document IDs mismatch"
        
        print(f"  ✓ All documents retrieved successfully")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "chromadb_document_ingestion",
            "result": "success",
            "documents_added": len(documents),
            "duration": duration
        })


@pytest.mark.e2e
@pytest.mark.requires_chromadb
class TestChromaDBSemanticSearch:
    """Test semantic search capabilities"""
    
    def test_chromadb_semantic_search(
        self,
        chromadb_collection,
        sample_documents,
        e2e_capture_output
    ):
        """Query with text similarity"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "chromadb_semantic_search",
            "description": "Test semantic similarity search"
        })
        
        # Add documents first
        ids = [doc["id"] for doc in sample_documents]
        documents = [doc["text"] for doc in sample_documents]
        metadatas = [doc["metadata"] for doc in sample_documents]
        
        chromadb_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        # Test queries
        queries = [
            ("Tell me about the Vault Dweller", "doc1"),
            ("What is the Brotherhood?", "doc2"),
            ("Pre-war beverages", "doc3")
        ]
        
        for query_text, expected_doc_id in queries:
            print(f"\nQuery: {query_text}")
            
            start_time = time.time()
            results = chromadb_collection.query(
                query_texts=[query_text],
                n_results=3
            )
            duration = time.time() - start_time
            
            assert len(results["ids"]) > 0, f"No results for query: {query_text}"
            assert len(results["ids"][0]) > 0, f"No documents returned for: {query_text}"
            
            top_result_id = results["ids"][0][0]
            top_distance = results["distances"][0][0]
            
            print(f"  ✓ Query completed in {duration:.3f}s")
            print(f"  Top result: {top_result_id} (distance: {top_distance:.4f})")
            
            # Verify expected document is in top 3
            assert expected_doc_id in results["ids"][0], \
                f"Expected {expected_doc_id} in top 3, got {results['ids'][0]}"
            
            e2e_capture_output.log_event("QUERY_COMPLETED", {
                "query": query_text,
                "top_result": top_result_id,
                "distance": top_distance,
                "duration": duration
            })
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "chromadb_semantic_search",
            "result": "success",
            "queries_tested": len(queries)
        })


@pytest.mark.e2e
@pytest.mark.requires_chromadb
class TestChromaDBMetadataFiltering:
    """Test metadata filtering"""
    
    def test_chromadb_metadata_filtering(
        self,
        chromadb_collection,
        sample_documents,
        e2e_capture_output
    ):
        """Filter by metadata (type, region, etc.)"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "chromadb_metadata_filtering",
            "description": "Test metadata-based filtering"
        })
        
        # Add documents
        ids = [doc["id"] for doc in sample_documents]
        documents = [doc["text"] for doc in sample_documents]
        metadatas = [doc["metadata"] for doc in sample_documents]
        
        chromadb_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        # Test filters
        test_filters = [
            ({"type": "lore"}, ["doc1"]),
            ({"type": "faction"}, ["doc2"]),
            ({"region": "California"}, ["doc1"])
        ]
        
        for filter_dict, expected_ids in test_filters:
            print(f"\nFilter: {filter_dict}")
            
            results = chromadb_collection.query(
                query_texts=["General query"],
                n_results=10,
                where=filter_dict
            )
            
            returned_ids = results["ids"][0] if results["ids"] else []
            
            print(f"  ✓ Returned {len(returned_ids)} documents")
            print(f"  IDs: {returned_ids}")
            
            # Verify expected documents are returned
            for expected_id in expected_ids:
                assert expected_id in returned_ids, \
                    f"Expected {expected_id} with filter {filter_dict}, got {returned_ids}"
            
            e2e_capture_output.log_event("FILTER_TESTED", {
                "filter": filter_dict,
                "results_count": len(returned_ids),
                "expected_ids": expected_ids
            })
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "chromadb_metadata_filtering",
            "result": "success",
            "filters_tested": len(test_filters)
        })


@pytest.mark.e2e
@pytest.mark.requires_chromadb
class TestChromaDBRelevanceScoring:
    """Test relevance scoring and ranking"""
    
    def test_chromadb_relevance_scoring(
        self,
        chromadb_collection,
        sample_documents,
        e2e_capture_output
    ):
        """Verify distance scores and ranking"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "chromadb_relevance_scoring",
            "description": "Test relevance scoring accuracy"
        })
        
        # Add documents
        ids = [doc["id"] for doc in sample_documents]
        documents = [doc["text"] for doc in sample_documents]
        metadatas = [doc["metadata"] for doc in sample_documents]
        
        chromadb_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        # Query with exact match text
        query = "The Vault Dweller emerged from Vault 13"
        
        print(f"Query: {query}")
        
        results = chromadb_collection.query(
            query_texts=[query],
            n_results=3
        )
        
        distances = results["distances"][0]
        returned_ids = results["ids"][0]
        
        print(f"\nResults:")
        for i, (doc_id, distance) in enumerate(zip(returned_ids, distances), 1):
            print(f"  {i}. {doc_id}: distance={distance:.4f}")
        
        # Verify top result is doc1 (exact match)
        assert returned_ids[0] == "doc1", f"Expected doc1 as top result, got {returned_ids[0]}"
        
        # Verify distances are sorted (ascending)
        assert distances == sorted(distances), "Distances not sorted correctly"
        
        # Verify top distance is smallest
        assert distances[0] <= distances[-1], "Top result should have smallest distance"
        
        print(f"\n✓ Relevance scoring working correctly")
        print(f"  Top result has smallest distance: {distances[0]:.4f}")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "chromadb_relevance_scoring",
            "result": "success",
            "top_distance": distances[0]
        })


@pytest.mark.e2e
@pytest.mark.requires_chromadb
class TestChromaDBCollectionManagement:
    """Test collection management operations"""
    
    def test_chromadb_collection_management(
        self,
        chromadb_client,
        e2e_capture_output
    ):
        """List, update, delete collections"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "chromadb_collection_management",
            "description": "Test collection CRUD operations"
        })
        
        # Create multiple collections
        collection_names = [
            f"test_mgmt_1_{int(time.time() * 1000)}",
            f"test_mgmt_2_{int(time.time() * 1000)}",
            f"test_mgmt_3_{int(time.time() * 1000)}"
        ]
        
        print("Creating collections...")
        for name in collection_names:
            chromadb_client.create_collection(name=name)
            print(f"  ✓ Created: {name}")
        
        # List collections
        all_collections = chromadb_client.list_collections()
        all_names = [c.name for c in all_collections]
        
        print(f"\n✓ Listed {len(all_collections)} collections")
        
        # Verify our collections are there
        for name in collection_names:
            assert name in all_names, f"Collection {name} not found in list"
        
        # Update collection metadata
        collection = chromadb_client.get_collection(collection_names[0])
        original_metadata = collection.metadata
        
        collection.modify(metadata={"updated": True, "test": "metadata"})
        
        print(f"\n✓ Updated collection metadata")
        
        # Delete collections
        print(f"\nDeleting collections...")
        for name in collection_names:
            chromadb_client.delete_collection(name)
            print(f"  ✓ Deleted: {name}")
        
        # Verify deletion
        all_collections = chromadb_client.list_collections()
        all_names = [c.name for c in all_collections]
        
        for name in collection_names:
            assert name not in all_names, f"Collection {name} still exists after deletion"
        
        print(f"\n✓ All collections deleted successfully")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "chromadb_collection_management",
            "result": "success",
            "collections_managed": len(collection_names)
        })


@pytest.mark.e2e
@pytest.mark.requires_chromadb
class TestChromaDBPerformance:
    """Test query performance and benchmarks"""
    
    def test_chromadb_query_performance(
        self,
        chromadb_collection,
        e2e_capture_output
    ):
        """Benchmark query speed"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "chromadb_query_performance",
            "description": "Benchmark query performance"
        })
        
        # Add a larger set of documents
        num_docs = 100
        
        print(f"Creating {num_docs} test documents...")
        
        ids = [f"doc_{i}" for i in range(num_docs)]
        documents = [
            f"This is test document number {i} with some random content about topic {i % 10}"
            for i in range(num_docs)
        ]
        metadatas = [{"index": i, "category": f"cat_{i % 5}"} for i in range(num_docs)]
        
        # Benchmark ingestion
        start_time = time.time()
        chromadb_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        ingestion_duration = time.time() - start_time
        
        print(f"  ✓ Ingested {num_docs} documents in {ingestion_duration:.3f}s")
        print(f"  Rate: {num_docs/ingestion_duration:.1f} docs/sec")
        
        # Benchmark queries
        num_queries = 10
        query_times = []
        
        print(f"\nRunning {num_queries} test queries...")
        
        for i in range(num_queries):
            query = f"test document {i * 10}"
            
            start_time = time.time()
            results = chromadb_collection.query(
                query_texts=[query],
                n_results=10
            )
            query_time = time.time() - start_time
            
            query_times.append(query_time)
        
        avg_query_time = sum(query_times) / len(query_times)
        min_query_time = min(query_times)
        max_query_time = max(query_times)
        
        print(f"\n✓ Query Performance:")
        print(f"  Average: {avg_query_time*1000:.1f}ms")
        print(f"  Min: {min_query_time*1000:.1f}ms")
        print(f"  Max: {max_query_time*1000:.1f}ms")
        
        # Verify reasonable performance (< 1 second per query)
        assert avg_query_time < 1.0, f"Queries too slow: {avg_query_time:.3f}s average"
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "chromadb_query_performance",
            "result": "success",
            "documents": num_docs,
            "avg_query_time_ms": avg_query_time * 1000,
            "ingestion_rate": num_docs / ingestion_duration
        })
    
    def test_chromadb_retrieval_accuracy(
        self,
        chromadb_collection,
        sample_documents,
        e2e_capture_output
    ):
        """Verify correct documents returned"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "chromadb_retrieval_accuracy",
            "description": "Test retrieval accuracy"
        })
        
        # Add documents
        ids = [doc["id"] for doc in sample_documents]
        documents = [doc["text"] for doc in sample_documents]
        metadatas = [doc["metadata"] for doc in sample_documents]
        
        chromadb_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        # Test exact retrieval by ID
        print("Testing exact retrieval by ID...")
        
        for doc_id, doc_text in zip(ids, documents):
            results = chromadb_collection.get(ids=[doc_id])
            
            assert len(results["ids"]) == 1, f"Expected 1 result for {doc_id}"
            assert results["ids"][0] == doc_id, f"ID mismatch"
            assert results["documents"][0] == doc_text, f"Document text mismatch"
            
            print(f"  ✓ {doc_id}: Retrieved correctly")
        
        # Test semantic accuracy
        print("\nTesting semantic retrieval accuracy...")
        
        # Use document text as query (should return itself as top result)
        for doc_id, doc_text in zip(ids, documents):
            results = chromadb_collection.query(
                query_texts=[doc_text],
                n_results=1
            )
            
            top_result = results["ids"][0][0]
            assert top_result == doc_id, \
                f"Query with exact text should return same document. Expected {doc_id}, got {top_result}"
            
            print(f"  ✓ {doc_id}: Semantic match accurate")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "chromadb_retrieval_accuracy",
            "result": "success",
            "documents_tested": len(ids)
        })
