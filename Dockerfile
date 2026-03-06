# Use the official, lightweight Python 3.11 image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Prevent Python from writing .pyc files and force output straight to the terminal (useful for logging)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy only the requirements first, to leverage Docker caching
COPY backend/requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the actual application code into the container
COPY backend/ ./backend/

# Expose the port that FastAPI runs on
EXPOSE 8000

# The command to run when the container starts
# Notice we bind to 0.0.0.0 so it can be accessed from outside the Docker container
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]