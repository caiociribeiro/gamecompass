FROM node:24-slim

WORKDIR /app

# Dependências primeiro: a camada só é refeita quando o package-lock.json muda.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
# O build faz a checagem de tipos e gera a pasta dist.
RUN npm run build

# O vite preview serve o build e repassa /api para a API, com a mesma regra de proxy do
# npm run dev (veja vite.config.ts). Dentro do Compose a API responde em api:8000.
ENV API_PROXY_TARGET=http://api:8000

EXPOSE 5173

CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]
