'use client';

import dynamic from 'next/dynamic';

const Terminal = dynamic(() => import('@/components/Terminal'), {
  ssr: false,
  loading: () => <div className="text-white">Loading Terminal...</div>,
});

export default function TerminalPage() {
  return (
    <div className="flex flex-col h-full bg-gray-900 text-white p-4">
      <h1 className="text-2xl font-bold mb-4">Agent Terminal</h1>
      <div className="flex-1 border border-gray-700 rounded-lg overflow-hidden">
        <Terminal />
      </div>
    </div>
  );
}
