FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-alpine AS deps
WORKDIR /app

COPY package.json ./
RUN npm config set registry https://registry.npmmirror.com \
    && npm install --no-audit --no-fund

FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG BACKEND_BASE_URL=http://decision:8104
ENV BACKEND_BASE_URL=${BACKEND_BASE_URL}
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ENV PORT=3003
ENV BACKEND_BASE_URL=http://decision:8104

COPY --from=builder /app/public ./public 2>/dev/null || true
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.mjs ./next.config.mjs
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3003

CMD ["node_modules/.bin/next", "start", "-p", "3003", "-H", "0.0.0.0"]
