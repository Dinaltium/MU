// app/layout.tsx — Root layout with React Query provider
import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "RxBridge — AI Clinical Decision Support",
  description: "Intelligent antibiotic prescribing powered by Bayesian inference and PK/PD modelling",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
