FROM python:3.12-slim
WORKDIR /app                       
COPY requirements.txt .             
RUN pip install --no-cache-dir -r requirements.txt  

COPY . .                             
# Copy and make the script executable
COPY start.sh .
RUN chmod +x start.sh

# Use exec form to run the script (no shell interpolation)
CMD ["./start.sh"]  
