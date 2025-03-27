# -------------------------------------------------------
#  Dockerfile for Prompt Builder Flask App
# -------------------------------------------------------

# 1. Use an official lightweight Python image
FROM python:3.10-slim

# 2. Create a working directory in the container
WORKDIR /app

# 3. Copy requirements.txt first (for efficient caching)
COPY requirements.txt /app/

# 4. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the app code to the container
COPY . /app/

# 6. Expose the port Flask will run on
EXPOSE 5000

# 7. By default, run the Flask app
CMD ["python", "app.py"]