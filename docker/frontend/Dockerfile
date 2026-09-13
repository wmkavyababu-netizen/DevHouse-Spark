# Build stage for TARANG React frontend
FROM node:20-alpine AS dev

WORKDIR /app

# Copy package descriptors
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY frontend/ ./

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
