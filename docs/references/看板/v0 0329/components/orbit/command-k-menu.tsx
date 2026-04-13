"use client";

import { useEffect, useState, useMemo } from "react";
import {
  LayoutDashboard,
  Users,
  BarChart3,
  Settings,
  Search,
  Building2,
  Plus,
  Activity,
  UserPlus,
  TrendingUp,
  Zap,
} from "lucide-react";
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command";
import { cn } from "@/lib/utils";
import { useOrbit } from "./orbit-provider";
import { getHealthStatus, formatCurrency, type Account } from "@/lib/mock-data";
import type { ViewType } from "./command-dock";

interface CommandKMenuProps {
  onSelectView: (view: ViewType) => void;
  onSelectAccount: (account: Account) => void;
  onCreateAccount: () => void;
}

export function CommandKMenu({
  onSelectView,
  onSelectAccount,
  onCreateAccount,
}: CommandKMenuProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const { accounts } = useOrbit();

  const activeAccounts = accounts.filter((acc) => !acc.isArchived);

  // Handle keyboard shortcut
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
      // New account shortcut
      if (e.key === "n" && (e.metaKey || e.ctrlKey) && !e.shiftKey) {
        e.preventDefault();
        onCreateAccount();
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [onCreateAccount]);

  // Filter accounts based on search
  const filteredAccounts = useMemo(() => {
    if (!search) {
      // Show most recently active accounts
      return [...activeAccounts]
        .sort((a, b) => b.lastActivity.getTime() - a.lastActivity.getTime())
        .slice(0, 5);
    }
    const query = search.toLowerCase();
    return activeAccounts.filter(
      (acc) =>
        acc.name.toLowerCase().includes(query) ||
        acc.industry.toLowerCase().includes(query) ||
        acc.tier.toLowerCase().includes(query)
    );
  }, [search, activeAccounts]);

  // At-risk accounts for quick access
  const atRiskAccounts = useMemo(() => {
    return activeAccounts
      .filter((acc) => acc.healthScore < 50)
      .sort((a, b) => a.healthScore - b.healthScore)
      .slice(0, 3);
  }, [activeAccounts]);

  const handleSelectView = (view: ViewType) => {
    onSelectView(view);
    setOpen(false);
    setSearch("");
  };

  const handleSelectAccount = (account: Account) => {
    onSelectAccount(account);
    setOpen(false);
    setSearch("");
  };

  const handleCreateAccount = () => {
    onCreateAccount();
    setOpen(false);
    setSearch("");
  };

  return (
    <>
      {/* Search trigger button */}
      <button
        onClick={() => setOpen(true)}
        className="hidden md:flex items-center gap-2 px-4 py-2 w-[280px] bg-muted/50 border border-border rounded-lg text-[13px] text-muted-foreground hover:text-foreground hover:bg-muted hover:border-border/80 transition-all"
      >
        <Search className="w-4 h-4 flex-shrink-0" />
        <span className="flex-1 text-left">搜索...</span>
        <kbd className="px-1.5 py-0.5 bg-background border border-border rounded text-[11px] font-mono flex-shrink-0">
          <span className="text-muted-foreground">Cmd</span> K
        </kbd>
      </button>

      <CommandDialog
        open={open}
        onOpenChange={setOpen}
        title="命令菜单"
        description="搜索策略或导航到不同视图"
      >
        <CommandInput
          placeholder="搜索策略、操作、导航..."
          value={search}
          onValueChange={setSearch}
        />
        <CommandList className="max-h-[450px]">
          <CommandEmpty>
            <div className="flex flex-col items-center py-6">
              <Search className="w-10 h-10 text-muted-foreground/50 mb-3" />
              <p className="text-sm font-medium text-foreground">未找到结果</p>
              <p className="text-xs text-muted-foreground mt-1">
                请尝试其他搜索词
              </p>
            </div>
          </CommandEmpty>

          {/* Quick actions */}
          <CommandGroup heading="快捷操作">
            <CommandItem onSelect={() => handleSelectView("dashboard")}>
              <LayoutDashboard className="mr-2 h-4 w-4 text-muted-foreground" />
              <span>前往首页</span>
            </CommandItem>
            <CommandItem onSelect={() => handleSelectView("accounts")}>
              <Users className="mr-2 h-4 w-4 text-muted-foreground" />
              <span>查看所有持仓</span>
            </CommandItem>
          </CommandGroup>

          {/* At-risk accounts - show only when not searching */}
          {!search && atRiskAccounts.length > 0 && (
            <>
              <CommandSeparator />
              <CommandGroup heading="需要关注">
                {atRiskAccounts.map((account) => (
                  <CommandItem
                    key={account.id}
                    value={`at-risk-${account.name}`}
                    onSelect={() => handleSelectAccount(account)}
                  >
                    <div className="flex items-center gap-3 w-full">
                      <div
                        className={cn(
                          "w-2 h-2 rounded-full shrink-0",
                          account.healthScore < 30 ? "bg-destructive" : "bg-warning"
                        )}
                      />
                      <Activity className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm text-foreground">
                          {account.name}
                        </span>
                      </div>
                      <span
                        className={cn(
                          "text-xs font-mono px-2 py-0.5 rounded-full",
                          account.healthScore < 30
                            ? "badge-critical"
                            : "badge-warning"
                        )}
                      >
                        {account.healthScore}
                      </span>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            </>
          )}

          <CommandSeparator />

          {/* Accounts */}
          <CommandGroup heading={search ? "策略" : "最近策略"}>
            {filteredAccounts.map((account) => {
              const healthStatus = getHealthStatus(account.healthScore);
              return (
                <CommandItem
                  key={account.id}
                  value={`${account.name} ${account.industry} ${account.tier}`}
                  onSelect={() => handleSelectAccount(account)}
                >
                  <div className="flex items-center gap-3 w-full">
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full shrink-0",
                        healthStatus === "healthy" && "bg-success",
                        healthStatus === "neutral" && "bg-primary",
                        healthStatus === "at-risk" && "bg-warning",
                        healthStatus === "critical" && "bg-destructive"
                      )}
                    />
                    <Building2 className="h-4 w-4 text-muted-foreground shrink-0" />
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-foreground">
                        {account.name}
                      </span>
                      <span className="ml-2 text-xs text-muted-foreground">
                        {account.industry}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-muted-foreground">
                      {formatCurrency(account.arr)}
                    </span>
                  </div>
                </CommandItem>
              );
            })}
          </CommandGroup>

          {/* Show "Create" option when searching and no exact match */}
          {search && filteredAccounts.length === 0 && (
            <>
              <CommandSeparator />
              <CommandGroup heading="创建">
                <CommandItem onSelect={handleCreateAccount}>
                  <Plus className="mr-2 h-4 w-4 text-primary" />
                  <span>
                    创建新策略{" "}
                    <span className="text-primary font-medium">"{search}"</span>
                  </span>
                </CommandItem>
              </CommandGroup>
            </>
          )}
        </CommandList>
      </CommandDialog>
    </>
  );
}
