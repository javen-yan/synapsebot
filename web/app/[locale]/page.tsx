"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Brain } from "lucide-react";
import { chatApi } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";
import { useTranslations } from "next-intl";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const t = useTranslations('Chat');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [thinking, setThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, thinking]);

  const handleSend = async () => {
    if (!input.trim() || streaming) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setThinking(true);

    // Add empty assistant message that will be filled
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      await chatApi.sendMessageStream(
        input,
        // onChunk
        (chunk: string) => {
          setThinking(false);
          setStreaming(true);
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage.role === "assistant") {
              lastMessage.content += chunk;
            }
            return newMessages;
          });
        },
        // onError
        (error: string) => {
          console.error("Stream error:", error);
          setThinking(false);
          setStreaming(false);
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage.role === "assistant" && !lastMessage.content) {
              lastMessage.content = `Error: ${error}`;
            }
            return newMessages;
          });
        },
        // onDone
        () => {
          setThinking(false);
          setStreaming(false);
        },
      );
    } catch (error) {
      console.error("Chat error:", error);
      setThinking(false);
      setStreaming(false);
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage.role === "assistant" && !lastMessage.content) {
          lastMessage.content = t('error');
        }
        return newMessages;
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="border-b border-slate-700 p-6 bg-slate-900">
        <h2 className="text-2xl font-semibold text-white">{t('title')}</h2>
        <p className="text-slate-400 text-sm mt-1">
          {t('subtitle')}
        </p>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-20">
            <p className="text-lg">
              {t('emptyState.title')}
            </p>
            <p className="text-sm mt-2">
              {t('emptyState.subtitle')}
            </p>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index}>
            <div
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-3xl rounded-2xl px-6 py-4 ${
                  message.role === "user"
                    ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white"
                    : "bg-slate-800 text-slate-100 border border-slate-700"
                }`}
              >
                {message.role === "user" ? (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <div className="prose prose-invert prose-slate max-w-none prose-headings:text-white prose-p:text-slate-200 prose-strong:text-white prose-code:text-cyan-300">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      rehypePlugins={[rehypeHighlight]}
                      components={{
                        code: ({
                          node,
                          inline,
                          className,
                          children,
                          ...props
                        }: any) => {
                          return inline ? (
                            <code
                              className="bg-slate-700 px-1.5 py-0.5 rounded text-cyan-300 font-mono text-sm"
                              {...props}
                            >
                              {children}
                            </code>
                          ) : (
                            <code className={className} {...props}>
                              {children}
                            </code>
                          );
                        },
                        pre: ({ children, ...props }: any) => (
                          <pre
                            className="bg-slate-900 border border-slate-700 rounded-lg p-4 overflow-x-auto my-3"
                            {...props}
                          >
                            {children}
                          </pre>
                        ),
                        a: ({ children, ...props }: any) => (
                          <a
                            className="text-cyan-400 hover:text-cyan-300 underline"
                            {...props}
                          >
                            {children}
                          </a>
                        ),
                        ul: ({ children, ...props }: any) => (
                          <ul
                            className="list-disc list-inside space-y-1 my-2"
                            {...props}
                          >
                            {children}
                          </ul>
                        ),
                        ol: ({ children, ...props }: any) => (
                          <ol
                            className="list-decimal list-inside space-y-1 my-2"
                            {...props}
                          >
                            {children}
                          </ol>
                        ),
                        h1: ({ children, ...props }: any) => (
                          <h1
                            className="text-2xl font-bold mt-4 mb-2 text-white"
                            {...props}
                          >
                            {children}
                          </h1>
                        ),
                        h2: ({ children, ...props }: any) => (
                          <h2
                            className="text-xl font-bold mt-3 mb-2 text-white"
                            {...props}
                          >
                            {children}
                          </h2>
                        ),
                        h3: ({ children, ...props }: any) => (
                          <h3
                            className="text-lg font-semibold mt-2 mb-1 text-white"
                            {...props}
                          >
                            {children}
                          </h3>
                        ),
                        p: ({ children, ...props }: any) => (
                          <p className="my-2 text-slate-200" {...props}>
                            {children}
                          </p>
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>

            {/* Thinking indicator - show after last message if thinking */}
            {index === messages.length - 1 && thinking && (
              <div className="flex justify-start mt-4">
                <div className="bg-slate-800 border border-slate-600 rounded-2xl px-6 py-4 flex items-center gap-3 shadow-lg shadow-cyan-900/10">
                  <Brain className="text-cyan-400 animate-pulse" size={20} />
                  <div className="flex gap-1 items-end">
                    <span className="text-slate-200 text-sm font-medium">{t('thinking')}</span>
                    <span className="animate-bounce delay-0 text-cyan-400 font-bold">.</span>
                    <span className="animate-bounce delay-100 text-cyan-400 font-bold">.</span>
                    <span className="animate-bounce delay-200 text-cyan-400 font-bold">.</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-700 p-6 bg-slate-900">
        <div className="max-w-4xl mx-auto flex gap-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={t('placeholder')}
            className="flex-1 bg-slate-800 border border-slate-600 rounded-xl px-6 py-4 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
            disabled={streaming || thinking}
          />
          <button
            onClick={handleSend}
            disabled={streaming || thinking || !input.trim()}
            className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl px-8 py-4 font-medium transition-all flex items-center gap-2 text-white"
          >
            {streaming || thinking ? (
              <Loader2 className="animate-spin" size={20} />
            ) : (
              <Send size={20} />
            )}
            {t('send')}
          </button>
        </div>
      </div>
    </div>
  );
}
