# Use a slim Python 3.10 image to avoid compatibility issues with faiss-cpu
FROM python:3.10-slim

# Install system dependencies if required (libgomp1 is often needed by faiss)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user 'user' with UID 1000 to comply with Hugging Face Spaces requirements
RUN useradd -m -u 1000 user

# Switch to the 'user'
USER user

# Set environment variables for the user's home directory and path
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory
WORKDIR $HOME/app

# Set HF_HOME to a directory the user has permissions to write to
# This prevents model loading failures when sentence-transformers tries to download models
ENV HF_HOME=$HOME/app/.cache/huggingface

# Copy requirements file with correct ownership
COPY --chown=user:user requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code with correct ownership
COPY --chown=user:user . $HOME/app

# Expose port 7860 which is required by Hugging Face Spaces
EXPOSE 7860

# Command to run the FastAPI server via uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
