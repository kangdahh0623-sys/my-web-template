import "./globals.css";
import Navbar from "@/components/Navbar";
export const metadata = { title: "급식줍쇼" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko"><body className="min-h-screen bg-white text-gray-900">
      <Navbar />
      <main className="mx-auto max-w-5xl px-5 py-6">{children}</main>
    </body></html>
  );
}
