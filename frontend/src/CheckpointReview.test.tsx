import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { CheckpointReview } from "./CheckpointReview";

it("submits reviewed saved content without claiming approval", () => {
  const retry = vi.fn();
  render(
    <CheckpointReview
      disabled={false}
      onRetry={retry}
      run={{
        id: "failed-run",
        input_hash: "source-hash",
        kind: "generate",
        status: "failed",
        error: "synthetic",
        events: [],
        checkpoints: {
          introduction: {
            summary: "Original summary",
            items: [],
            open_issues: [],
          },
        },
      }}
    />,
  );
  fireEvent.change(screen.getByRole("textbox", { name: "Summary" }), {
    target: { value: "Reviewed summary" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Retry with reviewed edits" }),
  );
  expect(retry).toHaveBeenCalledWith({
    introduction: {
      summary: "Reviewed summary",
      items: [],
      open_issues: [],
    },
  });
  expect(screen.getByText(/does not approve the document/)).toBeTruthy();
});
