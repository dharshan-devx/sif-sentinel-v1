import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ForbiddenState } from "@/components/ui/forbidden-state";

describe("ForbiddenState", () => { it("does not treat valid authentication as logout", () => { render(<ForbiddenState />); expect(screen.getByRole("alert")).toHaveTextContent("Access denied"); }); });
