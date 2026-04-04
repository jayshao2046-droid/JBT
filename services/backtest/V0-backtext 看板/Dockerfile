# ────────────────────────────────────────────────
# JBT 回测看板 — Next.js 生产 Docker 镜像
# 端口: 3001
# 运行时不需要 TqSdk 凭证
# 注意: 构建上下文须设置为 services/backtest/V0-backtext 看板/
# ────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# 启用 pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm run build

# ── 生产运行层 ──────────────────────────────────
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3001
ENV HOSTNAME=0.0.0.0

# 最小权限用户
RUN addgroup --system --gid 1001 nextjs && \
    adduser --system --uid 1001 nextjs

# pnpm（生产运行需要 next start）
RUN corepack enable && corepack prepare pnpm@latest --activate

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/pnpm-lock.yaml ./pnpm-lock.yaml
RUN pnpm install --frozen-lockfile --prod

COPY --from=builder --chown=nextjs:nextjs /app/.next ./.next
COPY --from=builder --chown=nextjs:nextjs /app/public ./public

USER nextjs

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -qO- http://localhost:3001/ || exit 1

CMD ["pnpm", "run", "start"]
