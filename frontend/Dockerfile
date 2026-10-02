# Local/production-like image for the frontend: build the static export, serve it with nginx.
# NEXT_PUBLIC_API_URL is inlined at build time, so pass it as a build argument.

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_GITHUB_URL=
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_PUBLIC_GITHUB_URL=${NEXT_PUBLIC_GITHUB_URL} \
    NEXT_TELEMETRY_DISABLED=1
COPY . .
RUN npm run build

FROM nginx:1.29-alpine
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/out /usr/share/nginx/html
EXPOSE 3000
