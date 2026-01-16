# Python & LLM Development Best Practices

## Python Code Standards

### Code Style & Organization
- Follow PEP 8 style guidelines
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters (with flexibility for readability)
- Use descriptive variable names; avoid single-letter variables except in comprehensions/lambdas
- Organize imports: standard library, third-party, local (separated by blank lines)
- Use absolute imports over relative imports for clarity

### Error Handling
- Use specific exception types; avoid bare `except:` clauses
- Include informative error messages with context
- Log exceptions with proper severity levels
- Use context managers (`with` statements) for resource management
- Implement retry logic with exponential backoff for API calls

### Function Design
- Keep functions focused on a single responsibility
- Limit function parameters (max 5; use dataclasses/TypedDict for complex inputs)
- Return early to reduce nesting
- Use default arguments sparingly; prefer explicit configuration
- Document complex logic with inline comments

### Documentation
- Use docstrings for all public modules, classes, and functions
- Follow Google or NumPy docstring format consistently
- Include type information in docstrings when it adds clarity
- Document assumptions, limitations, and side effects
- Provide usage examples for complex functions

## LLM Integration Best Practices

### Prompt Engineering
- Use system prompts to establish role, tone, and constraints
- Structure prompts with clear sections (context, task, constraints, output format)
- Include few-shot examples for complex tasks
- Use XML/JSON tags to separate prompt sections for clarity
- Version control prompts as templates in separate files
- Test prompts with edge cases and validate outputs

### API Usage
- Implement timeout and retry mechanisms for all LLM API calls
- Use streaming responses for long-form content when available
- Implement rate limiting and token budget management
- Cache frequently used responses when deterministic
- Log all LLM interactions for debugging and cost tracking
- Handle API errors gracefully with fallback options

### Token Management
- Track and log token usage per request
- Implement context window management for long conversations
- Truncate or summarize old messages to stay within limits
- Use token counting utilities before sending requests
- Optimize prompts to minimize unnecessary tokens
- Consider cost vs. quality tradeoffs for model selection

### Response Processing
- Validate LLM outputs against expected schemas
- Implement fallback parsing strategies (JSON, regex, text extraction)
- Use Pydantic models to validate structured outputs
- Sanitize and escape LLM-generated content before use
- Implement confidence checks and quality validation
- Log malformed responses for prompt refinement

### RAG (Retrieval-Augmented Generation)
- Chunk documents semantically, not just by character count
- Include metadata (source, date, category) in vector storage
- Use hybrid search (semantic + keyword) when appropriate
- Implement relevance scoring and filtering
- Re-rank retrieved results before passing to LLM
- Cite sources in generated responses for verification

### Safety & Validation
- Implement input validation and sanitization
- Filter out sensitive information from prompts
- Validate outputs for hallucinations and factual accuracy
- Implement content moderation for user inputs and outputs
- Add guardrails to prevent prompt injection attacks
- Use structured outputs (JSON mode) when possible to constrain responses

### Testing & Evaluation
- Create test suites with expected inputs/outputs
- Implement automated quality metrics (relevance, coherence, accuracy)
- Use deterministic temperature (0.0) for consistent testing
- A/B test prompt variations with real-world data
- Monitor production outputs for drift and degradation
- Maintain golden datasets for regression testing

### Performance & Optimization
- Batch similar requests when possible
- Use async/await for concurrent LLM calls
- Implement response caching with appropriate TTL
- Monitor and optimize for latency bottlenecks
- Use smaller models for simple tasks
- Pre-compute embeddings for static content

### Configuration Management
- Store model parameters in configuration files
- Use environment variables for API keys and endpoints
- Version control prompt templates separately from code
- Make temperature, max_tokens, and model configurable
- Implement feature flags for gradual rollouts
- Document all configuration options

### Monitoring & Observability
- Log all LLM interactions with timestamps and identifiers
- Track cost per request and per user/session
- Monitor response times and error rates
- Implement alerting for quality degradation
- Create dashboards for usage patterns and costs
- Track prompt versions and their performance metrics

## Project-Specific Patterns

### ChromaDB/Vector Database
- Store XML structure in metadata fields
- Use consistent collection naming conventions
- Implement metadata filtering for efficient queries
- Version your embedding model choice
- Test queries with your actual data distribution
- Include document hierarchy in metadata

### Audio/TTS Integration
- Validate audio file paths and formats before processing
- Implement audio quality checks post-generation
- Use appropriate sample rates for target hardware
- Manage disk space for generated audio files
- Include audio metadata (duration, voice, timestamp)

### Character Consistency
- Load personality profiles from structured files (JSON/YAML)
- Validate character cards against schema
- Include personality traits in system prompts
- Test responses against character expectations
- Version control character profiles
- Document voice characteristics and mannerisms

## Code Quality Tools

### Required Tools
- `black` - Code formatting
- `isort` - Import sorting
- `mypy` - Static type checking
- `pylint` or `ruff` - Linting
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting

### Pre-commit Checks
- Format code with black
- Sort imports with isort
- Run type checker
- Run linter
- Execute test suite
- Check test coverage (minimum 70%)

### Continuous Practices
- Write tests before implementation (TDD when appropriate)
- Review type hints coverage
- Update documentation with code changes
- Profile performance-critical sections
- Monitor memory usage for large datasets
- Refactor when complexity increases