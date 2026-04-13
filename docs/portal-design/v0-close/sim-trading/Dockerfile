FROM node:20-alpine AS deps
WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN npm install -g pnpm && pnpm config set registry https://registry.npmmirror.com && pnpm install --frozen-lockfile

FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG BACKEND_BASE_URL=http://sim-trading:8101
ENV BACKEND_BASE_URL=${BACKEND_BASE_URL}
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm install -g pnpm && pnpm build

FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV HOSTNAME=0.0.0.0
ENV PORT=3002

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.mjs ./next.config.mjs
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3002

CMD ["node_modules/.bin/next", "start", "-p", "3002", "-H", "0.0.0.0"]
