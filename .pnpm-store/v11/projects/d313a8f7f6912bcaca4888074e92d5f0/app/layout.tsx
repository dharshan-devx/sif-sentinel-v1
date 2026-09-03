import type { Metadata } from "next";
import "@/app/globals.css";
import { AppProviders } from "@/providers/app-providers";

export const metadata: Metadata = { title: "SIF Sentinel", description: "Workplace safety decision support" };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body><AppProviders>{children}</AppProviders></body></html>; }
