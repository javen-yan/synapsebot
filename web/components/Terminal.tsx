'use client';

import React, { useEffect, useRef } from 'react';
import '@xterm/xterm/css/xterm.css';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';

interface TerminalComponentProps {
  wsUrl?: string; // Optional override
}

const TerminalComponent: React.FC<TerminalComponentProps> = ({ wsUrl }) => {
  const terminalRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const termRef = useRef<Terminal | null>(null);

  useEffect(() => {
    // Determine WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // Use current host (Next.js is proxying or same origin)
    // If running dev server on 3000 and API on 8000, we might need configuration.
    // Assuming API is proxied or we point to 8000 directly. 
    // Let's assume for now we need to point to port 8000 if in dev mode on localhost
    
    let url = wsUrl;
    if (!url) {
        // Simple heuristic for dev environment
        if (host.includes('localhost:3000')) {
             url = `${protocol}//localhost:8000/ws/shell`;
        } else {
             url = `${protocol}//${host}/api/ws/shell`; // Assuming /api rewrite or similar
             // Or just direct if on same port
             if (!url) url = `${protocol}//${host}/ws/shell`;
        }
    }

    // Initialize xterm
    const term = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#f0f0f0',
      },
    });
    
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    term.loadAddon(new WebLinksAddon());

    if (terminalRef.current) {
      term.open(terminalRef.current);
      fitAddon.fit();
      termRef.current = term;
    }

    // Connect WebSocket
    const ws = new WebSocket(url!);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => {
      term.writeln('\x1b[1;32mConnected to SynapseBot Shell\x1b[0m');
      
      // Send initial resize
      const dims = { cols: term.cols, rows: term.rows };
      ws.send(`RESIZE:${dims.rows}:${dims.cols}`);
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        term.write(event.data);
      } else {
        term.write(new Uint8Array(event.data));
      }
    };

    ws.onclose = () => {
      term.writeln('\r\n\x1b[1;31mConnection closed\x1b[0m');
    };

    ws.onerror = (err) => {
      term.writeln(`\r\n\x1b[1;31mConnection error: ${err}\x1b[0m`);
    };

    // Terminal -> WebSocket
    const disposable = term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
      }
    });

    // Handle Resize
    const handleResize = () => {
      fitAddon.fit();
      if (ws.readyState === WebSocket.OPEN) {
         ws.send(`RESIZE:${term.rows}:${term.cols}`);
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      disposable.dispose();
      term.dispose();
      ws.close();
    };
  }, [wsUrl]);

  return (
    <div 
      ref={terminalRef} 
      className="w-full h-full min-h-[500px] bg-[#1e1e1e] rounded-lg overflow-hidden p-2"
    />
  );
};

export default TerminalComponent;
