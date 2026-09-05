import { render, screen } from "@testing-library/react";
import { useQueryClient } from "@tanstack/react-query";
import { Providers } from "@/providers";

function Probe() { const client = useQueryClient(); return <span>stale:{String(client.getDefaultOptions().queries?.staleTime)}</span>; }
describe("Providers", () => { it("supplies the configured QueryClient", () => { render(<Providers><Probe /></Providers>); expect(screen.getByText("stale:30000")).toBeVisible(); }); });
