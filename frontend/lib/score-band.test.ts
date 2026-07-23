import { describe, expect, it } from "vitest";

import { scoreBand } from "@/lib/score-band";

describe("scoreBand", () => {
  it("returns success at and above 0.8", () => {
    expect(scoreBand(0.8)).toBe("success");
    expect(scoreBand(1)).toBe("success");
  });

  it("returns brand between 0.6 (inclusive) and 0.8 (exclusive)", () => {
    expect(scoreBand(0.6)).toBe("brand");
    expect(scoreBand(0.79)).toBe("brand");
  });

  it("returns warning below 0.6", () => {
    expect(scoreBand(0.59)).toBe("warning");
    expect(scoreBand(0)).toBe("warning");
  });
});
