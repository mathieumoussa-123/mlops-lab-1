import os
from io import BytesIO
from typing import Annotated

import mlflow.pyfunc
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from torchvision import transforms

import mlflow

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)

MODEL_URI = "models:/food11@champion"


# ---------------------------------------------------------
# Food-11 classes
# ---------------------------------------------------------

CATEGORIES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]


# ---------------------------------------------------------
# MLflow setup
# ---------------------------------------------------------

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

print(f"MLflow tracking URI: {MLFLOW_TRACKING_URI}")


# The model is kept at module level so tests can replace it
# with a fake model.
model = None


# ---------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------

transform = transforms.Compose(
    [
        transforms.Resize((128, 128)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


# ---------------------------------------------------------
# FastAPI
# ---------------------------------------------------------

app = FastAPI(
    title="Food-11 Classification API"
)


# ---------------------------------------------------------
# Startup
# ---------------------------------------------------------

@app.on_event("startup")
def load_model():
    global model

    # During unit tests, do not contact MLflow
    # or load the real model.
    if os.environ.get("SKIP_MODEL"):
        print("SKIP_MODEL is set - model loading skipped")
        return

    print(f"Loading model: {MODEL_URI}")

    model = mlflow.pyfunc.load_model(
        MODEL_URI
    )

    print("Model loaded successfully")


# ---------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------------------------------------------------
# Prediction endpoint
# ---------------------------------------------------------

@app.post("/predict")
async def predict(
    file: Annotated[UploadFile, File()]
):

    # If the real model was skipped and no fake model
    # has been inserted by a test, prediction is unavailable.
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model is not loaded",
        )

    image_bytes = await file.read()

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    image_tensor = transform(image)

    # Add batch dimension:
    # [3, 128, 128] -> [1, 3, 128, 128]
    image_tensor = image_tensor.unsqueeze(0)

    # MLflow pyfunc accepts NumPy input
    model_input = image_tensor.numpy()

    predictions = model.predict(
        model_input
    )

    # Convert model output to a torch tensor
    logits = torch.as_tensor(
        predictions
    )

    probabilities = torch.softmax(
        logits,
        dim=1,
    )

    confidence, predicted_class = torch.max(
        probabilities,
        dim=1,
    )

    class_index = predicted_class.item()

    return {
        "category": CATEGORIES[class_index],
        "confidence": float(
            confidence.item()
        ),
    }