from starlette.requests import Request
from fastapi import FastAPI
from fastapi.background import BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel
import requests, time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:3000"],
    allow_methods = ["*"],
    allow_headers = ["*"]

)


# This should be a different database
redis =  get_redis_connection(
    host= "redis-19209.c80.us-east-1-2.ec2.cloud.redislabs.com",
    port=19209,
    password= "yPrR7kLjfSdUAd4X7JupqDwhTeB46Ev7",
    decode_responses=True
)


class Order(HashModel):
    product_id: str
    price: float 
    fee: float
    total: float
    quantity: int
    status: str # pending, completed, refunded

    class Meta:
        database = redis

@app.get("/orders/{pk}")
def get(pk: str):
    return Order.get(pk)

@app.post("/orders")
async def create(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    req = requests.get("http://localhost:8000/products/%s" % body["id"])
    product = req.json()

    order = Order(
        product_id = body["id"],
        price = product["price"],
        fee = 0.2 * product["price"],
        total = 1.2 * product["price"],
        quantity = body["quantity"],
        status = "pending"
    )
    order.save()

    # Running Bakcground task to change the status to completed
    background_tasks.add_task(order_completed, order)

    return order

def order_completed(order: Order):
    time.sleep(5)
    order.status = "completed"
    order.save()
    redis.xadd('order_completed', order.dict(), '*')

