# Use Python 3.10 official image as the base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/requirements.txt

# Install dependencies from the requirements file
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the backend app code into the container
COPY . /app

# Expose the port that the backend API will run on (adjust if necessary)
EXPOSE 8000

# Install Uvicorn if it's not in your requirements.txt
RUN pip install uvicorn

# Run the backend app using Uvicorn when the container starts
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]