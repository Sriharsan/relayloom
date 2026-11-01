# Relayloom agents inside the network isolated boundary. Synthetic data only.
FROM python:3.12-slim
RUN pip install --no-cache-dir cryptography==44.0.3 PyMuPDF==1.26.1
WORKDIR /app
COPY relayloom /app/relayloom
COPY fixtures /app/fixtures
COPY web /app/web
COPY scripts/boundary_probe.py /app/scripts/boundary_probe.py
ENV PYTHONUNBUFFERED=1
CMD ["python", "scripts/boundary_probe.py"]
