import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import MainLayout from '@/components/layout/main-layout';

export default function SettingsPage() {
  return (
    <MainLayout title="系统设置">
      <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">系统设置</h1>
        <p className="text-gray-400 mt-2">配置交易平台参数</p>
      </div>

      <Tabs defaultValue="account" className="w-full">
        <TabsList className="bg-gray-900">
          <TabsTrigger value="account">账户设置</TabsTrigger>
          <TabsTrigger value="trading">交易时段</TabsTrigger>
          <TabsTrigger value="notifications">通知配置</TabsTrigger>
          <TabsTrigger value="services">服务管理</TabsTrigger>
        </TabsList>

        <TabsContent value="account" className="space-y-4">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">账户信息</CardTitle>
              <CardDescription className="text-gray-400">管理您的账户信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-gray-300">用户名</Label>
                <Input id="username" defaultValue="admin" className="bg-gray-800 border-gray-700 text-white" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email" className="text-gray-300">邮箱</Label>
                <Input id="email" type="email" defaultValue="admin@jbt.com" className="bg-gray-800 border-gray-700 text-white" />
              </div>
              <Button>保存更改</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trading" className="space-y-4">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">交易时段控制</CardTitle>
              <CardDescription className="text-gray-400">配置交易时段和自动开关</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-gray-300">启用自动交易</Label>
                  <p className="text-sm text-gray-500">在交易时段自动启动交易</p>
                </div>
                <Switch />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-gray-300">盘前准备</Label>
                  <p className="text-sm text-gray-500">开盘前30分钟启动系统</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-gray-300">盘后清算</Label>
                  <p className="text-sm text-gray-500">收盘后自动执行清算</p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">通知配置</CardTitle>
              <CardDescription className="text-gray-400">配置飞书和邮件通知</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="feishu-webhook" className="text-gray-300">飞书 Webhook</Label>
                <Input 
                  id="feishu-webhook" 
                  placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..." 
                  className="bg-gray-800 border-gray-700 text-white" 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email-smtp" className="text-gray-300">SMTP 服务器</Label>
                <Input 
                  id="email-smtp" 
                  placeholder="smtp.example.com" 
                  className="bg-gray-800 border-gray-700 text-white" 
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-gray-300">启用告警通知</Label>
                <Switch defaultChecked />
              </div>
              <Button>保存配置</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services" className="space-y-4">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-white">服务管理</CardTitle>
              <CardDescription className="text-gray-400">管理各个服务的运行状态</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {['模拟交易', '回测系统', '决策引擎', '数据服务'].map((service) => (
                <div key={service} className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                  <div>
                    <p className="text-white font-medium">{service}</p>
                    <p className="text-sm text-green-500">运行中</p>
                  </div>
                  <Button variant="outline" size="sm">重启</Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
    </MainLayout>
  );
}
