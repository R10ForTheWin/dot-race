import json
import os
import uuid
from flask import Flask, jsonify, request, render_template, redirect

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

PALETTE = ["#58A6FF", "#FF5A5F", "#68D66B", "#FFB703", "#B388FF", "#FF7F50"]


def data_file(token):
    safe = ''.join(c for c in token if c.isalnum())[:32]
    return os.path.join(DATA_DIR, f'{safe}.json')


SEED_PROJECTS = [
    {"name": "Project 1 Name Here", "progress": 0.20, "colorHex": "#58A6FF", "lane": "racing"},
    {"name": "Project 2 Name Here", "progress": 0.55, "colorHex": "#68D66B", "lane": "racing"},
    {"name": "Project 3 Name Here", "progress": 0.80, "colorHex": "#FFB703", "lane": "racing"},
]


def load_projects(token):
    f = data_file(token)
    if not os.path.exists(f):
        defaults = [{"id": str(uuid.uuid4()), **p} for p in SEED_PROJECTS]
        save_projects(token, defaults)
        return defaults
    with open(f) as fh:
        return json.load(fh)


def save_projects(token, projects):
    with open(data_file(token), 'w') as f:
        json.dump(projects, f, indent=2)


@app.route('/')
def root():
    return '''<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#000000">
</head><body style="background:#000"><script>
var t=localStorage.getItem('dottie_token');
if(!t){t=Math.random().toString(36).slice(2,10);localStorage.setItem('dottie_token',t);}
location.replace('/'+t);
</script></body></html>'''


@app.route('/<token>')
def index(token):
    if not token.isalnum() or len(token) > 32:
        return redirect('/')
    return render_template('index.html', token=token)


@app.route('/manifest.json')
def manifest():
    return render_template('manifest.json'), 200, {'Content-Type': 'application/manifest+json'}


@app.route('/api/<token>/projects', methods=['GET'])
def get_projects(token):
    return jsonify(load_projects(token))


@app.route('/api/<token>/projects', methods=['POST'])
def add_project(token):
    projects = load_projects(token)
    data = request.get_json() or {}
    color = PALETTE[len(projects) % len(PALETTE)]
    name = (data.get('name') or '').strip() or f'Project {len(projects) + 1}'
    project = {
        'id': str(uuid.uuid4()),
        'name': name,
        'progress': 0.0,
        'colorHex': color,
        'lane': data.get('lane', 'bullpen'),
    }
    projects.append(project)
    save_projects(token, projects)
    return jsonify(project), 201


@app.route('/api/<token>/projects/<pid>', methods=['PATCH'])
def update_project(token, pid):
    projects = load_projects(token)
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
            save_projects(token, projects)
            return jsonify(p)
    return jsonify({'error': 'not found'}), 404


@app.route('/api/<token>/projects/<pid>', methods=['DELETE'])
def delete_project(token, pid):
    projects = load_projects(token)
    projects = [p for p in projects if p['id'] != pid]
    save_projects(token, projects)
    return '', 204


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
