import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { useEffect, useState } from "react";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "Create Next App",
  description: "Generated by create next app",
};

export default function RootLayout({ children }) {
  const [subscriptions, setSubscriptions] = useState([]);

  useEffect(() => {
    fetch('/api/subscriptions')
      .then(response => response.json())
      .then(data => setSubscriptions(data));
  }, []);

  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="flex">
          <aside className="w-64 p-4 bg-gray-100 h-screen">
            <h2 className="text-xl font-bold mb-4">Subscriptions</h2>
            <ul className="space-y-2">
              {subscriptions.map(subscription => (
                <li key={subscription.id}>
                  <a href={`/feeds/${subscription.feed.id}`} className="text-blue-500 hover:underline">
                    {subscription.feed.title}
                  </a>
                </li>
              ))}
            </ul>
          </aside>
          <main className="flex-1 p-4">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
