from dotenv import dotenv_values
env_vars = dotenv_values('.env')
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import uuid

app = Flask(__name__)
CORS(app)

# MongoDB Atlas connection details
MONGO_URI = env_vars['MONGO_URI']
print(MONGO_URI)
DB_NAME = 'zomatoDB'
MENU_COLLECTION = 'menu'
ORDERS_COLLECTION = 'orders'

# MongoDB client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
menu_collection = db[MENU_COLLECTION]
orders_collection = db[ORDERS_COLLECTION]

# Routes for managing the menu
@app.route('/menu', methods=['GET'])
def get_menu():
    menu = list(menu_collection.find())
    print(menu)
    return jsonify(menu)

@app.route('/menu', methods=['POST'])
def add_dish():
    dish = request.get_json()
    dish['_id'] = str(uuid.uuid4())
    menu_collection.insert_one(dish)
    return jsonify({"message": "Dish added successfully"})

@app.route('/menu/<dish_id>', methods=['DELETE'])
def remove_dish(dish_id):
    try:
        print('id : ',dish_id)
        result = menu_collection.delete_one({'_id': dish_id})

        if result.deleted_count == 1:
            return jsonify({"message": "Dish removed successfully"})
        else:
            return jsonify({"message": "Dish not found"})

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)})


@app.route('/menu/<dish_id>', methods=['PATCH'])
def update_dish_availability(dish_id):
    try:
        update_data = request.get_json()
        result = menu_collection.update_one({'_id': dish_id}, {'$set': update_data})

        if result.modified_count == 1:
            return jsonify({"message": "Dish availability updated"})
        elif result.matched_count == 1:
            return jsonify({"message": "No changes made to dish availability"})
        else:
            return jsonify({"message": "Dish not found"})

    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)})

# Routes for managing orders
@app.route('/orders', methods=['POST'])
def place_order():
    order = request.get_json()
    for dish_id in order['dish_ids']:
        dish = menu_collection.find_one({'_id': dish_id, 'availability': 'yes'})
        if dish:
            orders_collection.insert_one({
                'order_id': str(uuid.uuid4()),
                'customer_name': order['customer_name'],
                'dish_id': dish_id,
                'status': 'received'
            })
        else:
            return jsonify({"message": f"Dish {dish_id} is not available"})
    return jsonify({"message": "Order placed successfully"})

@app.route('/orders/<order_id>', methods=['PATCH'])
def update_order_status(order_id):
    status = request.get_json().get('status')
    orders_collection.update_one({'order_id': order_id}, {'$set': {'status': status}})
    return jsonify({"message": "Order status updated"})

# Start the Flask application
if __name__ == '__main__':
    app.run(debug=True)