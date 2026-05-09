import json
import os
import uuid
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'projects.json')

PALETTE = ["#58A6FF", "#FF5A5F", "#68D66B", "#FFB703", "#B388FF", "#FF7F50"]

DEFAULT_PROJECTS = [
    {"name": "Website Refresh", "progress": 0.08, "colorHex": "#58A6FF", "lane": "racing"},
    {"name": "Launch Plan",     "progress": 0.24, "colorHex": "#FF5A5F", "lane": "bullpen"},
    {"name": "Client Portal",   "progress": 0.67, "colorHex": "#68D66B", "lane": "racing"},
    {"name": "Spring Campaign", "progress": 1.00, "colorHex": "#FFB703", "lane": "retired"},
]


def load_projects():
    if not os.path.exists(DATA_FILE):
        defaults = [{"id": str(uuid.uuid4()), **p} for p in DEFAULT_PROJECTS]
        save_projects(defaults)
        return defaults
    with open(DATA_FILE) as f:
        return json.load(f)


def save_projects(projects):
    with open(DATA_FILE, 'w') as f:
        json.dump(projects, f, indent=2)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manifest.json')
def manifest():
    return render_template('manifest.json'), 200, {'Content-Type': 'application/manifest+json'}


@app.route('/api/projects', methods=['GET'])
def get_projects():
    return jsonify(load_projects())


@app.route('/api/projects', methods=['POST'])
def add_project():
    projects = load_projects()
    data = request.get_json() or {}
    color = PALETTE[len(projects) % len(PALETTE)]
    name = (data.get('name') or '').strip() or f'Project {len(projects) + 1}'
    project = {
        'id': str(uuid.uuid4()),
        'name': name,
        'progress': 0.1,
        'colorHex': color,
        'lane': data.get('lane', 'bullpen'),
    }
    projects.append(project)
    save_projects(projects)
    return jsonify(project), 201


@app.route('/api/projects/<pid>', methods=['PATCH'])
def update_project(pid):
    projects = load_projects()
    for p in projects:
        if p['id'] == pid:
            data = request.get_json() or {}
            if 'name' in data:
                p['name'] = data['name']
            if 'progress' in data:
                p['progress'] = max(0.0, min(1.0, float(data['progress'])))
            if 'lane' in data and data['lane'] in ('bullpen', 'racing', 'retired'):
                p['lane'] = data['lane']
                if data['lane'] == 'retired':
                    p['progress'] = 1.0
            save_projects(projects)
            return jsonify(p)
    return jsonify({'error': 'not found'}), 404


@app.route('/api/projects/<pid>', methods=['DELETE'])
def delete_project(pid):
    projects = load_projects()
    projects = [p for p in projects if p['id'] != pid]
    save_projects(projects)
    return '', 204


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
