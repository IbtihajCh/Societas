FROM python:3.14-slim AS builder

WORKDIR /build

COPY simulation/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.14-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY simulation/ .

CMD ["python", "-m", "engine.main"]
