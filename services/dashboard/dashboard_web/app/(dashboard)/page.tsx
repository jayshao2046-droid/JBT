import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, TrendingUp, AlertCircle, Database } from 'lucide-react';

export default function DashboardPage() {
  const services = [
    {
      name: '模拟交易',
      icon: TrendingUp,
      status: 'running',
      description: '实时交易执行与风控监控',
      stats: { active: 12, total: 15 },
    },
    {
      name: '回测系统',
      icon: Activity,
      status: 'running',
      description: '策略回测与参数优化',
      stats: { running: 3, completed: 45 },
    },
    {
      name: '决策引擎',
      icon: AlertCircle,
      status: 'running',
      description: '信号生成与策略研究',
      stats: { signals: 8, strategies: 23 },
    },
    {
      name: '数据服务',
      icon: Database,
      status: 'running',
      description: '数据采集与质量监控',
      stats: { sources: 18, quality: '98.5%' },
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">统一看板</h1>
        <p className="text-gray-400 mt-2">JBT 交易平台总览</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {services.map((service) => {
          const Icon = service.icon;
          return (
            <Card key={service.name} className="bg-gray-900 border-gray-800">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <Icon className="h-8 w-8 text-blue-500" />
                  <span className="text-xs text-green-500">● {service.status}</span>
                </div>
                <CardTitle className="text-white">{service.name}</CardTitle>
                <CardDescription className="text-gray-400">{service.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-gray-300">
                  {Object.entries(service.stats).map(([key, value]) => (
                    <div key={key} className="flex justify-between py-1">
                      <span className="text-gray-400">{key}:</span>
                      <span className="font-medium">{value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">今日重点</CardTitle>
          <CardDescription className="text-gray-400">需要关注的事项</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-gray-300">
            <div className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              <span>3 个策略等待审核</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <span>1 个数据源连接异常</span>
            </div>
            <div className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
              <AlertCircle className="h-5 w-5 text-blue-500" />
              <span>5 个回测任务进行中</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
