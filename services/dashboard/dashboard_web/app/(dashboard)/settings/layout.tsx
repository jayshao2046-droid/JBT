import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '系统设置 - JBT Dashboard',
  description: '配置交易平台参数和服务管理',
};

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-950">
      {children}
    </div>
  );
}
