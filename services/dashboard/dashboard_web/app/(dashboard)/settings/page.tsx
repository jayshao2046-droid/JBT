'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { settingsApi, type SystemSettings } from '@/lib/api/settings';

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await settingsApi.getSettings();
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAccountSave = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      await settingsApi.updateAccount(settings.account);
      alert('账户设置已保存');
    } catch (error) {
      console.error('Failed to save account:', error);
      alert('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleTradingToggle = async (field: keyof NonNullable<typeof settings>['trading'], value: boolean) => {
    if (!settings) return;
    try {
      await settingsApi.updateTrading({ [field]: value });
      setSettings({
        ...settings,
        trading: { ...settings.trading, [field]: value },
      });
    } catch (error) {
      console.error('Failed to update trading settings:', error);
      alert('更新失败');
    }
  };

  const handleNotificationSave = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      await settingsApi.updateNotifications(settings.notifications);
      alert('通知配置已保存');
    } catch (error) {
      console.error('Failed to save notifications:', error);
      alert('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleServiceRestart = async (serviceName: string) => {
    try {
      await settingsApi.restartService(serviceName);
      alert(`${serviceName} 重启请求已发送`);
    } catch (error) {
      console.error('Failed to restart service:', error);
      alert('重启失败');
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <p className="text-muted-foreground">加载中...</p>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="p-6 flex items-center justify-center">
        <p className="text-destructive">加载设置失败</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">系统设置</h1>
        <p className="text-muted-foreground mt-2">配置交易平台参数</p>
      </div>

      <Tabs defaultValue="account" className="w-full">
        <TabsList className="bg-muted">
          <TabsTrigger value="account">账户设置</TabsTrigger>
          <TabsTrigger value="trading">交易时段</TabsTrigger>
          <TabsTrigger value="notifications">通知配置</TabsTrigger>
          <TabsTrigger value="services">服务管理</TabsTrigger>
        </TabsList>

        <TabsContent value="account" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground">账户信息</CardTitle>
              <CardDescription className="text-muted-foreground">管理您的账户信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-foreground">用户名</Label>
                <Input
                  id="username"
                  value={settings.account.username}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      account: { ...settings.account, username: e.target.value },
                    })
                  }
                  className="bg-background border-input text-foreground"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email" className="text-foreground">邮箱</Label>
                <Input
                  id="email"
                  type="email"
                  value={settings.account.email}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      account: { ...settings.account, email: e.target.value },
                    })
                  }
                  className="bg-background border-input text-foreground"
                />
              </div>
              <Button onClick={handleAccountSave} disabled={saving}>
                {saving ? '保存中...' : '保存更改'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trading" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground">交易时段控制</CardTitle>
              <CardDescription className="text-muted-foreground">配置交易时段和自动开关</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-foreground">启用自动交易</Label>
                  <p className="text-sm text-muted-foreground">在交易时段自动启动交易</p>
                </div>
                <Switch
                  checked={settings.trading.auto_trading_enabled}
                  onCheckedChange={(checked) => handleTradingToggle('auto_trading_enabled', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-foreground">盘前准备</Label>
                  <p className="text-sm text-muted-foreground">开盘前30分钟启动系统</p>
                </div>
                <Switch
                  checked={settings.trading.pre_market_enabled}
                  onCheckedChange={(checked) => handleTradingToggle('pre_market_enabled', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-foreground">盘后清算</Label>
                  <p className="text-sm text-muted-foreground">收盘后自动执行清算</p>
                </div>
                <Switch
                  checked={settings.trading.post_market_enabled}
                  onCheckedChange={(checked) => handleTradingToggle('post_market_enabled', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground">通知配置</CardTitle>
              <CardDescription className="text-muted-foreground">配置飞书和邮件通知</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="feishu-webhook" className="text-foreground">飞书 Webhook</Label>
                <Input
                  id="feishu-webhook"
                  value={settings.notifications.feishu_webhook}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, feishu_webhook: e.target.value },
                    })
                  }
                  placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
                  className="bg-background border-input text-foreground"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email-smtp" className="text-foreground">SMTP 服务器</Label>
                <Input
                  id="email-smtp"
                  value={settings.notifications.smtp_server}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, smtp_server: e.target.value },
                    })
                  }
                  placeholder="smtp.example.com"
                  className="bg-background border-input text-foreground"
                />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-foreground">启用告警通知</Label>
                <Switch
                  checked={settings.notifications.alert_enabled}
                  onCheckedChange={(checked) =>
                    setSettings({
                      ...settings,
                      notifications: { ...settings.notifications, alert_enabled: checked },
                    })
                  }
                />
              </div>
              <Button onClick={handleNotificationSave} disabled={saving}>
                {saving ? '保存中...' : '保存配置'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="services" className="space-y-4">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-foreground">服务管理</CardTitle>
              <CardDescription className="text-muted-foreground">管理各个服务的运行状态</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {settings.services.map((service) => (
                <div key={service.name} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div>
                    <p className="text-foreground font-medium">{service.name}</p>
                    <p
                      className={`text-sm ${
                        service.status === 'running'
                          ? 'text-green-400'
                          : service.status === 'stopped'
                          ? 'text-yellow-400'
                          : 'text-red-400'
                      }`}
                    >
                      {service.status === 'running' ? '运行中' : service.status === 'stopped' ? '已停止' : '错误'}
                    </p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => handleServiceRestart(service.name)}>
                    重启
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
