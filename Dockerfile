FROM node:20-slim

WORKDIR /app

COPY package.json tsconfig.json ./
COPY src ./src
COPY bin ./bin

RUN npm install && npm run build

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "fetch('http://localhost:8000/health').then(r => r.ok ? process.exit(0) : process.exit(1)).catch(() => process.exit(1))" || exit 1

CMD ["node", "dist/server.js"]
