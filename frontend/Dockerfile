# Use an official Node.js runtime as a parent image
FROM node:20-alpine

# Install curl for healthcheck
RUN apk add --no-cache curl

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to the container
COPY package*.json ./

# Install project dependencies
RUN npm install

# Copy the rest of the application code to the container
COPY . .

# The command to run the application (Vite dev server)
CMD ["npm", "run", "dev"]
