# Lab 3 Answers

## Answer 1

My registered food11 model was given Version 1.

A logged model artifact belongs to a specific MLflow training run and contains the saved model files produced by that run. A registered model gives that model a persistent name and version in the MLflow Model Registry. This makes it easier to manage and promote models independently of the individual experiment run that originally produced them.

---

## Answer 2

MLflow now uses user-defined aliases such as champion and challenger instead of the old fixed stages such as Staging and Production.

Versioning the model separately from the run gives the model its own lifecycle and version history even though it originally came from a particular training run.

An alias is more flexible because it is a mutable pointer. For example, champion can currently point to Version 1 and later be reassigned to Version 2 without changing the serving code or the model version numbers themselves.

In my case, food11 Version 1 was assigned the champion alias.

---

## Answer 3

Loading the model through models:/food11@champion avoids hard-coding the physical location of a .pth file and lets the serving application use the MLflow Model Registry.

The serving code only refers to the registered model name and the champion alias. If a newer model version becomes better, I only need to move the champion alias to that newer version. The serving code does not need to change.

This also separates model serving from the machine-specific location where the model artifact is stored.

---

## Answer 4

The dependency files are copied before the source code so Docker can cache the expensive dependency installation layer.

The dependencies only need to be reinstalled when pyproject.toml or uv.lock changes. If I only change a line in serve.py, Docker can reuse the cached dependency layer and only rebuild the later layer that copies the source code.

This makes repeated builds significantly faster.

---

## Answer 5

From my Docker images:

| Image | Disk usage | Content size |
| --- | ---: | ---: |
| Multi-stage image | 1.99 GB | 426 MB |
| Naive single-stage image | 2.13 GB | 456 MB |

The multi-stage image saved approximately 0.14 GB, or about 140 MB, of Docker disk usage and 30 MB of content size.

The largest layer in the multi-stage image was the copied virtual environment:

COPY /app/.venv /app/.venv — 1.43 GB

In the naive image, the largest layer was the dependency installation layer:

RUN uv sync --frozen --no-dev --no-install-project — 1.48 GB

The naive image also kept the uv installation layer of about 61 MB.

The multi-stage build is smaller because build-time tooling such as uv is left behind in the builder stage instead of being included in the final runtime image.

---

## Answer 6

Without .dockerignore, Docker would send unnecessary files such as .venv, the dataset, MLflow artifacts, Git history, and cache files as part of the build context. This would make the build context much larger and slow down builds.

My .dockerignore excludes:

- .venv/
- data/
- mlruns/
- mlflow.db
- .git/
- .dvc/
- __pycache__/
- *.pyc
- *.pyo
- *.pyd
- .pytest_cache/
- .DS_Store
- lab1-answer.md
- lab2-answer.md

The biggest unnecessary directories are .venv/, data/, and mlruns/.

With my current Dockerfile, simply sending these folders to the Docker daemon would mainly waste time and space because the Dockerfile only copies specific files. However, .venv/ would be especially problematic if it were accidentally copied into the image because my local virtual environment was created on Windows while the container runs Linux, so it would not be portable.

The mlruns/ directory also contains host-specific local MLflow artifact paths, so it should remain outside the image.

---

## Answer 7

A Docker container has its own isolated network namespace. Therefore, 127.0.0.1 inside the container refers to the container itself, not to the Windows host machine.

The MLflow server is running on the Windows host, so the container uses:

http://host.docker.internal:5000

host.docker.internal resolves to the host machine from inside Docker Desktop, allowing the container to communicate with the MLflow server running outside the container.

---

## Answer 8

Yes. I stopped the container and started a new container from the same food11-api:latest image without rebuilding it, and the API still started successfully and loaded the model.

This shows that the application code and Python dependencies are already baked into the Docker image.

The model itself is resolved and loaded at runtime through:

models:/food11@champion

from MLflow.

In my local setup, the container also needs access to the host MLflow server and the locally stored MLflow model artifacts at runtime. Therefore, changing the champion alias could make a newly started container load a different registered model version without rebuilding the Docker image.

---

## Answer 9

The Dockerfile is stored in Git, but the built Docker image currently exists only in my local Docker environment.

For another machine such as a CI runner or Kubernetes cluster to reliably use the exact same image, the image must be pushed to a container registry such as Docker Hub, GitHub Container Registry, Amazon ECR, or another registry.

The image should also be given a specific immutable version tag or referenced by its image digest rather than relying only on latest. This allows another machine to pull the exact built image instead of rebuilding it locally and potentially producing a different result.
