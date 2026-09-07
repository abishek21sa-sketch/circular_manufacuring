FROM python:3.14-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY web/dist ./web/dist
COPY artifacts ./artifacts
COPY data ./data
RUN pip install --no-cache-dir ".[postgres]"
ENV HOST=0.0.0.0
ENV PORT=8765
ENV CIRCULAR_DEPLOYMENT_MODE=production
ENV CIRCULAR_AUTH_MODE=bearer
EXPOSE 8765
CMD ["python","scripts/run_workbench.py"]
