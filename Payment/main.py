from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.background import BackgroundTasks
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request
import requests, time
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

class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total: float
    quantity: int
    status: str  # pending, completed, refunded

    class Meta:
        database = redis

def format(pk: str):
    order = Order.get(pk)

    return {
        'id': order.pk,
        'product_id': order.product_id,
        'price': order.price,
        'fee': order.fee,
        'total': order.total,
        'quantity': order.quantity,
        'status': order.status
    }

@app.get('/orders')
def all():
    return [format(pk) for pk in Order.all_pks()]

@app.get('/orders/{pk}')
def get(pk: str):
    return Order.get(pk)

@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks):  # id, quantity
    body = await request.json()

    req = requests.get(os.getenv("PRODUCT")+'/products/%s' % body['id'])
    product = req.json()

    order = Order(
        product_id=body['id'],
        price=product['price'],
        fee=0.2 * product['price'],
        total=1.2 * product['price'],
        quantity=body['quantity'],
        status='pending'
    )
    order.save()

    background_tasks.add_task(order_completed, order)

    return order

def order_completed(order: Order):
    time.sleep(5)
    order.status = 'completed'
    order.save()
    redis.xadd('order_completed', order.dict(), '*')