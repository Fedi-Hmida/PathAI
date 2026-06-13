# Prompt Templates

Prompt templates are versioned outside application logic. Phase 2 adds a small
registry that loads Markdown templates from `prompts/templates/`, renders simple
variables, and prepends prompt name/version metadata.

Current Phase 2 structure:

```text
prompts/
  registry.py
  templates/
    llm_health_check.md
    assessment_question_draft.md
```

Each prompt should include:

- purpose
- input variables
- output schema name
- version
- safety notes
