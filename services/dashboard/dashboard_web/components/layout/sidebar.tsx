'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, TrendingUp, Activity, Brain, Database, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: '总览', href: '/', icon: Home },
  { name: '模拟交易', href: '/sim-trading', icon: TrendingUp },
  { name: '回测系统', href: '/backtest', icon: Activity },
  { name: '决策引擎', href: '/decision', icon: Brain },
  { name: '数据服务', href: '/data', icon: Database },
  { name: '系统设置', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-xl font-bold text-white">JBT Platform</h1>
        <p className="text-sm text-gray-400 mt-1">统一交易平台</p>
      </div>
      
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              )}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-500">
          <p>Version 1.0.0</p>
          <p className="mt-1">© 2026 JBT</p>
        </div>
      </div>
    </aside>
  );
}
