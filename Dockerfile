# Use the official Python 3.10 image as a base image
FROM python:3.10

# Set the working directory in the Docker container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any dependencies in the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application's code into the container at /app
COPY TARS/ .

# Command to run on container start. Adjust the file name as necessary
CMD ["python", "./main.py"]