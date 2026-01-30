"use client";

import { useState, useEffect, useRef } from "react";
import { Upload, Trash2, Loader2, FileArchive } from "lucide-react";
import { skillsApi, type Skill } from "@/lib/api";
import { useTranslations } from "next-intl";

export default function SkillsPage() {
  const t = useTranslations('Skills');
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadSkills();
  }, []);

  const loadSkills = async () => {
    try {
      const data = await skillsApi.list();
      setSkills(data);
    } catch (error) {
      console.error("Failed to load skills:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!file.name.endsWith(".zip")) {
      alert(t('upload.alert'));
      return;
    }

    setUploading(true);
    try {
      await skillsApi.upload(file);
      loadSkills();
    } catch (error: any) {
      console.error("Failed to upload skill:", error);
      alert(error.response?.data?.detail || t('upload.error'));
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(t('list.deleteConfirm', {name}))) return;
    try {
      await skillsApi.delete(name);
      loadSkills();
    } catch (error) {
      console.error("Failed to delete skill:", error);
    }
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-white">{t('title')}</h2>
        <p className="text-slate-400 text-sm mt-1">
          {t('subtitle')}
        </p>
      </div>

      {/* Upload Zone */}
      <div
        className={`mb-8 border-2 border-dashed rounded-xl p-8 transition-all ${
          dragActive
            ? "border-cyan-500 bg-cyan-500/10"
            : "border-slate-700 hover:border-slate-600"
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4">
            {uploading ? (
              <Loader2 className="animate-spin text-cyan-400" size={32} />
            ) : (
              <FileArchive className="text-cyan-400" size={32} />
            )}
          </div>
          <h3 className="text-lg font-semibold text-white mb-2">
            {uploading ? t('upload.uploading') : t('upload.title')}
          </h3>
          <p className="text-slate-400 text-sm mb-4">
            {t('upload.dragDrop')}
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={handleFileChange}
            className="hidden"
            disabled={uploading}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 disabled:opacity-50 rounded-lg px-6 py-3 font-medium transition-all flex items-center gap-2 text-white"
          >
            <Upload size={20} />
            {t('upload.button')}
          </button>
        </div>
      </div>

      {/* Skills Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <Loader2 className="animate-spin text-cyan-400" size={32} />
        </div>
      ) : skills.length === 0 ? (
        <div className="text-center text-slate-400 py-12">
          <p>{t('list.emptyDict')}</p>
          <p className="text-sm mt-2">{t('list.emptySubtitle')}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {skills.map((skill) => (
            <div
              key={skill.name}
              className="bg-slate-900 border border-slate-700 rounded-xl p-6 hover:border-cyan-500 transition-all"
            >
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-white">
                  {skill.name}
                </h3>
                <button
                  onClick={() => handleDelete(skill.name)}
                  className="text-red-400 hover:text-red-300 transition-colors"
                >
                  <Trash2 size={18} />
                </button>
              </div>
              <p className="text-slate-300 text-sm">{skill.description}</p>
              <p className="text-xs text-slate-600 mt-4">{skill.path}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
