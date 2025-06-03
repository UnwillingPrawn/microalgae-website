from flask import Flask, render_template, redirect, url_for, request
import re
import os

app = Flask(__name__)

# Dummy descriptions for known species
descriptions = {
    'astrionella': 'Astrionella is a genus of diatoms with star-shaped colonies. Its cells are elongated and connected at the ends, forming radiating patterns.',
    'bellerochea': 'A diatom with rectangular cells joined in chains.',
    'chaetoceros': 'Chain-forming diatom with long spines (setae).',
    'entomoneis': 'Elongated diatom with wing-like keels.',
    'euplotes': 'Ciliated protozoan with large, distinctive caudal cirri.',
    'heterosigma': 'Flagellated golden-brown alga with variable cell shape.',
    'nannochloropsis': 'Green, non-motile spherical cells measuring 2–5µm.',
    'navicula': 'Boat-shaped benthic diatom with gliding movement.',
    'nitzschia': 'Pennate benthic diatom with large spines.',
    'oscillatoria': 'Filamentous cyanobacterium with oscillating motion.',
    'pleurosigma': 'Elongated pennate diatom with diagonal striations.',
    'scripsiella': 'Photosynthetic dinoflagellate.',
    'thalassionema': 'Diatom forming star-shaped or zigzag chains.',
    'thalassiosira': 'Centric diatom with circular, radially symmetrical cells.',
    'triceratium': 'Large triangular diatom with silicified walls.',
}

def extract_species_name_from_url(url):
    filename = url.split('/')[-1]
    match = re.match(r'^([a-zA-Z]+)', filename)
    return match.group(1).lower() if match else filename.lower()

def build_image_data():
    base_path = os.path.join(app.static_folder, 'images')
    data = {}

    for group_name in os.listdir(base_path):
        group_path = os.path.join(base_path, group_name)
        if os.path.isdir(group_path):
            image_files = [f for f in os.listdir(group_path)
                           if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
            urls = [url_for('static', filename=f'images/{group_name}/{f}') for f in image_files]
            if urls:
                data[group_name] = urls

    return data

@app.route('/')
def home():
    image_data = build_image_data()
    groups = [{'name': group, 'thumbnail': image_data[group][0]} for group in sorted(image_data)]
    return render_template('index.html', groups=groups)

@app.route('/group/<group_name>')
def group_detail(group_name):
    image_data = build_image_data()
    if group_name not in image_data:
        return f"No data found for group {group_name}", 404

    species_dict = {}
    for url in image_data[group_name]:
        species = extract_species_name_from_url(url)
        if species not in species_dict:
            species_dict[species] = url  # Use first image as species thumbnail

    sorted_species = dict(sorted(species_dict.items()))
    return render_template('group.html', group_name=group_name, species_list=sorted_species)

@app.route('/algae/<alga_id>')
def alga_detail(alga_id):
    image_data = build_image_data()
    alga_id_lower = alga_id.lower()

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

    image_data = build_image_data()
    results = []
    species_seen = set()

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

    exact_matches = [r for r in results if r['id'].lower() == query.lower()]
    if len(exact_matches) == 1:
        return redirect(url_for('alga_detail', alga_id=query))

    return render_template('search_results.html', results=results, query=query)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
