# Use an official Python image
FROM --platform=linux/amd64 python:3.11-slim
 
# Set the working directory inside the container
WORKDIR /app
 
# Copy requirements file and install dependencies
COPY requirements.txt .
 
#RUN pip install -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu 
 
# Copy the rest of the application code
COPY . .
 
RUN pip install --no-cache-dir docling==2.16.0 --extra-index-url https://download.pytorch.org/whl/cpu
 
RUN pip install --no-cache-dir python-multipart --extra-index-url https://download.pytorch.org/whl/cpu
 
# Set environment variables
ENV PORT=8082

# Run FastAPI using Uvicorn
CMD ["uvicorn", "api.fastapi_backend:app", "--host", "0.0.0.0", "--port", "8082"]