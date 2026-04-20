"use client";

import { useState, useEffect } from "react";

interface SymbolPriority {
  symbol: string;
  priority: number;
  enabled: boolean;
}

export default function PriorityAdjuster() {
  const [symbols, setSymbols] = useState<SymbolPriority[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    fetchSymbols();
  }, []);

  const fetchSymbols = async () => {
    try {
      const response = await fetch("/api/data/api/v1/researcher/symbols");
      const data = await response.json();
      if (data.success) {
        setSymbols(data.symbols);
      }
    } catch (error) {
      console.error("Failed to fetch symbols:", error);
    } finally {
      setLoading(false);
    }
  };

  const updatePriority = async (symbol: string, priority: number) => {
    try {
      const response = await fetch("/api/data/api/v1/researcher/symbols", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          symbol: symbol,
          priority: priority,
        }),
      });

      const data = await response.json();
      if (data.success) {
        // 更新本地状态
        setSymbols((prev) =>
          prev.map((s) => (s.symbol === symbol ? { ...s, priority } : s))
        );
      }
    } catch (error) {
      console.error("Failed to update priority:", error);
    }
  };

  const toggleSymbol = async (symbol: string, enabled: boolean) => {
    try {
      const response = await fetch("/api/data/api/v1/researcher/symbols", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          symbol: symbol,
          enabled: enabled,
        }),
      });

      const data = await response.json();
      if (data.success) {
        // 更新本地状态
        setSymbols((prev) =>
          prev.map((s) => (s.symbol === symbol ? { ...s, enabled } : s))
        );
      }
    } catch (error) {
      console.error("Failed to toggle symbol:", error);
    }
  };

  const filteredSymbols = symbols.filter((s) =>
    s.symbol.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedSymbols = [...filteredSymbols].sort(
    (a, b) => b.priority - a.priority
  );

  if (loading) {
    return <div className="text-center py-4">加载中...</div>;
  }

  return (
    <div className="space-y-4">
      {/* 搜索框 */}
      <div className="flex items-center space-x-4">
        <input
          type="text"
          placeholder="搜索品种..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <div className="text-sm text-muted-foreground">
          共 {symbols.length} 个品种，已启用{" "}
          {symbols.filter((s) => s.enabled).length} 个
        </div>
      </div>

      {/* 优先级说明 */}
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
        <div className="text-sm text-blue-400">
          <strong>优先级说明：</strong>
          <ul className="list-disc list-inside mt-1 space-y-1">
            <li>高优先级（8-10）：重点关注，异常立即分析</li>
            <li>中优先级（5-7）：正常关注，定期分析</li>
            <li>低优先级（1-4）：一般关注，批量分析</li>
          </ul>
        </div>
      </div>

      {/* 品种列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedSymbols.map((symbol) => (
          <div
            key={symbol.symbol}
            className={`border rounded-lg p-4 ${
              symbol.enabled ? "bg-card" : "bg-muted/50"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-lg">{symbol.symbol}</h3>
              <button
                onClick={() => toggleSymbol(symbol.symbol, !symbol.enabled)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  symbol.enabled
                    ? "bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                {symbol.enabled ? "启用" : "禁用"}
              </button>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">优先级:</span>
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    symbol.priority >= 8
                      ? "bg-red-500/20 text-red-400 border border-red-500/30"
                      : symbol.priority >= 5
                      ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {symbol.priority}
                </span>
              </div>

              <input
                type="range"
                min="1"
                max="10"
                value={symbol.priority}
                onChange={(e) =>
                  updatePriority(symbol.symbol, parseInt(e.target.value))
                }
                className="w-full"
                disabled={!symbol.enabled}
              />

              <div className="flex justify-between text-xs text-muted-foreground">
                <span>低</span>
                <span>中</span>
                <span>高</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {sortedSymbols.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          {searchTerm ? "未找到匹配的品种" : "暂无品种配置"}
        </div>
      )}
    </div>
  );
}
