from fastapi import FastAPI, HTTPException

app = FastAPI(title="Shop API")


products = [
    {
        "id": 1,
        "name": "Laptop",
        "price": 75000,
    },
    {
        "id": 2,
        "name": "Keyboard",
        "price": 2500,
    },
    {
        "id": 3,
        "name": "Mouse",
        "price": 1200,
    },
]


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/products")
def get_products():
    return products


@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(
        status_code=404,
        detail="Product not found",
    )