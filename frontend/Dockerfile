# STAGE 1: Build the React application
FROM node:20-slim AS build

# Set working directory
WORKDIR /app

# Copy package.json and install dependencies (caching step)
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy the rest of the frontend code and build it
COPY . .
RUN npm run build

# STAGE 2: Serve with Nginx
FROM nginx:alpine

# Copy the custom Nginx config — enables API proxying to the backend container
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the compiled React files from the build stage to Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80 for the web server
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]