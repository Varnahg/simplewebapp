# app.py

from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import os
import json
from datetime import datetime
import random
import matplotlib.pyplot as plt
import io
import base64

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

# Function to generate the chart
def generate_chart(data):
    users = data['users']
    colors = data['colors']
    fig, ax = plt.subplots(figsize=(10, 6))

    any_data = False  # Flag to check if there's any data to plot

    for user, user_data in users.items():
        weights = user_data['weights']
        if not weights:
            continue

        any_data = True  # We have at least one user's data

        # Sort weights by timestamp
        weights.sort(key=lambda x: x['timestamp'])

        dates = [datetime.fromtimestamp(w['timestamp']) for w in weights]
        weight_values = [w['weight'] for w in weights]

        # Get color
        color = colors[user]
        rgb_color = (color[0], color[1], color[2])

        # Plot user's weight data
        ax.plot(dates, weight_values, label=user, color=rgb_color)

        # Plot goal line as a dotted line
        goal = user_data['goal']
        ax.hlines(y=goal, xmin=min(dates), xmax=max(dates), linestyles='dashed', colors=[rgb_color], label=f"{user}'s Goal")

    if not any_data:
        plt.close(fig)
        return None  # Return None if there's no data to plot

    ax.set_title('Weight Tracker')
    ax.set_xlabel('Date')
    ax.set_ylabel('Weight (kg)')
    ax.legend()

    # Format the x-axis for dates
    fig.autofmt_xdate()

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close(fig)  # Close the figure to free memory
    return img

@app.route('/')
def index():
    data = load_data()
    chart_img = generate_chart(data)
    chart_url = None
    if chart_img:
        chart_base64 = base64.b64encode(chart_img.getvalue()).decode('utf-8')
        chart_url = 'data:image/png;base64,{}'.format(chart_base64)
    users = data['users'].keys()
    return render_template('index.html', chart_url=chart_url, users=users)

# Rest of your routes (add_user, add_data, edit_user, delete_user)
@app.route('/view_data/<username>')
def view_data(username):
    data = load_data()
    if username not in data['users']:
        flash('User not found.')
        return redirect(url_for('index'))
    user_data = data['users'][username]
    # Sort weights by timestamp
    weights = sorted(user_data['weights'], key=lambda x: x['timestamp'])
    return render_template('view_data.html', username=username, weights=weights)

@app.route('/edit_entry/<username>/<timestamp>', methods=['GET', 'POST'])
def edit_entry(username, timestamp):
    data = load_data()
    if username not in data['users']:
        flash('User not found.')
        return redirect(url_for('index'))
    user_data = data['users'][username]
    entry = next((w for w in user_data['weights'] if str(w['timestamp']) == timestamp), None)
    if not entry:
        flash('Entry not found.')
        return redirect(url_for('view_data', username=username))
    if request.method == 'POST':
        date_str = request.form.get('date')
        weight = request.form.get('weight')
        if not date_str or not weight:
            flash('Please provide all fields.')
            return redirect(url_for('edit_entry', username=username, timestamp=timestamp))
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        new_timestamp = date_obj.timestamp()
        entry['timestamp'] = new_timestamp
        entry['weight'] = float(weight)
        # Sort weights by timestamp
        user_data['weights'].sort(key=lambda x: x['timestamp'])
        save_data(data)
        return redirect(url_for('view_data', username=username))
    # Prepare data for the template
    entry_date = datetime.fromtimestamp(entry['timestamp']).strftime('%Y-%m-%d')
    return render_template('edit_entry.html', username=username, entry=entry, entry_date=entry_date)

@app.route('/delete_entry/<username>/<timestamp>', methods=['POST'])
def delete_entry(username, timestamp):
    data = load_data()
    if username not in data['users']:
        flash('User not found.')
        return redirect(url_for('index'))
    user_data = data['users'][username]
    user_data['weights'] = [w for w in user_data['weights'] if str(w['timestamp']) != timestamp]
    save_data(data)
    return redirect(url_for('view_data', username=username))

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
        return redirect(url_for('view_data', username=user))
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

# Custom filter to convert timestamp to date string
@app.template_filter('timestamp_to_date')
def timestamp_to_date_filter(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

if __name__ == '__main__':
    app.run(debug=True)
