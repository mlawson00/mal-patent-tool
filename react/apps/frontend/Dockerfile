FROM node:16.14.0 as setup

RUN mkdir /app
COPY package.json /app
COPY nginx.conf /app

WORKDIR /app

#ENV NODE_PATH=/app/node_modules
#ENV PATH=$PATH:/app/node_modules/.bin
#RUN npm install

COPY . /app
RUN npm install

FROM setup as dev
CMD ["npm", "start"]

FROM setup as build
RUN npm run build


FROM nginx:1.19.4-alpine AS prd
COPY --from=build /app/build /usr/share/nginx/html/admin
COPY --from=setup app/nginx.conf ../../../etc/nginx/nginx.conf
## Add Bash to make life easier.
RUN apk add --no-cache bash
WORKDIR /usr/share/nginx/html
ENTRYPOINT ["nginx", "-g", "daemon off;"]
