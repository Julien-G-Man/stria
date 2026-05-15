from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {'message': 'Stria API is live'}

@app.get("/health")
def health():
    return {'status': 'ok'}