from flask import Flask, request, render_template, jsonify, redirect, url_for, session  # Ajout de session
from tensorflow.keras.models import load_model
from PIL import Image
import numpy as np
import io
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import tensorflow as tf
app = Flask(__name__)
CORS(app)
app.secret_key = 'votre_cle_secrete_ici'  # Nécessaire pour les sessions

# Configuration de la base de données SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèle User pour la base de données
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username

# Créer la base de données (à faire une seule fois)
with app.app_context():
    db.create_all()
    # Route pour la page de changement de mot de passe
@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current-password')
        new_password = request.form.get('new-password')
        confirm_password = request.form.get('confirm-password')
        
        # Vérifier si l'utilisateur est connecté
        if 'username' not in session:
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=session['username']).first()
        
        if not user:
            return render_template('change-password.html', message='Erreur: Utilisateur non trouvé')
        
        # Vérifier le mot de passe actuel
        if not check_password_hash(user.password, current_password):
            return render_template('change-password.html', message='Erreur: Mot de passe actuel incorrect')
        
        # Vérifier la correspondance des nouveaux mots de passe
        if new_password != confirm_password:
            return render_template('change-password.html', message='Erreur: Les mots de passe ne correspondent pas')
        
        # Mettre à jour le mot de passe
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        return render_template('change-password.html', message='Succès: Mot de passe mis à jour')
    
    return render_template('change-password.html')

# Route pour la page de connexion (UNE SEULE FOIS)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password, password):
            return render_template('login.html', message='Nom d\'utilisateur ou mot de passe incorrect')
        
        # Stocker le nom d'utilisateur dans la session
        session['username'] = username
        
        return redirect(url_for('animal_recognition'))
    
    return render_template('login.html')


# Ajouter une route de déconnexion
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Charger le modèle entraîné
model = load_model('model_updated.keras')
class_names = ['Chien', 'Cheval', 'Éléphant', 'Papillon', 'Poulet', 'Chat', 'Vache', 'Mouton', 'Araignée', 'Écureuil']

# Base de données en mémoire pour les utilisateurs
users = {}


# Caractéristiques des animaux
animal_characteristics = {
    'Chien': {
        'habitat': 'Domestique, vit souvent avec les humains',
        'alimentation': 'Omnivore (croquettes, viande, légumes)',
        'poids_moyen': '5-50 kg selon la race',
        'esperance_vie': '10-15 ans'
    },
    'Cheval': {
        'habitat': 'Plaines, fermes, écuries',
        'alimentation': 'Herbivore (foin, herbe, grains)',
        'poids_moyen': '400-1000 kg',
        'esperance_vie': '25-30 ans'
    },
    'Éléphant': {
        'habitat': 'Savanes, forêts (Afrique, Asie)',
        'alimentation': 'Herbivore (feuilles, écorces, fruits)',
        'poids_moyen': '2000-14000 kg',
        'esperance_vie': '60-70 ans'
    },
    'Papillon': {
        'habitat': 'Jardins, forêts, prairies',
        'alimentation': 'Nectar des fleurs',
        'poids_moyen': '0.5-1 g',
        'esperance_vie': 'Quelques semaines'
    },
    'Poulet': {
        'habitat': 'Fermes, basse-cours',
        'alimentation': 'Omnivore (graines, insectes)',
        'poids_moyen': '1-3 kg',
        'esperance_vie': '5-10 ans'
    },
    'Chat': {
        'habitat': 'Domestique, vit souvent avec les humains',
        'alimentation': 'Carnivore (croquettes, viande)',
        'poids_moyen': '3-5 kg',
        'esperance_vie': '12-18 ans'
    },
    'Vache': {
        'habitat': 'Fermes, prairies',
        'alimentation': 'Herbivore (herbe, foin)',
        'poids_moyen': '600-1000 kg',
        'esperance_vie': '18-22 ans'
    },
    'Mouton': {
        'habitat': 'Fermes, prairies',
        'alimentation': 'Herbivore (herbe, foin)',
        'poids_moyen': '40-160 kg',
        'esperance_vie': '10-12 ans'
    },
    'Araignée': {
        'habitat': 'Partout (maisons, jardins, forêts)',
        'alimentation': 'Carnivore (insectes)',
        'poids_moyen': '0.1-50 g selon l’espèce',
        'esperance_vie': '1-2 ans'
    },
    'Écureuil': {
        'habitat': 'Forêts, parcs, jardins',
        'alimentation': 'Omnivore (noix, graines, fruits)',
        'poids_moyen': '0.5-1 kg',
        'esperance_vie': '6-12 ans'
    }
}


# Chemins des images similaires avec sous-dossiers et noms image1, image2, etc.
similar_images = {
    'Chien': ['images/Chien/image1.jpeg', 'images/Chien/image2.jpeg'],
    'Cheval': ['images/Cheval/image1.jpeg', 'images/Cheval/image2.jpeg'],
    'Éléphant': ['images/Éléphant/image1.jpeg', 'images/Éléphant/image2.jpeg'],
    'Papillon': ['images/Papillon/image1.jpeg', 'images/Papillon/image3.jpeg'],
    'Poulet': ['images/Poulet/image4.jpeg', 'images/Poulet/image6.jpeg'],
    'Chat': ['images/Chat/image5.webp', 'images/Chat/image3.jpeg'],
    'Vache': ['images/Vache/image2.jpeg', 'images/Vache/image6.jpeg'],
    'Mouton': ['images/Mouton/image2.jpeg', 'images/Mouton/image4.jpeg'],
    'Araignée': ['images/Araignée/image2.jpeg', 'images/Araignée/image6.jpeg'],
    'Écureuil': ['images/Écureuil/image1.jpeg', 'images/Écureuil/image7.jpeg']
}

# Route pour la page d'accueil
@app.route('/')
def home():
    return render_template('index.html')

# Route pour la page d'inscription
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        
        # Vérifier la confirmation du mot de passe
        if password != confirm_password:
            return render_template('register.html', message='Les mots de passe ne correspondent pas')
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            return render_template('register.html', message='Nom d\'utilisateur déjà pris')
        
        # Créer un nouvel utilisateur
        new_user = User(
            username=username,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')



@app.route('/view-users')
def view_users():
    users = User.query.all()
    return render_template('debug_users.html', users=users)
# Route pour la page de reconnaissance d'animaux
@app.route('/animal-recognition', methods=['GET', 'POST'])
def animal_recognition():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('animal-recognition.html', error='Aucune image téléchargée')
        file = request.files['file']
        image = Image.open(io.BytesIO(file.read())).convert('RGB').resize((96, 96))
        image_array = np.array(image) / 255.0
        image_array = np.expand_dims(image_array, axis=0)

        prediction = model.predict(image_array)
        predicted_class = class_names[np.argmax(prediction)]
        probability = float(np.max(prediction))

        # ✅ Nouveau : si la probabilité est trop faible (< 0.6), ce n'est pas un animal reconnu
        if probability < 0.6:
            return render_template('animal-recognition.html', error="Ce n'est pas un animal .")

        # Récupérer les caractéristiques et images similaires
        characteristics = animal_characteristics.get(predicted_class, {})
        images = similar_images.get(predicted_class, [])

        return render_template('animal-recognition.html', 
                              predicted_class=predicted_class,
                              probability=probability,
                              characteristics=characteristics,
                              similar_images=images)
    return render_template('animal-recognition.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
