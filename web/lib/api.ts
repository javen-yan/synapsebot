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
  sendMessage: async (message: string): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>('/chat', { message });
    return response.data;
  },
  sendMessageStream: async (
    message: string,
    onChunk: (chunk: string) => void,
    onError: (error: string) => void,
    onDone: () => void
  ) => {
    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error('Stream request failed');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);
              
              if (parsed.type === 'content') {
                onChunk(parsed.chunk);
              } else if (parsed.type === 'done') {
                onDone();
                return;
              } else if (parsed.error || parsed.type === 'error') {
                onError(parsed.error || 'Unknown error');
                return;
              }
            } catch (e) {
              // Ignore parse errors for incomplete chunks
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
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
