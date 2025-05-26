from google.oauth2 import service_account
from googleapiclient.discovery import build

from flask import Flask, render_template, url_for, redirect, request
import os
import re

app = Flask(__name__)

# Google Drive API Setup
SERVICE_ACCOUNT_FILE = r'C:\Users\dardarer\Desktop\Microalgae_site\microalgae-image-links-7319380563f2.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=creds)

# The Google Drive folder ID for 'grouped' folder containing all algae groups
GROUPED_FOLDER_ID = '1QWRaRT7BLa6lfUGkXdQ0JgwjvAggwuM1'

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
    """
    Extract species name from filename using regex:
    Match letters at the start of the filename until the first digit or non-letter.
    """
    match = re.match(r'^([a-zA-Z]+)', filename)
    if match:
        return match.group(1).lower()
    else:
        # fallback to filename without extension
        return os.path.splitext(filename)[0].lower()

def list_files_in_folder(folder_id):
    """List files (and folders) inside a given Google Drive folder ID"""
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(id, name, mimeType)"
    ).execute()
    return results.get('files', [])

def get_algae_groups():
    """Get algae groups as list of dicts with name and thumbnail URL"""
    groups = []
    group_folders = list_files_in_folder(GROUPED_FOLDER_ID)
    for folder in group_folders:
        if folder['mimeType'] == 'application/vnd.google-apps.folder':
            # get images in this group folder
            images = list_files_in_folder(folder['id'])
            thumbnail_url = None
            for img in images:
                if img['mimeType'].startswith('image/'):
                    thumbnail_url = f"https://drive.google.com/uc?id={img['id']}"
                    break
            if thumbnail_url:
                groups.append({
                    'name': folder['name'],
                    'thumbnail': thumbnail_url
                })
    return groups

def get_species_in_group(group_name):
    """Return species dict: {species_name: thumbnail_url} for the group"""
    # Find group folder by name
    group_folders = list_files_in_folder(GROUPED_FOLDER_ID)
    folder_id = None
    for folder in group_folders:
        if folder['name'].lower() == group_name.lower():
            folder_id = folder['id']
            break
    if not folder_id:
        return {}

    species = {}
    images = list_files_in_folder(folder_id)
    for img in images:
        if not img['mimeType'].startswith('image/'):
            continue
        species_name = extract_species_name(img['name'])
        if species_name not in species:
            species[species_name] = f"https://drive.google.com/uc?id={img['id']}"
    return species

def get_photos_for_species(species_name):
    """Return dict with species info and all photo URLs"""
    group_folders = list_files_in_folder(GROUPED_FOLDER_ID)
    for folder in group_folders:
        if folder['mimeType'] != 'application/vnd.google-apps.folder':
            continue
        images = list_files_in_folder(folder['id'])
        species_images = []
        for img in images:
            if img['mimeType'].startswith('image/') and extract_species_name(img['name']) == species_name.lower():
                species_images.append(f"https://drive.google.com/uc?id={img['id']}")
        if species_images:
            return {
                'id': species_name,
                'name': species_name.capitalize(),
                'description': descriptions.get(species_name, "No description available."),
                'images': species_images,
                'group': folder['name']
            }
    return None

@app.route('/')
def home():
    groups = get_algae_groups()
    return render_template('index.html', groups=groups)

@app.route('/group/<group_name>')
def group_detail(group_name):
    species_list = get_species_in_group(group_name)
    return render_template('group.html', group_name=group_name, species_list=species_list)

@app.route('/algae/<alga_id>')
def alga_detail(alga_id):
    alga = get_photos_for_species(alga_id)
    if alga:
        return render_template('alga.html', alga=alga)
    else:
        return f"No data found for {alga_id}", 404

@app.route('/search')
def search():
    query = request.args.get('query', '').lower().strip()
    if not query:
        return redirect(url_for('home'))

    results = []
    species_seen = set()

    group_folders = list_files_in_folder(GROUPED_FOLDER_ID)
    for folder in group_folders:
        if folder['mimeType'] != 'application/vnd.google-apps.folder':
            continue
        images = list_files_in_folder(folder['id'])
        for img in images:
            if not img['mimeType'].startswith('image/'):
                continue
            species_name = extract_species_name(img['name'])
            if species_name not in species_seen and query in species_name:
                species_seen.add(species_name)
                results.append({
                    'id': species_name,
                    'name': species_name.capitalize(),
                    'thumbnail': f"https://drive.google.com/uc?id={img['id']}",
                    'group': folder['name']
                })

    exact_matches = [r for r in results if r['id'] == query]
    if len(exact_matches) == 1:
        return redirect(url_for('alga_detail', alga_id=query))

    return render_template('search_results.html', results=results, query=query)

if __name__ == '__main__':
    app.run(debug=True)