FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-nep \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy code
COPY . .

# Install Python requirements
RUN pip install --upgrade pip && pip install -r requirements.txt

# Run app
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.enableCORS=false"]

