FROM python:3.12-slim

# Install Java & Dependencies

RUN apt-get update && apt-get install -y \
    default-jre curl unzip git && \
    rm -rf /var/lib/apt/lists/*


# Install Nextflow
RUN curl -s https://get.nextflow.io | bash && \
    chmod +x nextflow && mv nextflow /usr/local/bin/

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501
CMD ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]