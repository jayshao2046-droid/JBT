"use client";
// Build timestamp: 2026-03-17T18:45:00Z
// React and providers
import { useState, useEffect, useCallback } from "react";
import { OrbitProvider, useOrbit } from "@/components/orbit/orbit-provider";
import { ToastProvider } from "@/components/orbit/toast-provider";

// Core navigation and layout
import { CommandDock, type ViewType } from "@/components/orbit/command-dock";
import { AccountList } from "@/components/orbit/account-list";
import { CommandStage } from "@/components/orbit/command-stage";
import { CommandKMenu } from "@/components/orbit/command-k-menu";
import { AccountModal } from "@/components/orbit/modals/account-modal";
import { ThemeToggle } from "@/components/orbit/theme-toggle";

// Main views
import { PortfolioPulse } from "@/components/orbit/portfolio-pulse";
import { AnalyticsView } from "@/components/orbit/analytics-view";
import { SettingsView } from "@/components/orbit/settings-view";
import { AIChatPanel } from "@/components/orbit/ai-chat-panel";

// Deep dive views
import { ContractDeepDive } from "@/components/orbit/contract-deep-dive";
import { StockDeepDive } from "@/components/orbit/stock-deep-dive";

// Trading views
import { FuturesTrading } from "@/components/orbit/futures-trading";
import { ChinaAStockTrading } from "@/components/orbit/china-astock-trading";
import { StrategyFutures } from "@/components/orbit/strategy-futures";
import { StrategyAStock } from "@/components/orbit/strategy-astock";

// Monitoring views
import { DataCollectionView } from "@/components/orbit/data-collection-view";
import { APIQuotaView } from "@/components/orbit/api-quota-view";
import { StorageView } from "@/components/orbit/storage-view";
import { RiskMonitorView } from "@/components/orbit/risk-monitor-view";
import { AlertRecordsView } from "@/components/orbit/alert-records-view";
import { ComplianceReportView } from "@/components/orbit/compliance-report-view";
import { DeviceHeartbeatView } from "@/components/orbit/device-heartbeat-view";
import { ProcessMonitorView } from "@/components/orbit/process-monitor-view";
import { LogRecordsView } from "@/components/orbit/log-records-view";

// Settings views
import { StrategyParamsView } from "@/components/orbit/strategy-params-view";
import { RiskParamsView } from "@/components/orbit/risk-params-view";
import { CollectionParamsView } from "@/components/orbit/collection-params-view";
import { NotificationConfigView } from "@/components/orbit/notification-config-view";

// Hooks and types
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";
import type { Account } from "@/lib/mock-data";

