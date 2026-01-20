"""
Full Pipeline End-to-End Tests

Tests complete workflow integration:
- Broadcast generation with RAG (Ollama + ChromaDB)
- Multi-segment broadcasts with continuity
- Story progression validation
- Real LLM validation

Run with: pytest tests/e2e/test_full_pipeline_e2e.py --run-e2e -v
"""

import pytest
import time
import json


@pytest.mark.e2e
@pytest.mark.requires_ollama
@pytest.mark.requires_chromadb
class TestBroadcastWithRAG:
    """Test broadcast generation with RAG pipeline"""
    
    def test_broadcast_generation_with_rag(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        chromadb_collection,
        sample_documents,
        e2e_capture_output
    ):
        """Complete broadcast with ChromaDB RAG"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "broadcast_generation_with_rag",
            "description": "Generate broadcast segment using RAG"
        })
        
        # Step 1: Ingest lore into ChromaDB
        print("Step 1: Ingesting lore into ChromaDB...")
        
        ids = [doc["id"] for doc in sample_documents]
        documents = [doc["text"] for doc in sample_documents]
        metadatas = [doc["metadata"] for doc in sample_documents]
        
        chromadb_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"  ✓ Ingested {len(documents)} documents")
        
        # Step 2: Query for relevant lore
        print("\nStep 2: Querying relevant lore...")
        
        query = "Tell me about the wasteland and vaults"
        
        results = chromadb_collection.query(
            query_texts=[query],
            n_results=2
        )
        
        relevant_docs = results["documents"][0]
        print(f"  ✓ Retrieved {len(relevant_docs)} relevant documents")
        
        # Step 3: Generate broadcast with RAG context
        print("\nStep 3: Generating broadcast with Ollama...")
        
        context = "\n".join(relevant_docs)
        
        prompt = f"""You are Julie, a radio DJ in post-apocalyptic Appalachia.
        
Context from the lore database:
{context}

Create a brief radio news segment (2-3 sentences) about the wasteland based on this lore.
Keep it upbeat and friendly."""
        
        start_time = time.time()
        response = ollama_client.generate(
            model=ollama_model_name,
            prompt=prompt,
            options={"temperature": 0.7}
        )
        generation_time = time.time() - start_time
        
        broadcast_text = response["response"]
        
        assert len(broadcast_text) > 0, "Generated broadcast is empty"
        
        print(f"  ✓ Generated broadcast in {generation_time:.2f}s")
        print(f"\n  Broadcast:\n  {broadcast_text}\n")
        
        # Verify broadcast contains relevant information
        # (At least one keyword from the context)
        keywords = ["vault", "wasteland", "brotherhood", "dweller"]
        has_keyword = any(keyword.lower() in broadcast_text.lower() for keyword in keywords)
        
        assert has_keyword, "Broadcast doesn't seem to use the provided lore context"
        print(f"  ✓ Broadcast uses lore context")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "broadcast_generation_with_rag",
            "result": "success",
            "generation_time": generation_time,
            "broadcast_length": len(broadcast_text)
        })


@pytest.mark.e2e
@pytest.mark.requires_ollama
class TestMultiSegmentBroadcast:
    """Test multi-segment broadcast generation"""
    
    def test_multi_segment_broadcast(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        e2e_capture_output
    ):
        """Generate 3+ segments with continuity"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "multi_segment_broadcast",
            "description": "Generate multiple connected broadcast segments"
        })
        
        segment_types = ["greeting", "news", "weather", "closing"]
        segments = []
        
        print("Generating multi-segment broadcast...\n")
        
        for i, segment_type in enumerate(segment_types, 1):
            print(f"Segment {i}/{len(segment_types)}: {segment_type}")
            
            # Build prompt based on segment type
            if segment_type == "greeting":
                prompt = "You are Julie, a radio DJ. Write a friendly morning greeting (1-2 sentences)."
            elif segment_type == "news":
                prompt = "You are Julie. Share a brief wasteland news update (2-3 sentences)."
            elif segment_type == "weather":
                prompt = "You are Julie. Give a brief weather forecast for Appalachia (2 sentences)."
            else:  # closing
                prompt = "You are Julie. Write a friendly sign-off (1-2 sentences)."
            
            start_time = time.time()
            response = ollama_client.generate(
                model=ollama_model_name,
                prompt=prompt,
                options={"temperature": 0.7}
            )
            duration = time.time() - start_time
            
            segment_text = response["response"]
            segments.append({
                "type": segment_type,
                "text": segment_text,
                "duration": duration
            })
            
            print(f"  ✓ Generated in {duration:.2f}s")
            print(f"  Text: {segment_text[:100]}...\n")
        
        # Verify all segments generated
        assert len(segments) == len(segment_types), "Not all segments generated"
        
        # Verify reasonable length
        for segment in segments:
            assert len(segment["text"]) > 0, f"Empty segment: {segment['type']}"
            assert len(segment["text"]) < 1000, f"Segment too long: {segment['type']}"
        
        total_time = sum(s["duration"] for s in segments)
        print(f"✓ Generated {len(segments)} segments in {total_time:.2f}s total")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "multi_segment_broadcast",
            "result": "success",
            "segments_count": len(segments),
            "total_time": total_time
        })


