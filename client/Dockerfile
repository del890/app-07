FROM node:26-alpine3.23 AS generator

WORKDIR /app

COPY package*.json .

RUN npm install
COPY . .

RUN npm run generate

FROM nginx:latest
EXPOSE 80
# Backend service base URL for the /v1/ proxy. Overridden in production by the
# Elastic Beanstalk environment property of the same name; the default keeps the
# container booting (valid proxy_pass) when run without one.
ENV BACKEND_URL=http://localhost:5000
# Opt in to the base image deriving ${NGINX_LOCAL_RESOLVERS} from the
# container's /etc/resolv.conf, used by the runtime resolver in the /v1/ proxy.
ENV NGINX_ENTRYPOINT_LOCAL_RESOLVERS=1
# Rendered to /etc/nginx/conf.d/default.conf at startup via the base image's
# envsubst entrypoint, injecting BACKEND_URL into the /v1/ proxy_pass.
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=generator /app/dist /usr/share/nginx/html