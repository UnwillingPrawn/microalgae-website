from flask import Flask, render_template, url_for, redirect, request
import os
import re

# **NEW** import your image URLs from extras/image_links.py
from extras.image_links import image_data

app = Flask(__name__)

# Dummy descriptions for known species (keep as is)
descriptions = {
    'bellerochea': 'A diatom with rectangular cells joined in chains.',
    'nitzschia': 'Pennate benthic diatom with large spines.',
    'pleurosigma': 'Benthic diatom.',
    'astrionella': 'Colonial diatom forming star-shaped colonies.',
    'navicula': 'Common benthic diatom genus.',
    'entomoneis': 'Elongated diatom with wing-like keels.',
    'scripsiella': 'A photosynthetic dinoflagellate.',
    'euplotes': 'Ciliated protozoan with large, distinctive caudal cirri.',
    'nano': 'Green, non-motile spherical cells measuring between 2-5µm.',
    # Add more if needed
}

def extract_species_name(filename):
    match = re.match(r'^([a-zA-Z]+)', filename)
    if match:
        return match.group(1).lower()
    else:
        return os.path.splitext(filename)[0].lower()

@app.route('/')
def home():
    groups_path = os.path.join(app.static_folder, 'images')
    groups = [g for g in os.listdir(groups_path) if os.path.isdir(os.path.join(groups_path, g))]
    return render_template('index.html', groups=groups)

@app.route('/group/<group_name>')
def group_detail(group_name):
    group_folder = os.path.join(app.static_folder, 'images', group_name)
    species_dict = {}
    if os.path.exists(group_folder):
        for filename in os.listdir(group_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                species_name = extract_species_name(filename)
                if species_name not in species_dict:
                    species_dict[species_name] = filename  # First matching image
    return render_template('group.html', group_name=group_name, species_list=species_dict)

@app.route('/algae/<alga_id>')
def alga_detail(alga_id):
    alga_id_lower = alga_id.lower()

    # Search image_data for images matching alga_id (species name) in any group
    for group, urls in image_data.items():
        # Filter images that contain alga_id in filename (case-insensitive)
        matched_images = [url for url in urls if alga_id_lower in url.lower()]
        if matched_images:
            return render_template('alga.html', alga={
                'id': alga_id,
                'name': alga_id.capitalize(),
                'description': descriptions.get(alga_id_lower, "No description available."),
                'images': matched_images,
                'group': group
            })

    return f"No data found for {alga_id}", 404

@app.route('/search')
def search():
    query = request.args.get('query', '').lower().strip()
    if not query:
        return redirect(url_for('home'))

    results = []
    species_seen = set()
    base_folder = os.path.join(app.static_folder, 'images')

    for group in os.listdir(base_folder):
        group_folder = os.path.join(base_folder, group)
        if not os.path.isdir(group_folder):
            continue
        for filename in os.listdir(group_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                species_name = extract_species_name(filename)
                if species_name not in species_seen and query in species_name:
                    species_seen.add(species_name)
                    results.append({
                        'id': species_name,
                        'name': species_name.capitalize(),
                        'thumbnail': url_for('static', filename=f'images/{group}/{filename}'),
                        'group': group
                    })

    exact_matches = [r for r in results if r['id'] == query]
    if len(exact_matches) == 1:
        return redirect(url_for('alga_detail', alga_id=query))

    return render_template('search_results.html', results=results, query=query)

if __name__ == '__main__':
    app.run(debug=True)
