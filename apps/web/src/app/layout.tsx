import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Hallucination Analytics Studio",
  description:
    "Evaluate LLM outputs for hallucination, faithfulness, and grounding. Measure what your AI gets wrong.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