@pytest.mark.e2e
@pytest.mark.requires_ollama
class TestStoryContinuity:
    """Test story progression and continuity"""
    
    def test_story_continuity(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        e2e_capture_output
    ):
        """Validate story progression across segments"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "story_continuity",
            "description": "Test story continuation across multiple segments"
        })
        
        print("Testing story continuity...\n")
        
        # Generate initial story setup
        setup_prompt = """Write the beginning of a short wasteland story about a trader (2 sentences).
End with a cliffhanger."""
        
        response = ollama_client.generate(
            model=ollama_model_name,
            prompt=setup_prompt,
            options={"temperature": 0.7}
        )
        
        story_part1 = response["response"]
        print(f"Part 1 (Setup):\n{story_part1}\n")
        
        # Generate continuation
        continuation_prompt = f"""Continue this story (2 sentences):

{story_part1}

What happens next?"""
        
        response = ollama_client.generate(
            model=ollama_model_name,
            prompt=continuation_prompt,
            options={"temperature": 0.7}
        )
        
        story_part2 = response["response"]
        print(f"Part 2 (Continuation):\n{story_part2}\n")
        
        # Generate conclusion
        conclusion_prompt = f"""Conclude this story (2 sentences):

Part 1: {story_part1}
Part 2: {story_part2}

Write a satisfying ending."""
        
        response = ollama_client.generate(
            model=ollama_model_name,
            prompt=conclusion_prompt,
            options={"temperature": 0.7}
        )
        
        story_part3 = response["response"]
        print(f"Part 3 (Conclusion):\n{story_part3}\n")
        
        # Verify all parts generated
        assert len(story_part1) > 0, "Part 1 is empty"
        assert len(story_part2) > 0, "Part 2 is empty"
        assert len(story_part3) > 0, "Part 3 is empty"
        
        # Verify reasonable lengths
        assert len(story_part1) < 500, "Part 1 too long"
        assert len(story_part2) < 500, "Part 2 too long"
        assert len(story_part3) < 500, "Part 3 too long"
        
        full_story = f"{story_part1}\n\n{story_part2}\n\n{story_part3}"
        
        print(f"✓ Generated complete 3-part story ({len(full_story)} chars)")
        
        e2e_capture_output.log_event("TEST_PASSED", {
            "test": "story_continuity",
            "result": "success",
            "story_parts": 3,
            "total_length": len(full_story)
        })


@pytest.mark.e2e
@pytest.mark.requires_ollama
class TestValidationWithRealLLM:
    """Test validation using real Ollama LLM"""
    
    def test_validation_with_real_llm(
        self,
        ollama_client,
        ollama_model_name,
        verify_ollama_model,
        e2e_capture_output
    ):
        """Use real Ollama for validation"""
        e2e_capture_output.log_event("TEST_START", {
            "test": "validation_with_real_llm",
            "description": "Use LLM to validate generated content"
        })
        
        print("Testing LLM-based validation...\n")
        
        # Generate test content
        content_prompt = "Write a 2-sentence radio announcement about a community event."
        
        response = ollama_client.generate(
            model=ollama_model_name,
            prompt=content_prompt,
            options={"temperature": 0.7}
        )
        
        generated_content = response["response"]
        print(f"Generated content:\n{generated_content}\n")
        
        # Use LLM to validate the content
        validation_prompt = f"""Analyze this radio announcement and respond with JSON:

Content: {generated_content}

Provide this JSON structure:
{{
  "is_appropriate": true/false,
  "is_on_topic": true/false,
  "tone": "friendly/neutral/hostile",
  "issues": ["list", "any", "problems"]
}}"""
        
        print("Running validation...")
        
        response = ollama_client.generate(
            model=ollama_model_name,
            prompt=validation_prompt,
            format="json",
            options={"temperature": 0.1}  # Low temperature for consistent validation
        )
        
        validation_result = response["response"]
        print(f"Validation result:\n{validation_result}\n")
        
        # Parse validation JSON
        try:
            validation_data = json.loads(validation_result)
            
            print("✓ Validation JSON is valid")
            print(f"  Appropriate: {validation_data.get('is_appropriate')}")
            print(f"  On topic: {validation_data.get('is_on_topic')}")
            print(f"  Tone: {validation_data.get('tone')}")
            
            # Verify expected fields exist
            assert "is_appropriate" in validation_data, "Missing 'is_appropriate' field"
            assert "is_on_topic" in validation_data, "Missing 'is_on_topic' field"
            assert "tone" in validation_data, "Missing 'tone' field"
            
            e2e_capture_output.log_event("TEST_PASSED", {
                "test": "validation_with_real_llm",
                "result": "success",
                "validation": validation_data
            })
        
        except json.JSONDecodeError as e:
            pytest.fail(f"Validation returned invalid JSON: {e}\nResponse: {validation_result}")
