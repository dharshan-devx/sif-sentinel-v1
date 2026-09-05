import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("root page", () => { it("establishes the product purpose without fake operational data", () => { render(<Home />); expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Make safety signals easier to see"); expect(screen.getByRole("link", { name: /sif sentinel/i })).toBeVisible(); expect(screen.queryByText(/incidents today/i)).not.toBeInTheDocument(); }); });
