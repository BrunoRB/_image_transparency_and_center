# front/Dockerfile
FROM node:19

WORKDIR /app

COPY package.json package-lock.json ./

ENV NODE_ENV=development

RUN npm install --include=dev

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]

