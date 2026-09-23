import os
from io import BytesIO

import mlflow
import mlflow.pyfunc
import torch
from fastapi import FastAPI, File, UploadFile
from PIL import Image
from torchvision import transforms


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000"
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
print(f"Loading model: {MODEL_URI}")


# Load model once when the API starts
model = mlflow.pyfunc.load_model(MODEL_URI)

print("Model loaded successfully")


# ---------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------

transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# ---------------------------------------------------------
# FastAPI
# ---------------------------------------------------------

app = FastAPI(
    title="Food-11 Classification API"
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    image_bytes = await file.read()

    image = Image.open(
        BytesIO(image_bytes)
    ).convert("RGB")

    image_tensor = transform(image)

    # Add batch dimension:
    # [3, 128, 128] -> [1, 3, 128, 128]
    image_tensor = image_tensor.unsqueeze(0)

    # MLflow pyfunc accepts NumPy tensor input
    model_input = image_tensor.numpy()

    predictions = model.predict(model_input)

    # Convert output logits back to torch tensor
    logits = torch.as_tensor(predictions)

    probabilities = torch.softmax(
        logits,
        dim=1
    )

    confidence, predicted_class = torch.max(
        probabilities,
        dim=1
    )

    class_index = predicted_class.item()

    return {
        "category": CATEGORIES[class_index],
        "confidence": float(confidence.item())
    }