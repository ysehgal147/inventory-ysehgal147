from fastapi import FastAPI
from redis_om import get_redis_connection,HashModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
 
load_dotenv()
env_path = Path('.')/'.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND")],
    allow_methods=['*'],
    allow_headers=['*']
)

redis = get_redis_connection(
    host=os.getenv("HOST"),
    port=os.getenv("PORT"),
    password=os.getenv("PASSWORD"),
    decode_responses=True
)

class Product(HashModel):
    name: str
    price: float
    quantity: int

    class Meta:
        database = redis

def format(pk: str):
    product = Product.get(pk)

    return {
        'id': product.pk,
        'name': product.name,
        'price': product.price,
        'quantity': product.quantity
    }

@app.get('/products')
def all():
    return [format(pk) for pk in Product.all_pks()]

@app.post('/products')
def create(product: Product):
    return product.save()

@app.get('/products/{pk}')
def get(pk: str):
    return Product.get(pk)

@app.delete('/products/{pk}')
def delete(pk: str):
    return Product.delete(pk)