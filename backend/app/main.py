from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="StockFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


from app.routers import products, inventory, suppliers , purchase_orders 
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(suppliers.router)
app.include_router(purchase_orders.router)

from app.routers import auth 
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(suppliers.router)
app.include_router(purchase_orders.router)