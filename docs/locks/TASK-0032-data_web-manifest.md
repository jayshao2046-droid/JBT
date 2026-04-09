# TASK-0032 data_web 显式文件清单

## Manifest 信息

- 任务 ID：TASK-0032
- 来源目录：`services/data/参考文件/V0 DATA  0409`
- 目标目录：`services/data/data_web`
- 生成角色：Atlas
- 生成时间：2026-04-09 20:18
- 目标文件总数：97

## 说明

1. 本清单用于后续 `jbt_lockctl.py issue` 的文件级白名单申请。
2. 清单规则：保持参考目录相对路径不变，整体映射到 `services/data/data_web/`。
3. `services/data/参考文件/V0 DATA  0409/JBT-data.txt` 为说明文件，不纳入本次导入。

## Root Config

- services/data/data_web/.gitignore
- services/data/data_web/components.json
- services/data/data_web/next-env.d.ts
- services/data/data_web/next.config.mjs
- services/data/data_web/package.json
- services/data/data_web/pnpm-lock.yaml
- services/data/data_web/postcss.config.mjs
- services/data/data_web/tailwind.config.ts
- services/data/data_web/tsconfig.json

## App Routes

- services/data/data_web/app/globals.css
- services/data/data_web/app/layout.tsx
- services/data/data_web/app/page.tsx
- services/data/data_web/app/agent-network/loading.tsx
- services/data/data_web/app/agent-network/page.tsx
- services/data/data_web/app/command-center/page.tsx
- services/data/data_web/app/intelligence/loading.tsx
- services/data/data_web/app/intelligence/page.tsx
- services/data/data_web/app/operations/page.tsx
- services/data/data_web/app/systems/page.tsx

## Styles

- services/data/data_web/styles/globals.css

## Hooks

- services/data/data_web/hooks/use-mobile.ts
- services/data/data_web/hooks/use-toast.ts

## Lib

- services/data/data_web/lib/utils.ts

## Components Pages

- services/data/data_web/components/pages/collectors-page.tsx
- services/data/data_web/components/pages/data-explorer-page.tsx
- services/data/data_web/components/pages/news-feed-page.tsx
- services/data/data_web/components/pages/overview-page.tsx
- services/data/data_web/components/pages/settings-page.tsx
- services/data/data_web/components/pages/system-monitor-page.tsx

## Components Shared

- services/data/data_web/components/theme-provider.tsx

## Components UI

- services/data/data_web/components/ui/accordion.tsx
- services/data/data_web/components/ui/alert-dialog.tsx
- services/data/data_web/components/ui/alert.tsx
- services/data/data_web/components/ui/aspect-ratio.tsx
- services/data/data_web/components/ui/avatar.tsx
- services/data/data_web/components/ui/badge.tsx
- services/data/data_web/components/ui/breadcrumb.tsx
- services/data/data_web/components/ui/button-group.tsx
- services/data/data_web/components/ui/button.tsx
- services/data/data_web/components/ui/calendar.tsx
- services/data/data_web/components/ui/card.tsx
- services/data/data_web/components/ui/carousel.tsx
- services/data/data_web/components/ui/chart.tsx
- services/data/data_web/components/ui/checkbox.tsx
- services/data/data_web/components/ui/collapsible.tsx
- services/data/data_web/components/ui/command.tsx
- services/data/data_web/components/ui/context-menu.tsx
- services/data/data_web/components/ui/dialog.tsx
- services/data/data_web/components/ui/drawer.tsx
- services/data/data_web/components/ui/dropdown-menu.tsx
- services/data/data_web/components/ui/empty.tsx
- services/data/data_web/components/ui/field.tsx
- services/data/data_web/components/ui/form.tsx
- services/data/data_web/components/ui/hover-card.tsx
- services/data/data_web/components/ui/input-group.tsx
- services/data/data_web/components/ui/input-otp.tsx
- services/data/data_web/components/ui/input.tsx
- services/data/data_web/components/ui/item.tsx
- services/data/data_web/components/ui/kbd.tsx
- services/data/data_web/components/ui/label.tsx
- services/data/data_web/components/ui/menubar.tsx
- services/data/data_web/components/ui/navigation-menu.tsx
- services/data/data_web/components/ui/pagination.tsx
- services/data/data_web/components/ui/popover.tsx
- services/data/data_web/components/ui/progress.tsx
- services/data/data_web/components/ui/radio-group.tsx
- services/data/data_web/components/ui/resizable.tsx
- services/data/data_web/components/ui/scroll-area.tsx
- services/data/data_web/components/ui/select.tsx
- services/data/data_web/components/ui/separator.tsx
- services/data/data_web/components/ui/sheet.tsx
- services/data/data_web/components/ui/sidebar.tsx
- services/data/data_web/components/ui/skeleton.tsx
- services/data/data_web/components/ui/slider.tsx
- services/data/data_web/components/ui/sonner.tsx
- services/data/data_web/components/ui/spinner.tsx
- services/data/data_web/components/ui/switch.tsx
- services/data/data_web/components/ui/table.tsx
- services/data/data_web/components/ui/tabs.tsx
- services/data/data_web/components/ui/textarea.tsx
- services/data/data_web/components/ui/toast.tsx
- services/data/data_web/components/ui/toaster.tsx
- services/data/data_web/components/ui/toggle-group.tsx
- services/data/data_web/components/ui/toggle.tsx
- services/data/data_web/components/ui/tooltip.tsx
- services/data/data_web/components/ui/use-mobile.tsx
- services/data/data_web/components/ui/use-toast.ts

## Public Assets

- services/data/data_web/public/apple-icon.png
- services/data/data_web/public/icon-dark-32x32.png
- services/data/data_web/public/icon-light-32x32.png
- services/data/data_web/public/icon.svg
- services/data/data_web/public/images/jbotquant-logo.png
- services/data/data_web/public/placeholder-logo.png
- services/data/data_web/public/placeholder-logo.svg
- services/data/data_web/public/placeholder-user.jpg
- services/data/data_web/public/placeholder.jpg
- services/data/data_web/public/placeholder.svg