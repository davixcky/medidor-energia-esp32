# Imagen del servidor de la plataforma (Railway, Render o cualquier host de contenedores).
# Contexto de construcción: esta carpeta (plataforma/).
FROM node:22-alpine AS construccion
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@10.33.0 --activate
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

# .output trae el servidor y las dependencias que usa; no hace falta node_modules.
FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production HOST=0.0.0.0 PORT=3000 NODE_OPTIONS=--max-old-space-size=192
COPY --from=construccion /app/.output ./.output
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
