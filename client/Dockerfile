# Stage 1: Build the application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* .npmrc ./
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Create the production image
FROM node:20-alpine AS production

WORKDIR /app

# Copy built assets from the builder stage
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./package.json

# Install production dependencies
RUN npm ci --omit=dev

# Expose the port the app will run on
EXPOSE 3000

# The command to run the application
# SvelteKit with adapter-node outputs a server to `build/index.js`
CMD ["node", "build/index.js"]
