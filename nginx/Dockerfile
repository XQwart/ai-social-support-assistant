FROM node:24-alpine AS frontend-builder

WORKDIR /code

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx/conf.d/prod.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-builder /code/dist /usr/share/nginx/html