FROM python:3.11-slim

WORKDIR /app

# Install CPU-only PyTorch FIRST from the CPU wheel index
RUN pip install --no-cache-dir torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu

# Install numpy before other deps to avoid version conflicts
RUN pip install --no-cache-dir numpy==1.26.4

# Copy and install other requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
