# Dockerfile
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including git
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY . /workspace

# Install packages
RUN pip install --no-cache-dir jupyter notebook ipykernel \
    numpy pandas matplotlib scikit-learn seaborn plotly streamlit holidays \
    && pip install -r requirements.txt || true

EXPOSE 8888

ENV PYTHONPATH="/workspace:${PYTHONPATH}"

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
