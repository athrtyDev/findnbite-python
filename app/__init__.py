from app.config import app, mongo
from app.routes import restaurant_routes, hashtag_routes
from app.admin import init_admin

# Register routes
restaurant_routes.register_routes(app)
hashtag_routes.register_routes(app)

# Initialize admin
init_admin(app, mongo) 