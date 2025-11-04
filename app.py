from fastapi import FastAPI
from pydantic import BaseModel # for validating and parsing input data
import torch
import torch.nn as nn
import joblib

# Define model
class SpamClassifier(nn.Module):
    def __init__(self, input_size, hidden_size=64):
        super(SpamClassifier, self).__init__()
        self.model = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1)
        )

    def forward(self, x):
        return self.model(x)

# Load model + vectorizer
vectorizer = joblib.load("vectorizer.pkl")

model = SpamClassifier(input_size=len(vectorizer.get_feature_names_out()))
model.load_state_dict(torch.load("spam_classifier_weights.pth", map_location="cpu"))
model.eval()  

# FastAPI setup
app = FastAPI()

class EmailText(BaseModel):
    text: str

@app.get("/")
def home():
    return {"message": "Spam classifier API is running."}

@app.post("/predict")
def predict_email(data: EmailText):
    # Vectorize text
    X = vectorizer.transform([data.text]).toarray()
    X_tensor = torch.tensor(X, dtype=torch.float32)

    # Predict
    with torch.no_grad(): 
        output = model(X_tensor)
        prob = torch.sigmoid(output).item()
        label = "spam" if prob >= 0.5 else "ham"

    return {"prediction": label, "probability": prob}
