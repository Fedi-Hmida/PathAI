# Progress Package

This package contains the Phase 8 progress tracking foundation.

The current implementation is deterministic, temporary, and no-auth. It uses an
in-memory store so tests do not require MongoDB.

Implemented:

- initialize progress from a `CurriculumPlan`,
- track topic status: `pending`, `in_progress`, `done`, `stuck`,
- compute week and curriculum completion,
- record progress events,
- include quiz-completed score events,
- produce adapter-ready progress signals without implementing the Adapter.

Not implemented:

- authentication and user ownership,
- MongoDB persistence,
- Adapter/replanning,
- production dashboard.
