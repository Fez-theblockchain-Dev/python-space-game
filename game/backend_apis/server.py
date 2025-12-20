import server
import name as __init__

from fastapi import FastAPI
app = FastAPI()
# get request 
@app.get("/")
def read_root():
    return{"welcome":"Guest"}

    


