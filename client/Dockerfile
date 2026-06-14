FROM node:26-alpine3.23 AS generator

WORKDIR /app

COPY package*.json .

RUN npm install
COPY . .

RUN npm run generate

FROM nginx:latest
COPY --from=generator /app/dist /usr/share/nginx/html