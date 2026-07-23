import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LifecycleStamps } from "@/components/goal/lifecycle-stamps";

function stamp(label: string) {
  return screen.getByText(label);
}

describe("LifecycleStamps", () => {
  it("marks only the reached stamps up to a fresh goal's status", () => {
    render(<LifecycleStamps status="created" />);

    expect(stamp("Created")).toHaveClass("border-brand");
    expect(stamp("Assessment Started")).toHaveClass("border-dashed");
    expect(stamp("Curriculum Generated")).toHaveClass("border-dashed");
    expect(stamp("Active")).toHaveClass("border-dashed");
    expect(stamp("Completed")).toHaveClass("border-dashed");
    expect(stamp("Failed")).toHaveClass("border-dashed");
  });

  it("marks every stamp up through the current one for a mid-lifecycle goal", () => {
    render(<LifecycleStamps status="curriculum_generated" />);

    expect(stamp("Created")).toHaveClass("border-brand");
    expect(stamp("Assessment Started")).toHaveClass("border-brand");
    expect(stamp("Curriculum Generated")).toHaveClass("border-brand");
    expect(stamp("Active")).toHaveClass("border-dashed");
    expect(stamp("Completed")).toHaveClass("border-dashed");
  });

  it("marks every stamp reached for a fully completed goal, Failed excluded", () => {
    render(<LifecycleStamps status="completed" />);

    expect(stamp("Created")).toHaveClass("border-brand");
    expect(stamp("Assessment Started")).toHaveClass("border-brand");
    expect(stamp("Curriculum Generated")).toHaveClass("border-brand");
    expect(stamp("Active")).toHaveClass("border-brand");
    expect(stamp("Completed")).toHaveClass("border-brand");
    expect(stamp("Failed")).toHaveClass("border-dashed");
  });

  it("shows a failed goal's real progress up to Active reached, with only Failed flagged - not reset to zero", () => {
    render(<LifecycleStamps status="failed" />);

    expect(stamp("Created")).toHaveClass("border-brand");
    expect(stamp("Assessment Started")).toHaveClass("border-brand");
    expect(stamp("Curriculum Generated")).toHaveClass("border-brand");
    expect(stamp("Active")).toHaveClass("border-brand");
    // Completed never happened - a failed goal must not show it reached.
    expect(stamp("Completed")).toHaveClass("border-dashed");
    // The Failed stamp itself uses the warning tone, not the brand tone.
    expect(stamp("Failed")).toHaveClass("border-warning");
    expect(stamp("Failed")).not.toHaveClass("border-brand");
  });
});
