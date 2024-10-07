// src/VideoGenerator.tsx
'use client'
// src/App.tsx
import React, { useState } from "react";

const App: React.FC = () => {
  const [youtubeUrl, setYoutubeUrl] = useState<string>("");
  const [startTime, setStartTime] = useState<string>("");
  const [endTime, setEndTime] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); // Ativar estado de carregamento
    setMessage("");
    setVideoUrl("");

    const data = {
      url: youtubeUrl,
      start_time: startTime ? parseInt(startTime) : null,
      end_time: endTime ? parseInt(endTime) : null,
    };

    try {
      const response = await fetch("http://localhost:8000/api/process_video", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();
      if (response.ok) {
        setMessage(result.message);
        setVideoUrl(result.video_path);
      } else {
        setMessage(`Erro: ${result.error}`);
      }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (error) {
      setMessage("Erro ao processar o vídeo.");
    } finally {
      setLoading(false); // Desativar estado de carregamento
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center">
      <div className="max-w-md w-full bg-white p-8 rounded shadow-md">
        <h2 className="text-2xl font-bold mb-4">Gerador de Vídeos para TikTok</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">URL do YouTube:</label>
            <input
              type="text"
              className="mt-1 block w-full border border-gray-300 rounded p-2"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              required
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">Início (segundos):</label>
            <input
              type="text"
              className="mt-1 block w-full border border-gray-300 rounded p-2"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">Fim (segundos):</label>
            <input
              type="text"
              className="mt-1 block w-full border border-gray-300 rounded p-2"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-500 text-white py-2 rounded hover:bg-blue-600"
            disabled={loading}
          >
            {loading ? "Processando..." : "Processar"}
          </button>
        </form>
        {message && <p className="mt-4 text-center text-sm text-gray-600">{message}</p>}
        {videoUrl && (
          <div className="mt-4">
            <h2 className="text-lg font-bold mb-2">Vídeo Processado:</h2>
            <video controls className="w-full">
              <source src={videoUrl} type="video/mp4" />
            </video>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
