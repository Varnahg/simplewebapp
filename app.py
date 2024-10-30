# app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
from datetime import datetime
import random

app = Flask(__name__)

# Data file path
DATA_FILE = os.path.join(app.root_path, 'data', 'data.json')

# Ensure data directory exists
if not os.path.exists(os.path.dirname(DATA_FILE)):
    os.makedirs(os.path.dirname(DATA_FILE))

# Load data from JSON
def load_data():
    if not os.path.exists(DATA_FILE):
        return {'users': {}, 'colors': {}}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Save data to JSON
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', users=data['users'], colors=data['colors'])

# Route to add a user
@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        goal = request.form.get('goal').strip()
        if not name or not goal:
            error = 'Please provide all fields.'
            return render_template('add_user.html', error=error)
        data = load_data()
        if name in data['users']:
            error = 'User already exists.'
            return render_template('add_user.html', error=error)
        data['users'][name] = {'goal': float(goal), 'weights': []}
        data['colors'][name] = [random.random(), random.random(), random.random()]
        save_data(data)
        return redirect(url_for('index'))
    return render_template('add_user.html')

# Route to add data
@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    data = load_data()
    if request.method == 'POST':
        user = request.form.get('user')
        date_str = request.form.get('date')
        weight = request.form.get('weight')
        if not user or not date_str or not weight:
            error = 'Please provide all fields.'
            return render_template('add_data.html', users=data['users'].keys(), error=error)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        timestamp = date_obj.timestamp()
        data['users'][user]['weights'].append({'timestamp': timestamp, 'weight': float(weight)})
        # Sort weights by timestamp
        data['users'][user]['weights'].sort(key=lambda x: x['timestamp'])
        save_data(data)
        return redirect(url_for('index'))
    return render_template('add_data.html', users=data['users'].keys())

# Route to edit a user
@app.route('/edit_user', methods=['GET', 'POST'])
def edit_user():
    data = load_data()
    if request.method == 'POST':
        old_name = request.form.get('old_name')
        new_name = request.form.get('new_name').strip()
        goal = request.form.get('goal').strip()
        if not old_name or not new_name or not goal:
            error = 'Please provide all fields.'
            return render_template('edit_user.html', users=data['users'].keys(), error=error)
        if old_name != new_name and new_name in data['users']:
            error = 'User with the new name already exists.'
            return render_template('edit_user.html', users=data['users'].keys(), error=error)
        data['users'][new_name] = data['users'].pop(old_name)
        data['users'][new_name]['goal'] = float(goal)
        data['colors'][new_name] = data['colors'].pop(old_name)
        save_data(data)
        return redirect(url_for('index'))
    return render_template('edit_user.html', users=data['users'].keys())

# Route to delete a user
@app.route('/delete_user', methods=['GET', 'POST'])
def delete_user():
    data = load_data()
    if request.method == 'POST':
        user = request.form.get('user')
        if user in data['users']:
            del data['users'][user]
            del data['colors'][user]
            save_data(data)
        return redirect(url_for('index'))
    return render_template('delete_user.html', users=data['users'].keys())

if __name__ == '__main__':
    app.run(debug=True)
