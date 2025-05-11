# Use an official Python 3.10 runtime as the base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app

# Install the necessary dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the Streamlit app code into the container
COPY app.py /app

# Expose the port that Streamlit will run on
EXPOSE 8501

# Run Streamlit when the container starts
CMD ["streamlit", "run", "app.py"]