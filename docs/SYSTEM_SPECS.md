# System Specifications

**Date Recorded:** January 4, 2026

## Hardware Overview

*   **Operating System:** Windows 11 Home (64-bit)
*   **Processor (CPU):** AMD Ryzen 9 5900HS
    *   Cores: 8
    *   Logical Processors: 16
*   **Memory (RAM):** 16 GB
*   **Graphics (GPU):**
    *   **Dedicated:** NVIDIA GeForce RTX 3060 Laptop GPU
        *   **VRAM:** 6 GB (6144 MiB)
    *   **Integrated:** AMD Radeon(TM) Graphics

## AI Capability Analysis

*   **Text-to-Speech (Chatterbox Turbo):** 
    *   Performance: Excellent.
    *   The RTX 3060 accelerates generation significantly.
    
*   **Large Language Models (Ollama):**
    *   **Supported Models:** Llama 3 (8B), Mistral (7B), and similar sized models.
    *   **Quantization:** 4-bit quantization (default in Ollama) is recommended.
    *   **Memory Usage:** An 8B parameter model typically uses ~4.5 - 5 GB of VRAM.

*   **Constraints:**
    *   **VRAM Limit:** With 6 GB of VRAM, running *both* the LLM and the TTS model on the GPU simultaneously may cause "Out of Memory" errors.
    *   **Recommendation:** Run generation steps sequentially (Generate Text -> Unload LLM -> Generate Audio) or offload one task to the CPU if necessary.
