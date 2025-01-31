# Use an official Python image
FROM python:3.11
 
# Set the working directory inside the container
WORKDIR /app
 
# Copy requirements file and install dependencies
COPY requirements.txt .
 
RUN pip install -r requirements.txt
 
# Copy the rest of the application code
COPY . .
 
RUN pip install docling==2.16.0
 
RUN pip install python-multipart
 
# Expose the port (Render will map this dynamically)
EXPOSE 10000
 
# Run FastAPI using Uvicorn
CMD ["uvicorn", "api.fastapi_backend:app", "--host", "0.0.0.0", "--port", "10000"]