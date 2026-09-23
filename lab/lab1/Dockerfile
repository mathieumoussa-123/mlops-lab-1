# =========================================================
# Stage 1: Builder
# =========================================================

FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv in the builder stage
RUN pip install --no-cache-dir uv

# Copy dependency files first so Docker can cache this layer
COPY pyproject.toml uv.lock ./

# Install project dependencies into /app/.venv
# --no-install-project avoids installing the local package
# before the source code has been copied
RUN uv sync --frozen --no-dev --no-install-project


# =========================================================
# Stage 2: Runtime
# =========================================================

FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY src/ /app/src/

# Make the virtual environment executables available
ENV PATH="/app/.venv/bin:$PATH"

# FastAPI/Uvicorn port
EXPOSE 8000

# Start the API
CMD ["uvicorn", "src.food11.serve:app", "--host", "0.0.0.0", "--port", "8000"]