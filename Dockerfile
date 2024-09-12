# Use the official Node.js 14 image as a base image
FROM node:14-slim

# Set the working directory in the Docker container
WORKDIR /app

# Copy the package.json and package-lock.json files into the container at /app
COPY package.json package-lock.json ./

# Install any dependencies in the package.json file
RUN npm install

# Copy the rest of the application files to the container
COPY . .

# Command to run your application
CMD ["node", "main.js"]
