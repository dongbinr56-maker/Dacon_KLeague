FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install
RUN test -f node_modules/.bin/next || (echo "ERROR: next not found in node_modules/.bin/" && ls -la node_modules/.bin/ && exit 1)
COPY . .
CMD ["npm", "run", "dev"]
