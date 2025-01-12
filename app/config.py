from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set secret key for session management
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '')

# Configure MongoDB
app.config["MONGO_URI"] = f"{os.getenv('MONGO_URI')}/{os.getenv('DB_NAME')}"
mongo = PyMongo(app)

# Test MongoDB connection
try:
    mongo.db.command('ping')
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Failed to connect to MongoDB. Error: {str(e)}")