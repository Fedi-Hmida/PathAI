# Quiz Package

This package contains the Phase 8 weekly quiz foundation.

The current implementation is deterministic and offline-safe. It generates
weekly quizzes from `CurriculumPlan` week/topic data, scores submissions, stores
attempts in memory, and exposes adapter-ready low-score signals.

Implemented:

- 1 to 7 questions per generated quiz, defaulting to 5,
- multiple-choice, true/false, and short-answer question types,
- deterministic explanations,
- deterministic scoring and feedback,
- best score and attempt history,
- optional mock-LLM structured-output boundary.

Not implemented:

- authentication and user ownership,
- MongoDB persistence,
- real-LLM-required quiz generation,
- frontend quiz UI,
- Adapter/replanning.
