from flask import Flask, render_template, redirect, url_for, request
import re

# Import your image URLs dictionary from extras/image_links.py
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

    # Redirect if exact match found
    exact_matches = [r for r in results if r['id'] == query]
    if len(exact_matches) == 1:
        return redirect(url_for('alga_detail', alga_id=query))

    return render_template('search_results.html', results=results, query=query)

if __name__ == '__main__':
    app.run(debug=True)
