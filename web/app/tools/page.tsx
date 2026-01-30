"use client";

import { useState, useEffect } from "react";
import { Loader2, Search } from "lucide-react";
import { toolsApi, type Tool } from "@/lib/api";

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      const data = await toolsApi.list();
      setTools(data);
    } catch (error) {
      console.error("Failed to load tools:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTools = tools.filter(
    (tool) =>
      tool.name.toLowerCase().includes(search.toLowerCase()) ||
      tool.description.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-white">MCP Tools</h2>
        <p className="text-slate-400 text-sm mt-1">
          Available tools from MCP servers
        </p>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative max-w-xl">
          <Search
            className="absolute left-4 top-1/2 transform -translate-y-1/2 text-slate-400"
            size={20}
          />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tools..."
            className="w-full bg-slate-800 border border-slate-600 rounded-lg pl-12 pr-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>
      </div>

      {/* Tools List */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="animate-spin text-cyan-400" size={32} />
        </div>
      ) : (
        <div className="space-y-4">
          {filteredTools.map((tool) => (
            <div
              key={tool.name}
              className="bg-slate-900 border border-slate-700 rounded-xl p-6 hover:border-cyan-500 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-semibold font-mono text-cyan-400">
                    {tool.name}
                  </h3>
                  <p className="text-slate-300 text-sm mt-2">
                    {tool.description}
                  </p>
                </div>
              </div>

              {tool.input_schema && (
                <details className="mt-4">
                  <summary className="cursor-pointer text-sm text-slate-400 hover:text-cyan-400 transition-colors">
                    View Schema
                  </summary>
                  <pre className="mt-3 bg-slate-950 border border-slate-700 rounded-lg p-4 text-xs overflow-x-auto text-slate-300">
                    {JSON.stringify(tool.input_schema, null, 2)}
                  </pre>
                </details>
              )}
            </div>
          ))}

          {filteredTools.length === 0 && (
            <div className="text-center text-slate-400 py-12">
              <p>No tools found matching your search</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
