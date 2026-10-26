FROM node:20-alpine

WORKDIR /app

# Copy package descriptors
COPY package*.json ./
RUN npm ci

# Copy application files
COPY . .

# Pass build-time environment variable
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL

# Build Next.js application
RUN npm run build

EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production

CMD ["npm", "start"]
