import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function LoginPage() {
  return (
    <Card className="w-full max-w-md">
      <CardHeader className="space-y-1">
        <CardTitle className="text-2xl font-bold">JBT 统一看板</CardTitle>
        <CardDescription>
          登录以访问模拟交易、回测、数据和决策看板
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="username">用户名</Label>
          <Input id="username" placeholder="请输入用户名" />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">密码</Label>
          <Input id="password" type="password" placeholder="请输入密码" />
        </div>
        <Button className="w-full">登录</Button>
        <div className="text-center text-sm text-muted-foreground">
          或使用会员码登录
        </div>
        <Input placeholder="请输入会员码" />
        <Button variant="outline" className="w-full">
          会员码登录
        </Button>
      </CardContent>
    </Card>
  );
}
