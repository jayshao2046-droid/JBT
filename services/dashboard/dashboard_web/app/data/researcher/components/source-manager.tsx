"use client";

import { useState, useEffect } from "react";

interface DataSource {
  name: string;
  url: string;
  enabled: boolean;
  interval: number;
  type: string;
}

export default function SourceManager() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSources();
  }, []);

  const fetchSources = async () => {
    try {
      const response = await fetch("/api/data/api/v1/researcher/sources");
      const data = await response.json();
      if (data.success) {
        setSources(data.sources);
      }
    } catch (error) {
      console.error("Failed to fetch sources:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSource = async (sourceName: string, enabled: boolean) => {
    try {
      const response = await fetch("/api/data/api/v1/researcher/sources", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: sourceName,
          enabled: enabled,
        }),
      });

      const data = await response.json();
      if (data.success) {
        // 更新本地状态
        setSources((prev) =>
          prev.map((source) =>
            source.name === sourceName ? { ...source, enabled } : source
          )
        );
      }
    } catch (error) {
      console.error("Failed to toggle source:", error);
    }
  };

  const updateInterval = async (sourceName: string, interval: number) => {
    try {
      const response = await fetch("/api/data/api/v1/researcher/sources", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: sourceName,
          interval: interval,
        }),
      });

      const data = await response.json();
      if (data.success) {
        // 更新本地状态
        setSources((prev) =>
          prev.map((source) =>
            source.name === sourceName ? { ...source, interval } : source
          )
        );
      }
    } catch (error) {
      console.error("Failed to update interval:", error);
    }
  };

  if (loading) {
    return <div className="text-center py-4">加载中...</div>;
  }

  return (
    <div className="space-y-4">
      {sources.map((source) => (
        <div
          key={source.name}
          className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
        >
          <div className="flex-1">
            <div className="flex items-center space-x-3">
              <h3 className="font-medium">{source.name}</h3>
              <span
                className={`px-2 py-1 text-xs rounded ${
                  source.type === "news"
                    ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                    : "bg-green-500/20 text-green-400 border border-green-500/30"
                }`}
              >
                {source.type}
              </span>
            </div>
            <div className="text-sm text-muted-foreground mt-1">{source.url}</div>
          </div>

          <div className="flex items-center space-x-4">
            {/* 采集间隔 */}
            <div className="flex items-center space-x-2">
              <label className="text-sm text-muted-foreground">间隔(秒):</label>
              <input
                type="number"
                value={source.interval}
                onChange={(e) =>
                  updateInterval(source.name, parseInt(e.target.value))
                }
                className="w-20 px-2 py-1 border rounded text-sm bg-background"
                min="60"
                step="60"
              />
            </div>

            {/* 开关 */}
            <button
              onClick={() => toggleSource(source.name, !source.enabled)}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                source.enabled
                  ? "bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              {source.enabled ? "已启用" : "已禁用"}
            </button>
          </div>
        </div>
      ))}

      {sources.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          暂无数据源配置
        </div>
      )}
    </div>
  );
}
