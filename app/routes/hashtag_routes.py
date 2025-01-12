from flask import request, jsonify
from app.config import mongo
from app.models.utils import parse_json, generate_short_id

def register_routes(app):
    @app.route('/api/hashtags', methods=['POST'])
    def add_hashtag():
        try:
            data = request.get_json()
            
            if 'name' not in data:
                return jsonify({'error': 'Name is required'}), 400

            existing_hashtag = mongo.db.hashtags.find_one({'name': data['name']})
            if existing_hashtag:
                return jsonify({'error': 'Hashtag already exists'}), 409

            hashtag = {
                '_id': data.get('_id', generate_short_id()),
                'name': data['name']
            }
            
            result = mongo.db.hashtags.insert_one(hashtag)
            created_hashtag = mongo.db.hashtags.find_one({'_id': hashtag['_id']})
            return jsonify({'message': 'Hashtag added successfully', 
                        'hashtag': parse_json(created_hashtag)}), 201
        
        except Exception as e:
            print(f"Error in add_hashtag: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/hashtags', methods=['GET'])
    def get_hashtags():
        try:
            search = request.args.get('search', '').lower()
            
            query = {}
            if search:
                query['name'] = {'$regex': search, '$options': 'i'}

            hashtags = list(mongo.db.hashtags.find(query))
            print(f"Found {len(hashtags)} hashtags")
            return jsonify({'hashtags': parse_json(hashtags)}), 200
        
        except Exception as e:
            print(f"Error in get_hashtags: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/hashtags/<hashtag_id>', methods=['PUT'])
    def update_hashtag(hashtag_id):
        try:
            data = request.get_json()
            
            existing_hashtag = mongo.db.hashtags.find_one({'_id': hashtag_id})
            if not existing_hashtag:
                return jsonify({'error': 'Hashtag not found'}), 404

            if 'name' in data:
                name_exists = mongo.db.hashtags.find_one({
                    '_id': {'$ne': hashtag_id},
                    'name': data['name']
                })
                if name_exists:
                    return jsonify({'error': 'Hashtag name already exists'}), 409

            update_data = {}
            if 'name' in data:
                update_data['name'] = data['name']

            if not update_data:
                return jsonify({'error': 'No valid fields to update'}), 400

            mongo.db.hashtags.update_one(
                {'_id': hashtag_id},
                {'$set': update_data}
            )

            updated_hashtag = mongo.db.hashtags.find_one({'_id': hashtag_id})
            return jsonify({'message': 'Hashtag updated successfully',
                        'hashtag': parse_json(updated_hashtag)}), 200
        
        except Exception as e:
            print(f"Error in update_hashtag: {str(e)}")
            return jsonify({'error': str(e)}), 500 