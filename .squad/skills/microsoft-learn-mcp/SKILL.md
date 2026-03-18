# Microsoft Learn MCP Skill

> Access official Microsoft documentation, code samples, and API references via MCP tools

## Confidence: high

## Tools Available

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `microsoft-learn-microsoft_docs_search` | Search docs for concepts, tutorials, architecture | Starting research, understanding services |
| `microsoft-learn-microsoft_code_sample_search` | Find code examples by SDK/method/language | Need working code, verify SDK patterns |
| `microsoft-learn-microsoft_docs_fetch` | Get full page content from a URL | Search found relevant page, need complete details |

## Usage Patterns

### Research Flow
1. **Search first:** Use `microsoft_docs_search` with descriptive query
2. **Fetch if needed:** If results are truncated, use `microsoft_docs_fetch` on the URL
3. **Code samples:** Use `microsoft_code_sample_search` for implementation examples

### Query Examples

**Doc Intelligence:**
```
microsoft_docs_search: "Azure AI Document Intelligence custom models"
microsoft_code_sample_search: query="DocumentAnalysisClient", language="python"
```

**Power Apps:**
```
microsoft_docs_search: "Power Apps Canvas app connectors"
microsoft_code_sample_search: query="Power Fx formulas"
```

**Logic Apps:**
```
microsoft_docs_search: "Logic Apps HTTP trigger connector"
microsoft_code_sample_search: query="Logic Apps workflow definition"
```

## Team Usage

- **M:** Architecture guidance, service limits, best practices
- **Q:** Power Apps patterns, Power Fx formulas, Canvas controls
- **Bond:** Azure SDK code samples, Doc Intelligence API, Logic Apps
- **Moneypenny:** Doc Intelligence documentation, extraction patterns
- **Felix:** Testing patterns for Azure services
- **Vesper:** Verify official terminology in instructions

## Notes

- Always cite the source URL when referencing Microsoft docs
- Code samples are authoritative — prefer them over generated code
- Use `language` parameter in code search for better results
