from flask import request, jsonify
from app.config import mongo
from app.models.utils import parse_json, get_current_time
from app.models.s3_utils import S3Uploader
from werkzeug.utils import secure_filename

def register_routes(app):
    s3_uploader = S3Uploader()

    @app.route('/api/restaurants', methods=['POST'])
    def add_restaurant():
        try:
            # Handle form data
            data = request.form.to_dict()
            required_fields = ['name', 'phone', 'shortLocation', 'description', 'priceRange', 'url']
            
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400

            # Handle file uploads
            uploaded_files = {
                'logo': None,
                'images': [],
                'menuImages': []
            }

            # Handle logo
            if 'logo' in request.files:
                logo_file = request.files['logo']
                if logo_file.filename:
                    uploaded_files['logo'] = s3_uploader.upload_file(logo_file, 'logos')

            # Handle images
            images = request.files.getlist('images')
            for image in images:
                if image.filename:
                    url = s3_uploader.upload_file(image, 'images')
                    uploaded_files['images'].append(url)

            # Handle menu images
            menu_images = request.files.getlist('menuImages')
            for menu_image in menu_images:
                if menu_image.filename:
                    url = s3_uploader.upload_file(menu_image, 'menus')
                    uploaded_files['menuImages'].append(url)

            current_time = get_current_time()
            
            # Create restaurant document
            restaurant = {
                'name': data['name'],
                'phone': data['phone'],
                'shortLocation': data['shortLocation'],
                'description': data['description'],
                'priceRange': data['priceRange'],
                'url': data['url'],
                'latitude': float(data.get('latitude', 0)),
                'longitude': float(data.get('longitude', 0)),
                'hashtags': data.get('hashtags', '').split(',') if data.get('hashtags') else [],
                'images': uploaded_files['images'],
                'menuImages': uploaded_files['menuImages'],
                'logo': uploaded_files['logo'],
                'rating': 0,
                'reviewCount': 0,
                '__v': 0,
                'createdAt': current_time,
                'updatedAt': current_time
            }
            
            result = mongo.db.restaurants.insert_one(restaurant)
            created_restaurant = mongo.db.restaurants.find_one({'_id': result.inserted_id})
            return jsonify({'message': 'Restaurant added successfully', 
                        'restaurant': parse_json(created_restaurant)}), 201
        
        except Exception as e:
            print(f"Error in add_restaurant: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/restaurants', methods=['GET'])
    def get_restaurants():
        print("GET /restaurants endpoint hit")
        try:
            hashtag = request.args.get('hashtag')
            
            query = {}
            if hashtag:
                query['hashtags'] = hashtag

            restaurants = list(mongo.db.restaurants.find(query))
            
            if restaurants:
                hashtag_ids = set()
                for restaurant in restaurants:
                    hashtag_ids.update(restaurant.get('hashtags', []))
                
                hashtags = {h['_id']: h['name'] 
                        for h in mongo.db.hashtags.find({'_id': {'$in': list(hashtag_ids)}})}
                
                for restaurant in restaurants:
                    restaurant['hashtagNames'] = [hashtags.get(h_id) for h_id in restaurant.get('hashtags', [])]

            print(f"Found {len(restaurants)} restaurants")
            return jsonify({'restaurants': parse_json(restaurants)}), 200
        
        except Exception as e:
            print(f"Error in get_restaurants: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/restaurants/<restaurant_id>', methods=['PUT'])
    def update_restaurant(restaurant_id):
        try:
            data = request.form.to_dict()
            
            existing_restaurant = mongo.db.restaurants.find_one({'_id': restaurant_id})
            if not existing_restaurant:
                return jsonify({'error': 'Restaurant not found'}), 404

            update_data = {}
            
            # Handle text fields
            allowed_fields = [
                'name', 'phone', 'shortLocation', 'description', 'priceRange', 
                'url', 'latitude', 'longitude', 'hashtags'
            ]
            
            for field in allowed_fields:
                if field in data:
                    if field == 'hashtags':
                        update_data[field] = data[field].split(',') if data[field] else []
                    elif field in ['latitude', 'longitude']:
                        update_data[field] = float(data[field])
                    else:
                        update_data[field] = data[field]

            # Handle file updates
            if 'logo' in request.files:
                logo_file = request.files['logo']
                if logo_file.filename:
                    # Delete old logo if exists
                    if existing_restaurant.get('logo'):
                        s3_uploader.delete_file(existing_restaurant['logo'])
                    update_data['logo'] = s3_uploader.upload_file(logo_file, 'logos')

            # Handle images
            if 'images' in request.files:
                images = request.files.getlist('images')
                if images and images[0].filename:
                    # Delete old images
                    for old_image in existing_restaurant.get('images', []):
                        s3_uploader.delete_file(old_image)
                    # Upload new images
                    update_data['images'] = [
                        s3_uploader.upload_file(image, 'images')
                        for image in images if image.filename
                    ]

            # Handle menu images
            if 'menuImages' in request.files:
                menu_images = request.files.getlist('menuImages')
                if menu_images and menu_images[0].filename:
                    # Delete old menu images
                    for old_menu in existing_restaurant.get('menuImages', []):
                        s3_uploader.delete_file(old_menu)
                    # Upload new menu images
                    update_data['menuImages'] = [
                        s3_uploader.upload_file(menu_image, 'menus')
                        for menu_image in menu_images if menu_image.filename
                    ]

            if not update_data:
                return jsonify({'error': 'No valid fields to update'}), 400

            update_data['updatedAt'] = get_current_time()

            mongo.db.restaurants.update_one(
                {'_id': restaurant_id},
                {'$set': update_data}
            )

            updated_restaurant = mongo.db.restaurants.find_one({'_id': restaurant_id})
            return jsonify({'message': 'Restaurant updated successfully',
                        'restaurant': parse_json(updated_restaurant)}), 200
        
        except Exception as e:
            print(f"Error in update_restaurant: {str(e)}")
            return jsonify({'error': str(e)}), 500 