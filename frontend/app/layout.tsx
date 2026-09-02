import type { Metadata } from "next";
import { Fraunces, Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "WorthWearing — Try it on. Know if it’s worth owning.",
  description:
    "WorthWearing combines Perfect Corp virtual try-on with wardrobe intelligence so shoppers keep what they buy.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${fraunces.variable} bg-white text-[#111111] antialiased`}>
        {children}
      </body>
    </html>
  );
}