function OrbitAppContent() {
  const {
    selectedAccountId,
    selectAccount,
    getAccountById,
    activeView,
    setActiveView,
  } = useOrbit();

  const [showAccountModal, setShowAccountModal] = useState(false);
  const [showAIChat, setShowAIChat] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | undefined>(
    undefined
  );

  const selectedAccount = selectedAccountId
    ? getAccountById(selectedAccountId)
    : null;

  const handleSelectAccount = (account: Account) => {
    selectAccount(account.id);
    setActiveView("accounts");
  };

  const handleBackToDashboard = () => {
    selectAccount(null);
  };

  const handleViewChange = (view: ViewType) => {
    setActiveView(view);
    // Clear selected account when navigating to a different main view
    if (view !== "accounts") {
      selectAccount(null);
    }
  };

  const handleNewAccount = () => {
    setEditingAccount(undefined);
    setShowAccountModal(true);
  };

  const handleEditAccount = (account: Account) => {
    setEditingAccount(account);
    setShowAccountModal(true);
  };

  const handleAccountCreated = (account: Account) => {
    // Navigate to the new account
    selectAccount(account.id);
    setActiveView("accounts");
  };

  // Global keyboard shortcuts
  useKeyboardShortcuts([
    // Escape to deselect account or go back
    {
      key: "Escape",
      action: () => {
        if (selectedAccountId) {
          selectAccount(null);
        } else if (activeView !== "dashboard") {
          setActiveView("dashboard");
        }
      },
      description: "返回/取消选择",
    },
    // Ctrl+1 to go to dashboard
    {
      key: "1",
      ctrl: true,
      action: () => setActiveView("dashboard"),
      description: "打开仪表盘",
    },
    // Ctrl+2 to go to futures
    {
      key: "2",
      ctrl: true,
      action: () => setActiveView("china-futures"),
      description: "打开中国期货",
    },
    // Ctrl+3 to go to A-stock
    {
      key: "3",
      ctrl: true,
      action: () => setActiveView("china-a-stock"),
      description: "打开中国A股",
    },
    // Ctrl+4 to go to analytics
    {
      key: "4",
      ctrl: true,
      action: () => setActiveView("analytics"),
      description: "打开数据分析",
    },
    // Ctrl+, to go to settings
    {
      key: ",",
      ctrl: true,
      action: () => setActiveView("settings"),
      description: "打开设置",
    },
    // Ctrl+N to create new account
    {
      key: "n",
      ctrl: true,
      action: handleNewAccount,
      description: "新建账户",
    },
    // Ctrl+R to refresh (prevent default refresh)
    {
      key: "r",
      ctrl: true,
      action: () => {
        // Could trigger data refresh here
        window.location.reload();
      },
      description: "刷新页面",
      preventDefault: true,
    },
  ]);

  // Helper function to get contract name from code
  const getContractName = (code: string): string => {
    const names: Record<string, string> = {
      'm2405': '豆粕',
      'rb2405': '螺纹钢',
      'hc2405': '热卷',
      'i2405': '铁矿石',
      'y2405': '豆油',
    };
    return names[code.toLowerCase()] || '螺纹钢';
  };

  // Helper function to get stock name from code
  const getStockName = (code: string): string => {
    const names: Record<string, string> = {
      '600809': '山西汾酒',
      '600519': '贵州茅台',
      '000568': '泸州老窖',
      '601888': '中国中免',
      '002415': '海康威视',
      '601166': '兴业银行',
      '600036': '招商银行',
      '600585': '海螺水泥',
      '000858': '五粮液',
      '601318': '中国平安',
      '000333': '美的集团',
      '000651': '格力电器',
      '600276': '恒瑞医药',
      '000725': '长虹美菱',
      '600887': '伊利股份',
    };
    return names[code] || '贵州茅台';
  };

  // Determine what to show in the Command Stage
  const renderStageContent = () => {
    // If showing china-futures view specifically
    if (activeView === 'china-futures') {
      return (
        <FuturesTrading
          onBack={() => setActiveView('dashboard')}
        />
      );
    }

    // If showing china-a-stock view specifically
    if (activeView === 'china-a-stock') {
      return (
        <ChinaAStockTrading
          onBack={() => setActiveView('dashboard')}
        />
      );
    }

    // If showing strategy-china-futures view specifically
    if (activeView === 'strategy-china-futures') {
      return (
        <StrategyFutures
          onBack={() => setActiveView('dashboard')}
        />
      );
    }

    // If showing strategy-china-a-stock view specifically
    if (activeView === 'strategy-china-a-stock') {
      return (
        <StrategyAStock
          onBack={() => setActiveView('dashboard')}
        />
      );
    }

    // If showing data-collection view specifically
    if (activeView === 'data-collection') {
      return <DataCollectionView />;
    }

    // If showing api-quota view specifically
    if (activeView === 'api-quota') {
      return <APIQuotaView />;
    }

    // If showing storage view specifically
    if (activeView === 'storage') {
      return <StorageView />;
    }

    // If showing risk-monitor view specifically
    if (activeView === 'risk-monitor') {
      return <RiskMonitorView />;
    }

    // If showing alert-records view specifically
    if (activeView === 'alert-records') {
      return <AlertRecordsView />;
    }

  // If showing compliance-report view specifically
  if (activeView === 'compliance-report') {
    return <ComplianceReportView />;
  }
  
  // If showing device-heartbeat view specifically
  if (activeView === 'device-heartbeat') {
    return <DeviceHeartbeatView />;
  }

  // If showing process-monitor view specifically
  if (activeView === 'process-monitor') {
    return <ProcessMonitorView />;
  }

  // If showing log-records view specifically
  if (activeView === 'log-records') {
    return <LogRecordsView />;
  }

  // If showing futures-detail view specifically
  if (activeView === 'futures-detail') {
    // Extract contract code from selectedAccountId (format: "futures-m2405")
    const contractCode = selectedAccountId?.replace('futures-', '') || 'rb2405';
    return (
      <ContractDeepDive
        contractCode={contractCode}
        contractName={getContractName(contractCode)}
        status="main"
        onBack={() => setActiveView('dashboard')}
      />
    );
  }

  // If showing stock-detail view specifically
  if (activeView === 'stock-detail') {
    // Extract stock code from selectedAccountId (format: "stock-600519")
    const stockCode = selectedAccountId?.replace('stock-', '') || '600519';
    return (
      <StockDeepDive
        stockCode={stockCode}
        stockName={getStockName(stockCode)}
        status="trading"
        onBack={() => setActiveView('dashboard')}
      />
    );
  }
  
  // If an account is selected, show the deep dive
    if (selectedAccount) {
      // Check if it's Nexus Retail - show stock detail page
      if (selectedAccount.name === 'Nexus Retail') {
        return (
          <StockDeepDive
            onBack={handleBackToDashboard}
          />
        );
      }
      // Check if it's Acme Corporation - show futures trading page (legacy)
      if (selectedAccount.name === 'Acme Corporation') {
        return (
          <FuturesTrading
            onBack={handleBackToDashboard}
          />
        );
      }
      // Default: show contract detail page
      return (
        <ContractDeepDive
          onBack={handleBackToDashboard}
        />
      );
    }

    // Otherwise show based on active view
    switch (activeView) {
      case "dashboard":
        return <PortfolioPulse onViewChange={handleViewChange} />;
      case "accounts":
        return <PortfolioPulse onViewChange={handleViewChange} />;
      case "analytics":
        return <AnalyticsView />;
      case "settings":
        return <SettingsView />;
      case "strategy-params":
        return <StrategyParamsView />;
      case "risk-params":
        return <RiskParamsView />;
      case "collection-params":
        return <CollectionParamsView />;
      case "notification-config":
        return <NotificationConfigView />;
      default:
        return <PortfolioPulse onViewChange={handleViewChange} />;
    }
  };

  // Determine the key for animations
  const stageKey = activeView === 'china-futures'
    ? 'view-china-futures'
    : activeView === 'china-a-stock'
    ? 'view-china-a-stock'
    : activeView === 'strategy-china-futures'
    ? 'view-strategy-china-futures'
    : activeView === 'strategy-china-a-stock'
    ? 'view-strategy-china-a-stock'
    : activeView === 'data-collection'
    ? 'view-data-collection'
    : activeView === 'api-quota'
    ? 'view-api-quota'
    : activeView === 'storage'
    ? 'view-storage'
    : activeView === 'risk-monitor'
    ? 'view-risk-monitor'
    : activeView === 'alert-records'
    ? 'view-alert-records'
    : activeView === 'compliance-report'
    ? 'view-compliance-report'
    : activeView === 'process-monitor'
    ? 'view-process-monitor'
    : activeView === 'log-records'
    ? 'view-log-records'
    : activeView === 'collection-params'
    ? 'view-collection-params'
    : activeView === 'notification-config'
    ? 'view-notification-config'
    : selectedAccount
      ? `account-${selectedAccount.id}`
      : `view-${activeView}`;

  // Get title for top bar - 所有页面内部都有自己的标题，顶栏不再显示重复标题
  const getTitle = () => {
    if (selectedAccount) return selectedAccount.name;
    // 所有其他页面都返回空字符串，避免与页面内部标题重复
    return "";
  };

  return (
    <div className="h-screen w-screen flex overflow-hidden bg-background">
      {/* Command Dock (Left Navigation) */}
      <CommandDock 
        activeView={activeView} 
        onViewChange={handleViewChange}
        onAIChatOpen={() => setShowAIChat(true)}
      />

      {/* Account List (Center-Left Panel) */}
      <AccountList
        selectedAccountId={selectedAccountId}
        onSelectAccount={handleSelectAccount}
        onNewAccount={handleNewAccount}
        onViewChange={handleViewChange}
      />

      {/* Command Stage (Main Content Area) */}
      <div className="flex-1 flex flex-col min-w-0 bg-background">
        {/* Top bar - minimal, borderless */}
        <div className="h-12 flex items-center justify-between px-6">
          <div className="flex items-center gap-2.5">
            <h2 className="text-sm font-medium text-foreground tracking-tight">{getTitle()}</h2>
            {selectedAccount && (
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-primary/8 text-primary font-medium">
                {selectedAccount.tier}
              </span>
            )}
          </div>

          {/* Right side actions */}
          <div className="flex items-center gap-2">
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {/* Command-K Search */}
            <CommandKMenu
              onSelectView={handleViewChange}
              onSelectAccount={handleSelectAccount}
              onCreateAccount={handleNewAccount}
            />
          </div>
        </div>

        {/* Stage Content */}
        <CommandStage viewKey={stageKey}>{renderStageContent()}</CommandStage>
      </div>

      {/* Account Modal */}
      <AccountModal
        isOpen={showAccountModal}
        onClose={() => {
          setShowAccountModal(false);
          setEditingAccount(undefined);
        }}
        account={editingAccount}
        onSuccess={handleAccountCreated}
      />

      {/* AI Chat Panel */}
      <AIChatPanel
        isOpen={showAIChat}
        onOpenChange={setShowAIChat}
      />

    </div>
  );
}

export default function OrbitApp() {
  return (
    <OrbitProvider>
      <ToastProvider>
        <OrbitAppContent />
      </ToastProvider>
    </OrbitProvider>
  );
}
