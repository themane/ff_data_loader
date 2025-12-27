import csv
from io import StringIO

from fastapi import FastAPI, File, UploadFile

from services.DataLoader import DataLoader
from utils import load_configs

configs = load_configs("data_loader.yml")
app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, world!"}


@app.post("/load")
async def upload_csv(file: UploadFile = File(...)):
    content = await file.read()
    decoded = content.decode("utf-8")
    csv_reader = csv.DictReader(StringIO(decoded))
    DataLoader(configs).load_data(csv_reader)
    return {"message": "CSV data processed successfully."}
