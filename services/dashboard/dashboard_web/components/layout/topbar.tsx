'use client';

import { Bell, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

export function Topbar() {
  return (
    <header className="h-16 border-b border-gray-800 bg-gray-900 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <div className="text-sm">
          <span className="text-gray-400">交易日：</span>
          <span className="text-white ml-2">2026-04-13</span>
        </div>
        <div className="h-4 w-px bg-gray-700" />
        <div className="text-sm">
          <span className="text-gray-400">交易时段：</span>
          <span className="text-green-500 ml-2">● 开盘中</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" className="relative text-gray-400 hover:text-white">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 h-2 w-2 bg-red-500 rounded-full" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="gap-2 text-gray-400 hover:text-white">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-blue-600 text-white">A</AvatarFallback>
              </Avatar>
              <span>Admin</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56 bg-gray-900 border-gray-800">
            <DropdownMenuLabel className="text-gray-300">我的账户</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-gray-800" />
            <DropdownMenuItem className="text-gray-300 focus:bg-gray-800 focus:text-white">
              <User className="mr-2 h-4 w-4" />
              个人资料
            </DropdownMenuItem>
            <DropdownMenuItem className="text-gray-300 focus:bg-gray-800 focus:text-white">
              设置
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-gray-800" />
            <DropdownMenuItem className="text-red-400 focus:bg-gray-800 focus:text-red-400">
              退出登录
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
