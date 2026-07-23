import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import "@testing-library/jest-dom/vitest";

// RTL's automatic afterEach cleanup only self-registers when it detects a
// global `afterEach` (Jest-style); this project doesn't enable Vitest's
// `globals: true`, so it's wired explicitly here instead - otherwise a
// second `render()` in the same test file leaves the first render's DOM
// mounted, breaking any single-match query in a later test.
afterEach(() => {
  cleanup();
});
