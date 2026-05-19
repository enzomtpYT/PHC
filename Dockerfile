FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

WORKDIR /app

COPY . .

RUN uv sync

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "src/Home.py"]