# Use the official Python 3.12 image as a base image
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set the working directory in the Docker container
WORKDIR /app

# Copy the project files
COPY pyproject.toml .
COPY uv.lock* .

# Install dependencies using uv
RUN uv sync --frozen

# Copy the application code
COPY TARS .

# Expose the Streamlit and FastAPI ports
EXPOSE 8501
EXPOSE 8000

# Command to run your application
CMD ["uv", "run", "python", "main.py"]