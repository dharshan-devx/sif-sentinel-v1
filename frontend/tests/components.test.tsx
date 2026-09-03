import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

describe("UI primitives", () => {
  it("renders accessible foundation components", () => {
    render(<><Alert title="Requires human review">Evidence needs confirmation.</Alert><Badge tone="critical">CRITICAL</Badge><Button>Continue</Button><EmptyState title="No safety signals" description="New data will appear here." /></>);
    expect(screen.getByRole("alert")).toHaveTextContent("Requires human review");
    expect(screen.getByText("CRITICAL")).toBeVisible();
    expect(screen.getByRole("button", { name: "Continue" })).toBeEnabled();
    expect(screen.getByRole("heading", { name: "No safety signals" })).toBeVisible();
  });
});
