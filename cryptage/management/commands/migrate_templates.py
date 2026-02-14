from django.core.management.base import BaseCommand
from django.core.files import File
from cryptage.models import CardTemplate
import os
from pathlib import Path


class Command(BaseCommand):
    help = 'Migre les templates de cartes existants vers la base de données'

    def handle(self, *args, **options):
        # Chemin vers le dossier des templates
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        template_dir = base_dir / 'model carte'
        
        recto_path = template_dir / 'carte devant.PNG'
        verso_path = template_dir / 'carte derriere.PNG'
        
        # Vérifier que les fichiers existent
        if not recto_path.exists():
            self.stdout.write(self.style.ERROR(f'Fichier non trouvé: {recto_path}'))
            return
        
        if not verso_path.exists():
            self.stdout.write(self.style.ERROR(f'Fichier non trouvé: {verso_path}'))
            return
        
        # Vérifier si un template existe déjà
        existing_template = CardTemplate.objects.filter(nom='Template CJP Original').first()
        
        if existing_template:
            self.stdout.write(self.style.WARNING('Un template "Template CJP Original" existe déjà.'))
            response = input('Voulez-vous le remplacer? (oui/non): ')
            if response.lower() not in ['oui', 'o', 'yes', 'y']:
                self.stdout.write(self.style.WARNING('Migration annulée.'))
                return
            else:
                # Supprimer l'ancien template
                existing_template.delete()
                self.stdout.write(self.style.SUCCESS('Ancien template supprimé.'))
        
        # Créer le nouveau template
        template = CardTemplate(
            nom='Template CJP Original',
            actif=True
        )
        
        # Ouvrir et attacher les fichiers
        with open(recto_path, 'rb') as recto_file:
            template.template_recto.save('carte_recto_original.png', File(recto_file), save=False)
        
        with open(verso_path, 'rb') as verso_file:
            template.template_verso.save('carte_verso_original.png', File(verso_file), save=False)
        
        # Sauvegarder le template
        template.save()
        
        self.stdout.write(self.style.SUCCESS(
            f'Template "{template.nom}" créé avec succès et marqué comme actif!'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Recto: {template.template_recto.url}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Verso: {template.template_verso.url}'
        ))
