from flask import Flask, render_template, redirect, url_for, request
import re
import os

# Import your image URLs dictionary from extras/image_links.py
from extras.image_links import image_data

app = Flask(__name__)

# Dummy descriptions for known species (keep as is)
descriptions = {
    'astrionella': 'Astrionella is a genus of diatoms with star-shaped colonies. Its cells are elongated and connected at the ends, forming radiating patterns.',
    'bellerochea': 'A diatom with rectangular cells joined in chains.',
    'chaetoceros': 'Chaetoceros is a genus of diatoms with elongated, chain-forming cells. Each cell has long, stiff spines called setae that extend outward, helping with buoyancy and protection.',
    'entomoneis': 'Elongated diatom with wing-like keels.',
    'euplotes': 'Ciliated protozoan with large, distinctive caudal cirri.',
    'heterosigma': 'Heterosigma is a genus of golden-brown flagellated microalgae with a highly variable cell shape. Each cell has two unequal flagella and surface scales that give it a distinctive texture.',
    'nannochloropsis': 'Green, non-motile spherical cells measuring between 2-5µm lacking flagella or complex external structures.',
    'navicula': 'Common benthic diatom genus with boat-shaped, elongated cells. They have fine, parallel striations and a central raphe used for gliding movement.',
    'nitzschia': 'Pennate benthic diatom with large spines.',
    'pleurosigma': 'Pleurosigma is a genus of pennate diatoms with elongated, slightly curved cells. Its silica shell features distinctive diagonal striations and a central raphe for movement.',
    'scripsiella': 'A photosynthetic dinoflagellate.',
    'thalassionema': 'Cells are usually in star-shaped or zigzagged chains. Cells are rectangular and have fine striations.',
}
def extract_species_name_from_url(url):
    # Extract filename from URL and get species name prefix (letters only)
    filename = url.split('/')[-1]
    match = re.match(r'^([a-zA-Z]+)', filename)
    if match:
        return match.group(1).lower()
    else:
        return filename.lower()

@app.route('/')
def home():
    # groups are keys in image_data dict
    groups = [{'name': group, 'thumbnail': image_data[group][0]} for group in image_data]
    return render_template('index.html', groups=groups)

@app.route('/group/<group_name>')
def group_detail(group_name):
    if group_name not in image_data:
        return f"No data found for group {group_name}", 404

    species_dict = {}
    for url in image_data[group_name]:
        species = extract_species_name_from_url(url)
        if species not in species_dict:
            species_dict[species] = url  # first image as thumbnail

    return render_template('group.html', group_name=group_name, species_list=species_dict)

@app.route('/algae/<alga_id>')
def alga_detail(alga_id):
    alga_id_lower = alga_id.lower()
    # Search for images of this species in all groups
    for group, urls in image_data.items():
        matched_images = [url for url in urls if extract_species_name_from_url(url) == alga_id_lower]
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

    # Search all species in all groups by matching query substring in species name
    for group, urls in image_data.items():
        for url in urls:
            species = extract_species_name_from_url(url)
            if species not in species_seen and query in species:
                species_seen.add(species)
                results.append({
                    'id': species,
                    'name': species.capitalize(),
                    'thumbnail': url,
                    'group': group
                })

    # Redirect if exact match found (case-insensitive)
    exact_matches = [r for r in results if r['id'].lower() == query.lower()]
    if len(exact_matches) == 1:
        return redirect(url_for('alga_detail', alga_id=query))

    return render_template('search_results.html', results=results, query=query)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
