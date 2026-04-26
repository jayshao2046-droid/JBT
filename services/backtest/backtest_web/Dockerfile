FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-alpine AS deps
WORKDIR /app

COPY package.json ./
RUN npm config set registry https://registry.npmmirror.com \
	&& npm install --no-audit --no-fund

FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG BACKEND_BASE_URL=http://backtest-api:8103
ENV BACKEND_BASE_URL=${BACKEND_BASE_URL}
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ENV PORT=3001
ENV BACKEND_BASE_URL=http://backtest-api:8103

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.mjs ./next.config.mjs
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3001

CMD ["node_modules/.bin/next", "start", "-p", "3001", "-H", "0.0.0.0"]