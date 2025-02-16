import { useEffect, useState } from 'react';

export default function Feeds() {
  const [feeds, setFeeds] = useState([]);

  useEffect(() => {
    fetch('/api/feeds')
      .then(response => response.json())
      .then(data => setFeeds(data));
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Feeds</h1>
      <ul className="space-y-4">
        {feeds.map(feed => (
          <li key={feed.id} className="p-4 border rounded-lg shadow-md">
            <h2 className="text-xl font-semibold">{feed.title}</h2>
            <p className="text-gray-700">{feed.description}</p>
            <a
              href={feed.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:underline"
            >
              {feed.url}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
