# Stage 1: Build the application
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only files necessary for dependency installation
COPY pyproject.toml poetry.lock* ./

# Install production dependencies
# --no-dev: Do not install development dependencies
# --no-interaction: Do not ask any interactive questions
# --no-ansi: Disable ANSI output
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application code
COPY . .

# Stage 2: Production image
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PORT=8000

# Copy installed dependencies from builder stage
COPY --from=builder /app/.venv /.venv
# Copy application code
COPY --from=builder /app/main.py ./main.py
# If you have other source files under open_notebook_mcp, copy them too
# COPY --from=builder /app/open_notebook_mcp ./open_notebook_mcp

# Activate virtual environment
ENV PATH="/.venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]