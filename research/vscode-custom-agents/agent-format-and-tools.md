# Research: VS Code Custom Agent File Format and Available Tools

**Date**: 2026-01-09  
**Researcher**: Researcher Agent  
**Context**: Understanding why yellow validation warnings appear in `.agent.md` files and what the correct tool syntax and available tools are for VS Code Copilot custom agents.

## Summary

VS Code Copilot custom agents use **tool categories** (like `'read'`, `'edit'`, `'search'`, `'fetch'`) in their YAML frontmatter, NOT individual tool names (like `'read_file'`, `'grep_search'`, `'semantic_search'`). The `#tool:toolName` reference syntax in the body is for documentation purposes only and should reference actual tool names, not categories. Example file paths used in documentation sections do not need to exist and can trigger warnings if they look like actual references.

## Key Findings

1. **Tool Categories in YAML Frontmatter**: The `tools` field uses high-level categories, not granular tool names
2. **Reference Syntax Validation**: VS Code validates `#tool:` references in the markdown body against available tools
3. **Example Paths Trigger Warnings**: Documentation examples with file paths get validated as if they were real references
4. **MCP Server Tools**: Use `server-name/*` format to include all tools from an MCP server

## Detailed Analysis

### Available Tool Categories for YAML Frontmatter

Based on VS Code's official documentation and the GitHub awesome-copilot repository, here are the **correct tool categories**:

#### Built-in Tool Categories:
- `'vscode'` - VS Code-specific commands and operations
- `'execute'` or `'run_in_terminal'` - Terminal execution capabilities  
- `'read'` - File reading operations (includes read_file, list_dir, etc.)
- `'edit'` - File editing operations (includes replace_string_in_file, create_file, etc.)
- `'search'` - Search operations (includes semantic_search, grep_search, file_search, etc.)
- `'fetch'` - Web fetching capabilities
- `'agent'` - Agent-related tools
- `'usages'` - Code usage/reference finding
- `'todo'` - Todo list management
- `'test'` or `'test_failure'` - Testing tools
- `'web'` - Web-related tools

#### MCP Server Tools:
- `'server-name/*'` - All tools from a specific MCP server (e.g., `'github/*'`, `'brave-search/*'`)

### Common Pitfalls

**Pitfall 1: Using Granular Tool Names Instead of Categories**
- **Problem**: Using tool names like `'semantic_search'`, `'read_file'`, `'grep_search'`, `'create_file'`, `'create_directory'` in the `tools` array
- **Why it happens**: The available function names (visible to agents internally) don't match the category names used in agent configuration
- **Solution**: Use categories like `'search'`, `'read'`, `'edit'` instead

**Pitfall 2: Using #tool: References for Documentation Examples**
- **Problem**: Using `#tool:toolName` syntax in documentation/example sections triggers validation
- **Why it happens**: VS Code validates ALL `#tool:` references, even in example text
- **Solution**: Either use plain text descriptions or ensure referenced tools actually exist

**Pitfall 3: Example File Paths in Documentation**
- **Problem**: Markdown links to example paths like `[instruction file](path/to/instructions.md)` trigger file-not-found warnings
- **Why it happens**: VS Code validates markdown links as if they're real references
- **Solution**: Use descriptive text without actual file path structure, or use code formatting to prevent validation

### Best Practices

**1. Tool Selection for Different Agent Types**

*Read-Only Agents (Planning, Research, Review):*
```yaml
tools: ['read', 'search', 'fetch', 'usages']
```

*Implementation Agents (Coding, Refactoring):*
```yaml
tools: ['read', 'search', 'edit', 'execute']
```

*Research Agents with External Data:*
```yaml
tools: ['read', 'search', 'fetch', 'edit', 'github/*', 'brave-search/*', 'sequential-thinking/*', 'todo']
```

**2. Tool Reference in Body**

When you want to describe available tools in the agent body, avoid using `#tool:` syntax for non-existent tools. Instead:

❌ **Incorrect**:
```markdown
- **#tool:semantic_search**: Find relevant code patterns
- **#tool:grep_search**: Search for specific terms
```

✅ **Correct**:
```markdown
- **Search Tools**: Find relevant code patterns and documentation using semantic and text-based search
- **Read Tools**: Examine project files and grep for specific terms
```

**3. Documentation Examples**

When providing examples of file references:

❌ **Incorrect**:
```markdown
Reference other files: `[instruction file](path/to/instructions.md)`
```

✅ **Correct**:
```markdown
Reference other files: Use markdown links like \`[instruction file](../../path/to/file.md)\`
```
(Note: Escaped backticks or using actual relative paths to real files)

## Comparison Matrix

| Aspect | Incorrect Approach | Correct Approach | Reason |
|--------|-------------------|------------------|--------|
| Tool Specification | `'semantic_search', 'grep_search', 'read_file'` | `'search', 'read'` | Categories vs individual tools |
| Tool References | `#tool:semantic_search` | Plain text description or verified tool name | VS Code validates references |
| Example Paths | `[file](path/to/file.md)` | Descriptive text or actual paths | Prevents validation warnings |
| MCP Tools | `'githubRepo'` | `'github/*'` | Correct MCP server syntax |

## Common Mistakes to Avoid

### 1. Mixing Tool Names and Categories
- **Problem**: Using both categories and specific tool names in the tools array
- **Why it happens**: Confusion between internal tool names and configuration categories
- **Solution**: Stick to documented category names only

### 2. Over-Specifying Tools
- **Problem**: Listing too many individual capabilities
- **Why it happens**: Attempting to be explicit about available functionality
- **Solution**: Use broader categories; the agent will have access to all tools within that category

### 3. Assuming #tool: is Documentation-Only
- **Problem**: Thinking `#tool:` syntax is just for human readability
- **Why it happens**: It looks like markdown formatting
- **Solution**: Understand that VS Code actively validates these references

## Recommendations

### For the Custom Agent Foundry File

1. **Update Reference Syntax section** to avoid actual #tool: references in examples
2. **Clarify** that `#tool:` references must point to real, available tools
3. **Provide** clear examples of valid markdown link formatting that won't trigger validation

### For the Researcher Agent File

1. **Use tool categories** in YAML: `['read', 'search', 'fetch', 'edit', ...]`
2. **Remove #tool: syntax** from Tool Usage Patterns section
3. **Use descriptive text** instead of tool references
4. **Update handoff agent** from invalid agent name to valid one (e.g., `copilot`)

### General Best Practices

1. Always check the [official VS Code documentation](https://code.visualstudio.com/docs/copilot/customization/custom-agents) for current tool categories
2. Test agent files after creation to catch validation warnings early
3. Use descriptive text for documentation rather than executable references
4. When in doubt, examine agents in the [awesome-copilot repository](https://github.com/github/awesome-copilot/tree/main/agents) for real-world examples

## References

- [VS Code Custom Agents Documentation](https://code.visualstudio.com/docs/copilot/customization/custom-agents)
- [GitHub Docs: Custom Agents Configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [GitHub awesome-copilot Repository - Agents](https://github.com/github/awesome-copilot/tree/main/agents)
- [VS Code Custom Instructions](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
