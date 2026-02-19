FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    gfortran \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir streamlit plotly pydantic celery redis langchain langchain-openai langchain-community typer[all] PyQt5

# Copy source code
COPY . .
RUN pip install -e .

# Expose Streamlit port
EXPOSE 8501

# Default command is help
CMD ["sesame-cli", "--help"]
