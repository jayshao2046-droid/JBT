'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { settingsApi, type SystemSettings } from '@/lib/api/settings';
import { usersApi, type User } from '@/lib/api/auth';
import { useAuth } from '@/lib/auth-context';
import { PermissionsDialog } from '@/components/settings/permissions-dialog';
import { TradingSessionsCard } from '@/components/settings/trading-sessions-card';
import { TradingCalendarCard } from '@/components/settings/trading-calendar-card';
import {
  Trash2,
  UserPlus,
  Key,
  ShieldCheck,
  User as UserIcon,
  LogOut,
  RefreshCw,
  Eye,
  EyeOff,
  Users,
  Shield,
} from 'lucide-react';

// ── 子组件：添加用户弹窗 ───────────────────────────────────
function AddUserDialog({
  open,
  onOpenChange,
  onSuccess,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onSuccess: (user: User) => void;
}) {
  const [form, setForm] = useState({ username: '', password: '', confirmPassword: '', role: 'user' });
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleClose = () => {
    setForm({ username: '', password: '', confirmPassword: '', role: 'user' });
    setError('');
    onOpenChange(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!form.username.trim()) { setError('请输入用户名'); return; }
    if (form.password.length < 6) { setError('密码不能少于6位'); return; }
    if (form.password !== form.confirmPassword) { setError('两次密码不一致'); return; }
    setLoading(true);
    try {
      const newUser = await usersApi.create({ username: form.username.trim(), password: form.password, role: form.role });
      onSuccess(newUser);
      handleClose();
    } catch (err: unknown) {
      setError((err as { message?: string }).message || '创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-orange-500" />
            添加用户
          </DialogTitle>
          <DialogDescription>
            添加后，用户即可使用该账号登录看板系统
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <div className="space-y-2">
            <Label htmlFor="add-username">用户名</Label>
            <Input
              id="add-username"
              placeholder="输入用户名（字母、数字、下划线）"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              autoComplete="off"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="add-password">密码</Label>
            <div className="relative">
              <Input
                id="add-password"
                type={showPwd ? 'text' : 'password'}
                placeholder="至少6位"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                autoComplete="new-password"
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="add-confirm-password">确认密码</Label>
            <Input
              id="add-confirm-password"
              type="password"
              placeholder="再次输入密码"
              value={form.confirmPassword}
              onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
              autoComplete="new-password"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="add-role">角色</Label>
            <select
              id="add-role"
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="w-full h-10 rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground"
            >
              <option value="user">普通用户（只读查看）</option>
              <option value="admin">管理员（完整权限）</option>
            </select>
          </div>
          {error && (
            <div className="rounded-md bg-destructive/10 border border-destructive/30 px-3 py-2">
              <p className="text-destructive text-sm">{error}</p>
            </div>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>取消</Button>
            <Button type="submit" disabled={loading}>
              {loading ? '创建中...' : '创建用户'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── 子组件：修改密码弹窗 ───────────────────────────────────
function ChangePasswordDialog({
  open,
  onOpenChange,
  targetUser,
  isSelf,
  isAdmin,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  targetUser: User | null;
  isSelf: boolean;
  isAdmin: boolean;
}) {
  const [form, setForm] = useState({ oldPassword: '', newPassword: '', confirmPassword: '' });
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleClose = () => {
    setForm({ oldPassword: '', newPassword: '', confirmPassword: '' });
    setError('');
    onOpenChange(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.newPassword.length < 6) { setError('新密码不能少于6位'); return; }
    if (form.newPassword !== form.confirmPassword) { setError('两次密码不一致'); return; }
    if (!targetUser) return;
    setLoading(true);
    try {
      await usersApi.changePassword(targetUser.id, {
        old_password: (isSelf && !isAdmin) ? form.oldPassword : undefined,
        new_password: form.newPassword,
      });
      handleClose();
      alert('密码修改成功');
    } catch (err: unknown) {
      setError((err as { message?: string }).message || '修改失败');
    } finally {
      setLoading(false);
    }
  };

  const needOldPwd = isSelf && !isAdmin;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Key className="w-5 h-5 text-orange-500" />
            修改密码
          </DialogTitle>
          <DialogDescription>
            {targetUser ? `为用户「${targetUser.username}」修改密码` : '修改密码'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          {needOldPwd && (
            <div className="space-y-2">
              <Label htmlFor="old-pwd">当前密码</Label>
              <Input
                id="old-pwd"
                type="password"
                placeholder="输入当前密码"
                value={form.oldPassword}
                onChange={(e) => setForm({ ...form, oldPassword: e.target.value })}
                autoComplete="current-password"
              />
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="new-pwd">新密码</Label>
            <div className="relative">
              <Input
                id="new-pwd"
                type={showPwd ? 'text' : 'password'}
                placeholder="至少6位"
                value={form.newPassword}
                onChange={(e) => setForm({ ...form, newPassword: e.target.value })}
                autoComplete="new-password"
                className="pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPwd(!showPwd)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm-pwd">确认新密码</Label>
            <Input
              id="confirm-pwd"
              type="password"
              placeholder="再次输入新密码"
              value={form.confirmPassword}
              onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
              autoComplete="new-password"
            />
          </div>
          {error && (
            <div className="rounded-md bg-destructive/10 border border-destructive/30 px-3 py-2">
              <p className="text-destructive text-sm">{error}</p>
            </div>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={handleClose}>取消</Button>
            <Button type="submit" disabled={loading}>
              {loading ? '修改中...' : '确认修改'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── 子组件：删除确认弹窗 ───────────────────────────────────
function DeleteUserDialog({
  open,
  onOpenChange,
  targetUser,
  onConfirm,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  targetUser: User | null;
  onConfirm: () => Promise<void>;
}) {
  const [loading, setLoading] = useState(false);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-destructive">删除用户</DialogTitle>
          <DialogDescription>
            确定要删除用户「<strong>{targetUser?.username}</strong>」吗？
            此操作不可撤销，该用户的所有会话将立即失效。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>取消</Button>
          <Button variant="destructive" onClick={handleConfirm} disabled={loading}>
            {loading ? '删除中...' : '确认删除'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── 主页面 ───────────────────────────────────────────────
export default function SettingsPage() {
  const { user: currentUser, isAdmin, logout } = useAuth();
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [users, setUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);

  const [showAddUser, setShowAddUser] = useState(false);
  const [changePwdTarget, setChangePwdTarget] = useState<User | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const [permissionsTarget, setPermissionsTarget] = useState<User | null>(null);

  const loadUsers = useCallback(async () => {
    if (!isAdmin) return;
    setUsersLoading(true);
    try {
      const data = await usersApi.list();
      setUsers(data);
    } catch (err) {
      console.error('Failed to load users:', err);
    } finally {
      setUsersLoading(false);
    }
  }, [isAdmin]);

  const loadSettings = useCallback(async () => {
    try {
      const data = await settingsApi.getSettings();
      setSettings(data);
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
    loadUsers();
  }, [loadSettings, loadUsers]);

  const handleTradingToggle = async (key: string, value: boolean) => {
    if (!settings) return;
    setSettings({ ...settings, trading: { ...settings.trading, [key]: value } });
  };

  const handleNotificationSave = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      await settingsApi.updateNotifications(settings.notifications);
      alert('通知配置已保存');
    } catch (err) {
      console.error('Failed to save notifications:', err);
      alert('保存失败');
    } finally {
      setSaving(false);
    }
  };

  const handleServiceRestart = async (serviceName: string) => {
    try {
      await settingsApi.restartService(serviceName);
      alert(`${serviceName} 重启请求已发送`);
    } catch {
      alert('重启失败');
    }
  };

  const handleDeleteUser = async () => {
    if (!deleteTarget) return;
    await usersApi.delete(deleteTarget.id);
    await loadUsers();
  };

  const handlePermissionsSave = async (userId: number, permissions: string[]) => {
    await usersApi.updatePermissions(userId, permissions);
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, permissions } : u));
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[200px]">
        <p className="text-muted-foreground">加载中...</p>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="p-6 flex items-center justify-center">
        <p className="text-destructive">加载设置失败，请刷新重试</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-transparent">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">系统设置</h1>
          <p className="text-muted-foreground mt-1">配置交易平台参数</p>
        </div>
        {currentUser && (
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-foreground">{currentUser.username}</p>
              <p className="text-xs text-muted-foreground">{isAdmin ? '管理员' : '普通用户'}</p>
            </div>
            <Button variant="outline" size="sm" onClick={logout} className="gap-2">
              <LogOut className="w-4 h-4" />
              <span className="hidden sm:inline">退出登录</span>
            </Button>
          </div>
        )}
      </div>

      <Tabs defaultValue="account" className="w-full">
        <TabsList className="bg-transparent backdrop-blur-sm">
          <TabsTrigger value="account">账户设置</TabsTrigger>
          <TabsTrigger value="trading">交易时段</TabsTrigger>
          <TabsTrigger value="notifications">通知配置</TabsTrigger>
          <TabsTrigger value="services">服务管理</TabsTrigger>
        </TabsList>

        {/* 账户设置 Tab */}
        <TabsContent value="account" className="space-y-4">
          <Card className="bg-transparent backdrop-blur-sm border-border">
            <CardHeader>
              <CardTitle className="text-foreground flex items-center gap-2">
                <UserIcon className="w-5 h-5 text-orange-500" />
                个人信息
              </CardTitle>
              <CardDescription className="text-muted-foreground">您的账户基本信息</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/30 border border-border">
                <div className="w-12 h-12 rounded-full bg-orange-500/10 flex items-center justify-center">
                  <UserIcon className="w-6 h-6 text-orange-500" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-foreground">{currentUser?.username}</p>
                    <Badge variant={isAdmin ? 'default' : 'secondary'} className="text-xs">
                      {isAdmin ? (
                        <span className="flex items-center gap-1">
                          <ShieldCheck className="w-3 h-3" /> 管理员
                        </span>
                      ) : '普通用户'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mt-0.5">
                    账户 ID: #{currentUser?.id} · 创建于 {currentUser?.created_at ? new Date(currentUser.created_at).toLocaleDateString('zh-CN') : '-'}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-2"
                  onClick={() => currentUser && setChangePwdTarget({ ...currentUser, role: currentUser.role, permissions: [] })}
                >
                  <Key className="w-4 h-4" />
                  修改密码
                </Button>
              </div>
            </CardContent>
          </Card>

          {isAdmin && (
            <Card className="bg-transparent backdrop-blur-sm border-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-foreground flex items-center gap-2">
                      <Users className="w-5 h-5 text-orange-500" />
                      用户管理
                    </CardTitle>
                    <CardDescription className="text-muted-foreground">
                      管理系统用户账户，只有管理员添加的账号才能登录看板
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={loadUsers}
                      disabled={usersLoading}
                      title="刷新列表"
                    >
                      <RefreshCw className={`w-4 h-4 ${usersLoading ? 'animate-spin' : ''}`} />
                    </Button>
                    <Button onClick={() => setShowAddUser(true)} size="sm" className="gap-2">
                      <UserPlus className="w-4 h-4" />
                      添加用户
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {usersLoading ? (
                  <div className="text-center py-8 text-muted-foreground text-sm">加载中...</div>
                ) : users.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground text-sm">暂无用户数据</div>
                ) : (
                  <div className="space-y-2">
                    {users.map((user) => (
                      <div
                        key={user.id}
                        className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/20 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-muted flex items-center justify-center">
                            {user.role === 'admin' ? (
                              <ShieldCheck className="w-4 h-4 text-orange-500" />
                            ) : (
                              <UserIcon className="w-4 h-4 text-muted-foreground" />
                            )}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="text-foreground font-medium text-sm">{user.username}</p>
                              {user.id === currentUser?.id && (
                                <Badge variant="outline" className="text-xs">我</Badge>
                              )}
                              <Badge
                                variant={user.role === 'admin' ? 'default' : 'secondary'}
                                className="text-xs"
                              >
                                {user.role === 'admin' ? '管理员' : '普通用户'}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">
                              创建于 {new Date(user.created_at).toLocaleDateString('zh-CN')}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="gap-1 text-muted-foreground hover:text-foreground"
                            onClick={() => setPermissionsTarget(user)}
                          >
                            <Shield className="w-3.5 h-3.5" />
                            <span className="hidden sm:inline">权限</span>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="gap-1 text-muted-foreground hover:text-foreground"
                            onClick={() => setChangePwdTarget(user)}
                          >
                            <Key className="w-3.5 h-3.5" />
                            <span className="hidden sm:inline">改密码</span>
                          </Button>
                          {user.id !== currentUser?.id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-destructive hover:text-destructive hover:bg-destructive/10"
                              onClick={() => setDeleteTarget(user)}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-orange-500" />
                    系统中共 {users.length} 个用户，{users.filter(u => u.role === 'admin').length} 个管理员
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* 交易时段 Tab */}
        <TabsContent value="trading" className="space-y-4">
          <TradingSessionsCard />
          <TradingCalendarCard />
        </TabsContent>

        {/* 通知配置 Tab */}
        <TabsContent value="notifications" className="space-y-4">
          <Card className="bg-transparent backdrop-blur-sm border-border">
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

        {/* 服务管理 Tab */}
        <TabsContent value="services" className="space-y-4">
          <Card className="bg-transparent backdrop-blur-sm border-border">
            <CardHeader>
              <CardTitle className="text-foreground">服务管理</CardTitle>
              <CardDescription className="text-muted-foreground">管理各个服务的运行状态</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {settings.services.map((service) => (
                <div key={service.name} className="flex items-center justify-between p-3 rounded-lg border border-border">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        service.status === 'running'
                          ? 'bg-green-500'
                          : service.status === 'stopped'
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                    />
                    <div>
                      <p className="text-foreground font-medium text-sm">{service.name}</p>
                      <p
                        className={`text-xs ${
                          service.status === 'running'
                            ? 'text-green-500'
                            : service.status === 'stopped'
                            ? 'text-yellow-500'
                            : 'text-red-500'
                        }`}
                      >
                        {service.status === 'running' ? '运行中' : service.status === 'stopped' ? '已停止' : '错误'}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleServiceRestart(service.name)}
                    className="gap-2"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    重启
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 弹窗 */}
      <AddUserDialog
        open={showAddUser}
        onOpenChange={setShowAddUser}
        onSuccess={(newUser) => {
          loadUsers();
          setPermissionsTarget(newUser);
        }}
      />

      <ChangePasswordDialog
        open={!!changePwdTarget}
        onOpenChange={(v) => { if (!v) setChangePwdTarget(null); }}
        targetUser={changePwdTarget}
        isSelf={changePwdTarget?.id === currentUser?.id}
        isAdmin={isAdmin}
      />

      <DeleteUserDialog
        open={!!deleteTarget}
        onOpenChange={(v) => { if (!v) setDeleteTarget(null); }}
        targetUser={deleteTarget}
        onConfirm={handleDeleteUser}
      />
      <PermissionsDialog
        open={!!permissionsTarget}
        onOpenChange={(open) => !open && setPermissionsTarget(null)}
        user={permissionsTarget}
        onSave={handlePermissionsSave}
      />
    </div>
  );
}
