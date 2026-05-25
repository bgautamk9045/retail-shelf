import motor.motor_asyncio as motor
import os

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME     = os.getenv("DB_NAME", "retail_shelf")

# motor is async MongoDB driver (works with FastAPI)
client = motor.AsyncIOMotorClient(MONGODB_URI)
db     = client[DB_NAME]

# Collections used:
#   db.events   — shelf scan results
#   db.planogram — expected shelf layout (optional, can be hardcoded)