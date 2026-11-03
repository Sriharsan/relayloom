# Relayloom agents inside the network isolated boundary. Synthetic data only.
FROM python:3.12-slim
WORKDIR /app
COPY requirements-ap.txt /app/requirements-ap.txt
# Playwright is left out: without it the dispute form is posted over HTTP and the run says so.
RUN grep -v '^playwright' requirements-ap.txt > /tmp/requirements.txt && pip install --no-cache-dir -r /tmp/requirements.txt
COPY relayloom /app/relayloom
COPY fixtures /app/fixtures
COPY web /app/web
COPY scripts/boundary_probe.py /app/scripts/boundary_probe.py
ENV PYTHONUNBUFFERED=1
CMD ["python", "scripts/boundary_probe.py"]
