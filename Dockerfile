# Use the official Python 3.12 image as a base image
FROM python:3.12-slim

# Set the working directory in the Docker container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY TARS/requirements.txt .

# Install any dependencies in the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the dir
COPY TARS .

# Expose the Streamlit port
EXPOSE 8501

# Command to run your application
CMD ["python", "main.py"]