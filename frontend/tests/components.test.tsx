import { render, screen } from "@testing-library/react";
import { Button } from "@/components/ui/button";
import { SeverityBadge } from "@/components/ui/severity-badge";
import { EmptyState, ErrorState, ForbiddenState, LoadingState } from "@/components/states";

describe("foundation components", () => {
  it("renders a keyboard-focusable button and severity text", () => {
    render(<><Button>Continue</Button><SeverityBadge severity="CRITICAL" /></>);
    const button = screen.getByRole("button", { name: "Continue" });
    button.focus();
    expect(button).toHaveFocus();
    expect(screen.getByText("CRITICAL")).toBeVisible();
  });

  it("renders reusable loading, empty, error, and forbidden states", () => {
    render(<><LoadingState label="Loading reports" /><EmptyState title="No reports" description="Try again later." /><ErrorState error={new Error("ignored")} /><ForbiddenState /></>);
    expect(screen.getByRole("status")).toHaveTextContent("Loading reports");
    expect(screen.getByText("No reports")).toBeVisible();
    expect(screen.getByText("Something went wrong")).toBeVisible();
    expect(screen.getByText("Access restricted")).toBeVisible();
  });
});
