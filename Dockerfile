
# Use official Python image
FROM python:3.12

# Set working directory
WORKDIR /app

ENV PYTHONPATH=/app

# Copy requirements and put in working directory
COPY ./app/requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY ./app .

# Expose API port
EXPOSE 8000

# Start FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
