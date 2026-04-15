"use client";

import { useState, useEffect } from "react";

interface Analysis {
  symbol: string;
  event_type: string;
  content: string;
  timestamp: string;
}

interface Report {
  timestamp: string;
  segment: string;
  summary: string;
  analyses: Analysis[];
}

export default function ReportViewer() {
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedSegment, setSelectedSegment] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReports();
  }, [selectedSegment]);

  const fetchReports = async () => {
    try {
      const params = new URLSearchParams();
      if (selectedSegment !== "all") {
        params.append("segment", selectedSegment);
      }
      params.append("limit", "10");

      const response = await fetch(
        `/api/data/api/v1/researcher/reports?${params}`
      );
      const data = await response.json();
      if (data.success) {
        setReports(data.reports);
      }
    } catch (error) {
      console.error("Failed to fetch reports:", error);
    } finally {
      setLoading(false);
    }
  };

  const segments = ["all", "盘前", "午间", "盘后", "夜盘收盘"];

  if (loading) {
    return <div className="text-center py-4">加载中...</div>;
  }

  return (
    <div className="space-y-4">
      {/* 时段筛选 */}
      <div className="flex space-x-2">
        {segments.map((segment) => (
          <button
            key={segment}
            onClick={() => setSelectedSegment(segment)}
            className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
              selectedSegment === segment
                ? "bg-blue-500 text-white"
                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
            }`}
          >
            {segment === "all" ? "全部" : segment}
          </button>
        ))}
      </div>

      {/* 报告列表 */}
      <div className="space-y-4">
        {reports.map((report, index) => (
          <div key={index} className="border rounded-lg p-4 hover:shadow-md">
            {/* 报告头部 */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-3">
                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm font-medium">
                  {report.segment}
                </span>
                <span className="text-sm text-gray-600">
                  {new Date(report.timestamp).toLocaleString()}
                </span>
              </div>
              <button
                onClick={() => {
                  // 下载报告
                  const blob = new Blob([JSON.stringify(report, null, 2)], {
                    type: "application/json",
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `report-${report.timestamp}.json`;
                  a.click();
                }}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                下载
              </button>
            </div>

            {/* 摘要 */}
            <div className="mb-3">
              <h4 className="font-medium text-gray-900 mb-1">市场概况</h4>
              <p className="text-sm text-gray-700">{report.summary}</p>
            </div>

            {/* 关键事件 */}
            {report.analyses && report.analyses.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">
                  关键事件 ({report.analyses.length})
                </h4>
                <div className="space-y-2">
                  {report.analyses.slice(0, 5).map((analysis, idx) => (
                    <div
                      key={idx}
                      className="flex items-start space-x-3 text-sm"
                    >
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium min-w-[60px] text-center">
                        {analysis.symbol}
                      </span>
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-medium">
                        {analysis.event_type}
                      </span>
                      <p className="flex-1 text-gray-700">{analysis.content}</p>
                    </div>
                  ))}
                  {report.analyses.length > 5 && (
                    <div className="text-sm text-gray-500 text-center">
                      还有 {report.analyses.length - 5} 条事件...
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}

        {reports.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            暂无报告数据
          </div>
        )}
      </div>
    </div>
  );
}
