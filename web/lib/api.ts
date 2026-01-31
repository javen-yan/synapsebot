import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ChatRequest {
  message: string;
  files?: string[];
}

export interface ChatResponse {
  response: string;
}

export interface Skill {
  name: string;
  description: string;
  path: string;
}

export interface Tool {
  name: string;
  description: string;
  input_schema: any;
  source: string;
}

export const chatApi = {
  API_BASE_URL,
  sendMessage: async (message: string, files: string[] = []): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', { message, files });
    return response.data;
  },
  connectWebSocket: (
    onMessage: (data: any) => void,
    onStatus: (data: any) => void,
    onError: (error: string) => void,
    onDone: () => void
  ) => {
    // Convert http(s) to ws(s)
    const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws';
    const wsUrl = `${API_BASE_URL.replace(/^https?:\/\//, '')}/ws/chat`;
    
    // Construct full URL with protocol
    const socket = new WebSocket(`${wsProtocol}://${wsUrl}`);

    socket.onopen = () => {
      console.log('WebSocket Connected');
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'status') {
            onStatus(data);
        } else if (data.type === 'chunk') {
            // Chunk with content
            onMessage(data);
        } else if (data.type === 'message') {
            // Final message with files
            onMessage(data);
        } else if (data.type === 'done') {
            // Streaming complete
            onDone();
        } else if (data.error) {
            onError(data.error);
        }
      } catch (e) {
        console.error("WS Parse Error", e);
      }
    };

    socket.onerror = (error) => {
      console.error("WebSocket Error", error);
      onError("WebSocket connection error");
    };

    socket.onclose = () => {
      console.log('WebSocket Disconnected');
    };

    return {
        send: (message: string, files: string[] = []) => {
            if (socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ text: message, files }));
            } else {
                console.warn("WebSocket not open");
                onError("Connection lost");
            }
        },
        close: () => socket.close()
    };
  },
  uploadFile: async (file: File): Promise<{ name: string; path: string; url: string; size: number; type: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

export const skillsApi = {
  list: async (): Promise<Skill[]> => {
    const response = await api.get<Skill[]>('/skills');
    return response.data;
  },
  upload: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/skills/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  delete: async (name: string) => {
    const response = await api.delete(`/skills/${name}`);
    return response.data;
  },
};

export const toolsApi = {
  list: async (): Promise<Tool[]> => {
    const response = await api.get<Tool[]>('/mcp/tools');
    return response.data;
  },
  getConfig: async () => {
    const response = await api.get('/config/mcp');
    return response.data;
  },
  updateConfig: async (config: any) => {
    const response = await api.post('/config/mcp', config);
    return response.data;
  },
  reload: async () => {
    const response = await api.post('/mcp/reload');
    return response.data;
  },
};
