"use client";

import { useState, useEffect } from "react";
import { Loader2, Search } from "lucide-react";
import { toolsApi, type Tool } from "@/lib/api";
import { useTranslations } from "next-intl";
import Editor from "@monaco-editor/react";

export default function ToolsPage() {
  const t = useTranslations('Tools');
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showConfig, setShowConfig] = useState(false);
  const [configJson, setConfigJson] = useState("");
  const [saving, setSaving] = useState(false);

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

  const handleOpenConfig = async () => {
    try {
      const config = await toolsApi.getConfig();
      setConfigJson(JSON.stringify(config, null, 2));
      setShowConfig(true);
    } catch (error) {
      console.error("Failed to load config:", error);
      alert(t('config.error'));
    }
  };

  const handleSaveConfig = async () => {
    try {
      setSaving(true);
      const config = JSON.parse(configJson);
      await toolsApi.updateConfig(config);
      await toolsApi.reload();
      alert(t('config.reloadSuccess'));
      setShowConfig(false);
      loadTools();
    } catch (error: any) {
      console.error("Failed to save config:", error);
      alert(error.message || t('config.error'));
    } finally {
      setSaving(false);
    }
  };

  const filteredTools = tools.filter(
    (tool) =>
      tool.name.toLowerCase().includes(search.toLowerCase()) ||
      tool.description.toLowerCase().includes(search.toLowerCase()) ||
      tool.source.toLowerCase().includes(search.toLowerCase()),
  );

  // Group tools by source
  const groupedTools = filteredTools.reduce((acc, tool) => {
    const source = tool.source || 'Other';
    if (!acc[source]) {
      acc[source] = [];
    }
    acc[source].push(tool);
    return acc;
  }, {} as Record<string, Tool[]>);

  return (
    <div className="p-6 relative">
       {/* Config Modal */}
      {showConfig && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-4xl flex flex-col h-[80vh]">
            <div className="p-6 border-b border-slate-700 flex justify-between items-center">
              <h3 className="text-xl font-semibold text-white">{t('config.title')}</h3>
              <button onClick={() => setShowConfig(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>
            <div className="flex-1 overflow-hidden bg-[#1e1e1e]">
               <Editor
                height="100%"
                defaultLanguage="json"
                theme="vs-dark"
                value={configJson}
                onChange={(value) => setConfigJson(value || "")}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  scrollBeyondLastLine: false,
                  wordWrap: "on",
                }}
              />
            </div>
            <div className="p-6 border-t border-slate-700 flex justify-end gap-3 bg-slate-900">
              <button
                onClick={() => setShowConfig(false)}
                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                disabled={saving}
              >
                {t('config.cancel')}
              </button>
              <button
                onClick={handleSaveConfig}
                className="bg-cyan-600 hover:bg-cyan-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                disabled={saving}
              >
                {saving ? t('config.saving') : t('config.save')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-8 flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-semibold text-white">{t('title')}</h2>
          <p className="text-slate-400 text-sm mt-1">
            {t('subtitle')}
          </p>
        </div>
        <button
           onClick={handleOpenConfig}
           className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-slate-700 hover:border-slate-600"
        >
          {t('config.button')}
        </button>
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
            placeholder={t('search.placeholder')}
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
        <div className="space-y-8">
          {Object.entries(groupedTools).map(([source, groupTools]) => (
            <div key={source}>
              <h3 className="text-xl font-bold text-slate-200 mb-4 flex items-center gap-2">
                <span className="capitalize">{source}</span>
                <span className="text-xs bg-slate-800 text-slate-400 px-2 py-1 rounded-full">
                  {groupTools.length}
                </span>
              </h3>
              <div className="grid grid-cols-1 gap-4">
                {groupTools.map((tool) => (
                  <div
                    key={tool.name}
                    className="bg-slate-900 border border-slate-700 rounded-xl p-6 hover:border-cyan-500 transition-all"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h4 className="text-lg font-semibold font-mono text-cyan-400">
                          {tool.name}
                        </h4>
                        <p className="text-slate-300 text-sm mt-2">
                          {tool.description}
                        </p>
                      </div>
                    </div>

                    {tool.input_schema && (
                      <details className="mt-4">
                        <summary className="cursor-pointer text-sm text-slate-400 hover:text-cyan-400 transition-colors">
                          {t('list.viewSchema')}
                        </summary>
                        <pre className="mt-3 bg-slate-950 border border-slate-700 rounded-lg p-4 text-xs overflow-x-auto text-slate-300">
                          {JSON.stringify(tool.input_schema, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}

          {filteredTools.length === 0 && (
            <div className="text-center text-slate-400 py-12">
              <p>{t('list.empty')}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
