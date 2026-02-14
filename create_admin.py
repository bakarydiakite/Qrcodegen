import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'generateur.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin():
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin'  # Mot de passe simple pour le développement

    if not User.objects.filter(username=username).exists():
        print(f"Création du superutilisateur '{username}'...")
        User.objects.create_superuser(username, email, password)
        print(f"✅ Superutilisateur créé avec succès !")
        print(f"👉 Username: {username}")
        print(f"👉 Password: {password}")
    else:
        print(f"⚠️ Le superutilisateur '{username}' existe déjà.")

if __name__ == '__main__':
    create_admin()
