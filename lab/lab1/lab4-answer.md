# Lab 4 - Docker Compose Answers

## Question 1

If no volume is mounted to /mlflow-data, everything MLflow writes there is stored only inside that container's writable filesystem. When the container is removed, that runtime data is removed with it. Starting a new container from the same image creates a fresh filesystem, so the MLflow UI starts again without the data created by the previous container.

---

## Question 2

A named volume is managed directly by Docker and is independent of the project directory and host filesystem layout. It is convenient for persistent application data such as the MLflow database and artifacts because it survives container recreation without adding MLflow runtime files to the repository.

A bind mount could also work, but it would map the storage directly to a specific folder on the host machine. This is useful for local development, but it is more dependent on host paths and operating-system details. A named volume is cleaner and more portable for this Compose setup.

---

## Question 3

In Lab 3, MLflow was running directly on the Windows host, outside the Docker network. Therefore, the container needed host.docker.internal to reach the host machine.

In Lab 4, MLflow and inference are both services in the same Docker Compose network. Docker Compose provides internal DNS, so the service name mlflow automatically resolves to the MLflow container. Therefore, inference can use http://mlflow:5000.

---

## Question 4

Using an environment variable keeps the frontend image independent of a specific deployment environment. Inside Docker Compose, INFERENCE_URL can be set to http://inference:8000, while the same frontend image could be run somewhere else with a different inference URL without modifying or rebuilding the application code.

---

## Question 5

The inference service does not need a host-published port because it is only called by the frontend service inside the Docker Compose network. The frontend reaches it directly using the Compose service name inference and port 8000 through http://inference:8000.

Only services that need to be accessed directly from the host, such as MLflow on port 5000 and Streamlit on port 8501, need published ports.

---

## Question 6

depends_on controls container startup order, but it does not guarantee that the MLflow server is already ready to accept requests.

During the lab, the frontend initially received connection errors because the inference service was not yet ready. After MLflow and inference finished starting and the model was loaded successfully, the health endpoint returned 200 with {"status":"ok"} and predictions worked.

If inference attempts to load the model before MLflow is ready, the startup can fail or the service can temporarily be unavailable. A production setup would normally use health checks, retries, or startup retry logic to handle this.

---

## Question 7

The output showed:

- MLflow published port 5000 to the host.
- Frontend published port 8501 to the host.
- Inference exposed port 8000 only inside the Compose network and did not publish it to the host.

This matches the docker-compose.yml configuration. The user needs direct access to MLflow and Streamlit, while the frontend communicates with inference internally through the Compose network.

---

## Question 8

I created Version 2 of food11 and moved the champion alias from Version 1 to Version 2. The already-running inference process did not automatically reload the model because serve.py loads the model once at startup.

The command used to make inference resolve the champion alias again was:

docker compose restart inference

After the restart and a short startup delay, the inference service loaded models:/food11@champion successfully, which now pointed to Version 2.

---

## Question 9

A rebuild is not required because the inference image already contains the application code and Python dependencies. The registered model is not permanently baked into the image.

At container startup, serve.py connects to MLflow and loads models:/food11@champion. Therefore, changing the champion alias in MLflow does not require rebuilding the image. Restarting the inference container is enough to resolve the alias again and load the model version currently assigned to it.

---

## Question 10

Yes. After running a normal docker compose down followed by docker compose up, the MLflow registry still contained food11, Version 1, Version 2, and the champion alias pointing to Version 2.

This happened because a normal docker compose down removes the containers and network but preserves the named volume.

After running docker compose down -v and starting the stack again, the MLflow registry was empty. The MLflow UI contained only the fresh default experiment, and search_registered_models() returned [].

The -v option removed the mlflow-data named volume, so the MLflow database, registered models, aliases, and stored artifacts in that volume were deleted.

After completing this persistence test, I restored the model and the champion alias so the final Compose stack was functional again.

---

## Question 11

Docker Compose is mainly designed to orchestrate containers on a single machine. For multiple inference replicas distributed across machines, automatic scheduling, load balancing, self-healing, and high availability, a container orchestration platform such as Kubernetes would be needed.

MLflow would also need storage and database services that are independent of one physical machine, such as an external database and durable shared or object storage. This would allow the MLflow service to be restarted on another machine without losing its registry or artifacts.
