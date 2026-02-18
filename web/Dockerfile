FROM node:20-alpine AS build
WORKDIR /app
COPY package.json /app/package.json
COPY vite.config.js /app/vite.config.js
COPY index.html /app/index.html
COPY src /app/src
RUN npm install --legacy-peer-deps
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
