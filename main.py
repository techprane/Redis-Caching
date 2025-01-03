from fastapi import FastAPI, HTTPException
import redis.asyncio as redis  
import asyncio
import json
from pydantic import BaseModel

app = FastAPI()

# Initialize Redis connection
redis_client = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    # Connect to Redis server
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()

# Data Model
class Item(BaseModel):
    id: int
    name: str
    description: str

# Simulated database
database = {
    1: {"id": 1, "name": "Item1", "description": "Description of Item1"},
    2: {"id": 2, "name": "Item2", "description": "Description of Item2"},
}

# Helper function to fetch data from "database"
async def fetch_item_from_db(item_id: int):
    await asyncio.sleep(1)  # Simulate database delay
    return database.get(item_id)

# Route to fetch item with Redis caching
@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    cache_key = f"item:{item_id}"
    
    # Check Redis cache
    cached_item = await redis_client.get(cache_key)
    if cached_item:
        return json.loads(cached_item)

    # If not in cache, fetch from database
    item = await fetch_item_from_db(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Store in Redis cache
    await redis_client.set(cache_key, json.dumps(item), ex=60)  # Cache for 60 seconds
    return item

# Clear cache for an item
@app.delete("/items/{item_id}/cache")
async def clear_item_cache(item_id: int):
    cache_key = f"item:{item_id}"
    await redis_client.delete(cache_key)
    return {"message": "Cache cleared"}








