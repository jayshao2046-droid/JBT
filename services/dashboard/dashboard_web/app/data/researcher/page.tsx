"use client";

import { useState, useEffect } from "react";
import SourceManager from "./components/source-manager";
import ReportViewer from "./components/report-viewer";
import PriorityAdjuster from "./components/priority-adjuster";

interface ResearcherStatus {
  running: boolean;
  processes: {
    kline_monitor: boolean;
    news_crawler: boolean;
    fundamental_crawler: boolean;
    llm_analyzer: boolean;
    report_generator: boolean;
  };
  last_report_time: string;
  total_analyses: number;
}

export default function ResearcherPage() {
  const [status, setStatus] = useState<ResearcherStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // 每 30 秒刷新
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch("/api/data/api/v1/researcher/status");
      const data = await response.json();
      if (data.success) {
        setStatus(data.status);
      }
    } catch (error) {
      console.error("Failed to fetch researcher status:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">加载中...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 标题和状态 */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">研究员 24/7 控制台</h1>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div
              className={`w-3 h-3 rounded-full ${
                status?.running ? "bg-green-500" : "bg-red-500"
              }`}
            />
            <span className="text-sm font-medium">
              {status?.running ? "运行中" : "已停止"}
            </span>
          </div>
          {status?.last_report_time && (
            <div className="text-sm text-muted-foreground">
              最后报告: {new Date(status.last_report_time).toLocaleString()}
            </div>
          )}
        </div>
      </div>

      {/* 进程状态卡片 */}
      {status && (
        <div className="grid grid-cols-5 gap-4">
          {Object.entries(status.processes).map(([name, running]) => (
            <div
              key={name}
              className={`rounded-lg shadow p-4 border-l-4 ${
                running
                  ? "bg-green-500/10 border-green-500"
                  : "bg-red-500/10 border-red-500"
              }`}
            >
              <div className="text-sm font-medium text-muted-foreground mb-1">
                {name.replace(/_/g, " ").toUpperCase()}
              </div>
              <div className="text-xs text-muted-foreground">
                {running ? "运行中" : "已停止"}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 统计信息 */}
      {status && (
        <div className="bg-card rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">统计信息</h2>
          <div className="grid grid-cols-3 gap-6">
            <div>
              <div className="text-sm text-muted-foreground">总分析数</div>
              <div className="text-2xl font-bold">{status.total_analyses}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">运行进程</div>
              <div className="text-2xl font-bold">
                {Object.values(status.processes).filter(Boolean).length} / 5
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">系统状态</div>
              <div className="text-2xl font-bold">
                {status.running ? "正常" : "异常"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 数据源管理 */}
      <div className="bg-card rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">数据源管理</h2>
        <SourceManager />
      </div>

      {/* 优先级调整 */}
      <div className="bg-card rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">品种优先级</h2>
        <PriorityAdjuster />
      </div>

      {/* 报告查看器 */}
      <div className="bg-card rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">最新报告</h2>
        <ReportViewer />
      </div>
    </div>
  );
}
