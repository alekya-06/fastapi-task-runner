# Use official Python image
FROM python:3.12

# Set working directory
WORKDIR /app

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Explicitly install beautifulsoup4 to ensure it's there
RUN pip install beautifulsoup4

# Set entry point
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
