FROM dhi.io/python:3.13-alpine3.21-dev AS builder

WORKDIR /app
ENV PATH="/app/venv/bin:$PATH"

RUN python -m venv /app/venv

COPY src/requirements.txt .

RUN apk add --no-cache g++
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt


FROM dhi.io/python:3.13-alpine3.21

WORKDIR /app
ENV PATH="/app/venv/bin:$PATH"

COPY --from=builder /app/venv /app/venv
COPY . /app/

EXPOSE 8501

ENTRYPOINT ["/app/venv/bin/python", "-m", "streamlit"]
CMD ["run", "src/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]