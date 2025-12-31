import type { Metadata } from "next";
import "../styles/globals.css";

export const metadata: Metadata = {
  title: "K-League Tactical Feedback",
  description: "고정캠 기반 전술 피드백 데모",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
