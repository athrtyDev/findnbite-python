import string
import random
from datetime import datetime

def parse_json(data):
    """Helper function to convert ObjectId to string and format dates"""
    if isinstance(data, list):
        return [{**item, '_id': str(item['_id'])} for item in data]
    return {**data, '_id': str(data['_id'])}

def generate_short_id(length=9):
    """Generate a random string of letters and numbers"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def get_current_time():
    """Get current time in the required format"""
    return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT") 