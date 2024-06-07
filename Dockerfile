# Use the official Python 3.10 image as a base image for production deployment
FROM python:3.10-slim

# Set the working directory in the Docker container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY TARS/requirements.txt .

# Install any dependencies in the requirements file
# This step is crucial for ensuring that all necessary Python packages are available in the container
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application directory into the container
# This includes all necessary files for running the application
COPY TARS .

# Command to run the application
# This is the final step that starts the application within the container
CMD ["python", "main.py"]
