FROM continuumio/miniconda3

RUN conda install mamba -n base -c conda-forge
RUN conda install -n base -c conda-forge conda-libmamba-solver
RUN conda config --set solver libmamba

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY environment.yml .

RUN mamba env create -f environment.yml && conda clean --all
SHELL ["conda", "run", "-n", "ts", "/bin/bash", "-c"]

COPY requirements_.txt .
RUN conda run -n ts pip install --no-cache-dir -r requirements_.txt
RUN conda run -n ts python -m nltk.downloader perluniprops
RUN conda run -n ts python -m nltk.downloader stopwords

EXPOSE 3003

ENV FLASK_APP=api/app.py
CMD ["conda", "run", "--no-capture-output", "-n", "ts", "python", "api/app.py"]