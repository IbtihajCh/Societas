FROM node:26-alpine AS builder

WORKDIR /build

COPY frontend/package*.json .
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM node:26-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /build/.next ./.next
COPY --from=builder /build/public ./public
COPY --from=builder /build/package*.json .
COPY --from=builder /build/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "start"]
