# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 3000

# Define environment variable
ENV NAME World

# SQLite database file is written to /app/orders.db by default.
# To persist data across container restarts, mount a volume at /app:
#   docker run -v /host/data:/app/data ... (then set DB_PATH accordingly)
# Override DATABASE_URL to use PostgreSQL instead of SQLite:
#   docker run -e DATABASE_URL="postgresql://user:pass@host:port/db?sslmode=require" ...
ENV DATABASE_URL=""

# Run app.py when the container launches
CMD ["python", "app.py"]
