FROM continuumio/miniconda3

# Install mamba and set libmamba as the solver
RUN conda install mamba -n base -c conda-forge
RUN conda install -n base -c conda-forge conda-libmamba-solver
RUN conda config --set solver libmamba

# Additional dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy environment and requirements files
COPY api/environment.yml .
COPY api/requirements.txt .

# Create conda environment and install dependencies
RUN mamba env create -f environment.yml && conda clean --all
SHELL ["conda", "run", "-n", "ts", "/bin/bash", "-c"]

RUN conda run -n ts pip install --no-cache-dir -r requirements.txt
RUN conda run -n ts python -m nltk.downloader perluniprops
RUN conda run -n ts python -m nltk.downloader stopwords

# Expose the application port
EXPOSE 3003

# Set environment variables
ENV FLASK_APP=/app/app.py
ENV PYTHONPATH=/app  

# Default command
CMD ["conda", "run", "--no-capture-output", "-n", "ts", "python", "/app/app.py"]