from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os
from django.conf import settings


class CardGenerator:
    """
    Générateur de cartes de membres avec QR code intégré.
    Supporte la génération en PNG (recto/verso) et PDF.
    """
    
    # Dimensions standard d'une carte de crédit en pixels (300 DPI)
    CARD_WIDTH = 1011  # 85.6mm à 300 DPI
    CARD_HEIGHT = 638  # 53.98mm à 300 DPI
    
    def __init__(self, membre, template=None):
        """
        Initialise le générateur de carte.
        
        Args:
            membre: Instance du modèle Membres
            template: Instance du modèle CardTemplate (optionnel)
        """
        self.membre = membre
        
        # Si aucun template n'est fourni, utiliser le template actif
        if template is None:
            from cryptage.models import CardTemplate
            template = CardTemplate.get_active_template()
        
        self.template = template
        self.qr_code_image = None
        self.carte_recto_image = None
        self.carte_verso_image = None
        
    def generate_qr_code(self, logo_path='static/images/log7.png'):
        """
        Génère un QR code avec le logo du club intégré.
        
        Args:
            logo_path: Chemin vers le logo à intégrer
            
        Returns:
            Image PIL du QR code
        """
        # Données à encoder dans le QR code
        data = (
            f"***CLUB DES JEUNES PROGRAMMEURS***\n"
            f"Nom: {self.membre.nom}\n"
            f"Prénom: {self.membre.prenom}\n"
            f"Département: {self.membre.departement}\n"
            f"Email: {self.membre.email}\n"
            f"Téléphone: {self.membre.telephone}\n"
            f"Profession: {self.membre.profession}\n"
            f"https://club-jp.com"
        )
        
        # Créer le QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Haute correction pour supporter le logo
            box_size=10,  # <<-- REMIS A 10 (haute résolution pour être net en réduction)
            border=1,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Générer l'image du QR code
        qr_img = qr.make_image(fill_color="black").convert('RGB')
        
        # Intégrer le logo si disponible
        # Construction du chemin absolu pour le logo par défaut
        if logo_path == 'static/images/log7.png':
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'log7.png')
            
        if os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert('RGBA')
                
                # Redimensionner le logo (environ 25% de la taille du QR code pour être plus visible)
                qr_width, qr_height = qr_img.size
                logo_size = min(qr_width, qr_height) // 4  # Ajusté à 25%
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Créer un fond blanc pour le logo (pour qu'il ne se mélange pas au QR code)
                # On fait un cercle blanc ou carré blanc derrière
                logo_bg = Image.new('RGB', (logo_size, logo_size), 'black') # <<-- CHANGÉ EN NOIR
                
                # Positionner le logo au centre
                logo_pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
                
                # Coller le fond noir d'abord
                qr_img.paste(logo_bg, logo_pos)
                
                # Coller le logo PAR DESSUS avec son masque de transparence (s'il en a un)
                qr_img.paste(logo, logo_pos, mask=logo)
                
            except Exception as e:
                print(f"Erreur lors de l'intégration du logo: {e}")
        else:
            print(f"Logo introuvable au chemin: {logo_path}")
        
        self.qr_code_image = qr_img
        return qr_img
    
    def generate_card_front(self):
        """
        Génère la face avant de la carte avec les informations du membre.
        
        Returns:
            Image PIL de la face avant
        """
        # Utiliser le template si disponible, sinon créer une carte par défaut
        if self.template and self.template.template_recto:
            try:
                # Charger le template
                template_path = self.template.template_recto.path
                card = Image.open(template_path).convert('RGB')
                
                # Redimensionner si nécessaire
                if card.size != (self.CARD_WIDTH, self.CARD_HEIGHT):
                    card = card.resize((self.CARD_WIDTH, self.CARD_HEIGHT), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"Erreur lors du chargement du template recto: {e}")
                card = self._create_default_front()
        else:
            card = self._create_default_front()
        
        # Ajouter les informations du membre sur la carte
        draw = ImageDraw.Draw(card)
        
        # Charger les polices (utiliser des polices par défaut si nécessaire)
        try:
            font_large = ImageFont.truetype("arial.ttf", 45)
            font_medium = ImageFont.truetype("arial.ttf", 32)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Ajouter la photo du membre si disponible
        if self.membre.photo:
            try:
                photo = Image.open(self.membre.photo.path).convert('RGB')
                # Redimensionner la photo (cercle de 150px de diamètre)
                photo_size = 150
                photo = photo.resize((photo_size, photo_size), Image.Resampling.LANCZOS)
                
                # Créer un masque circulaire
                mask = Image.new('L', (photo_size, photo_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, photo_size, photo_size), fill=255)
                
                # Appliquer le masque
                output = Image.new('RGB', (photo_size, photo_size), (255, 255, 255))
                output.paste(photo, (0, 0))
                output.putalpha(mask)
                
                # Positionner la photo (coin supérieur gauche)
                photo_x = 50
                photo_y = 50
                card.paste(output, (photo_x, photo_y), output)
            except Exception as e:
                print(f"Erreur lors de l'ajout de la photo: {e}")
        
        
        # Positionner le nom et prénom (À DROITE de la photo et de la zone orange)
        # On déplace tout vers le milieu/droite pour éviter le texte "CARTE MEMBRE"
        # text_color = (0, 0, 0)  # Noir (sur fond blanc)
        # name_x = 450  # Décalé vers la droite
        # name_y = 50   # En haut
        
        # full_name = f"{self.membre.prenom} {self.membre.nom}"
        # draw.text((name_x, name_y), full_name, fill=text_color, font=font_medium)
        
        # Positionner le département
        # dept_y = name_y + 40
        # draw.text((name_x, dept_y), str(self.membre.departement), fill=text_color, font=font_small)
        
        # Ajouter le QR Code sur le recto
        # Générer le QR code si ce n'est pas déjà fait
        if self.qr_code_image is None:
            self.generate_qr_code()

        # Dimensions du QR code (ajusté pour le recto)
        qr_size = 200  # <<-- Taille mise à jour à 200px
        qr_resized = self.qr_code_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Position du QR (Centré verticalement à droite)
        qr_x = self.CARD_WIDTH - qr_size - 80  # Marge augmentée pour bien centrer
        qr_y = (self.CARD_HEIGHT - qr_size) // 2 - 100 # <<-- ON SOUSTRAIT 100 POUR MONTER LE CODE (plus le chiffre est grand, plus ça monte)
        
        # Coller le QR code directement (sans cadre blanc supplémentaire)
        # On suppose que l'image QR a déjà un fond blanc ou transparent
        card.paste(qr_resized, (qr_x, qr_y))

        self.carte_recto_image = card
        return card
    
    def _create_default_front(self):
        """
        Crée une carte avant par défaut si aucun template n'est disponible.
        
        Returns:
        Image PIL de la carte avant par défaut
        """
        # Créer une image avec un design simple
        card = Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), color=(30, 30, 30))
        draw = ImageDraw.Draw(card)
        
        # Ajouter un rectangle orange (couleur du club)
        draw.rectangle([(50, 50), (self.CARD_WIDTH - 50, 200)], fill=(218, 165, 32))
        
        # Ajouter du texte
        try:
            font_title = ImageFont.truetype("arial.ttf", 50)
            font_text = ImageFont.truetype("arial.ttf", 30)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
        
        draw.text((100, 80), "CARTE MEMBRE", fill=(0, 0, 0), font=font_title)
        draw.text((100, 250), f"{self.membre.prenom} {self.membre.nom}", fill=(255, 255, 255), font=font_text)
        draw.text((100, 300), f"{self.membre.departement}", fill=(200, 200, 200), font=font_text)
        
        return card
    
    def generate_card_back(self):
        """
        Génère la face arrière de la carte (Image simple ou template verso).
        Note: Le QR code est maintenant sur le recto.
        
        Returns:
            Image PIL de la face arrière
        """
        # Utiliser le template si disponible, sinon créer une carte par défaut
        if self.template and self.template.template_verso:
            try:
                # Charger le template
                template_path = self.template.template_verso.path
                card = Image.open(template_path).convert('RGB')
                
                # Redimensionner si nécessaire
                if card.size != (self.CARD_WIDTH, self.CARD_HEIGHT):
                    card = card.resize((self.CARD_WIDTH, self.CARD_HEIGHT), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"Erreur lors du chargement du template verso: {e}")
                card = self._create_default_back()
        else:
            card = self._create_default_back()
        
        self.carte_verso_image = card
        return card
    
    def _create_default_back(self):
        """
        Crée une carte arrière par défaut si aucun template n'est disponible.
        
        Returns:
            Image PIL de la carte arrière par défaut
        """
        # Créer une image avec un design simple
        card = Image.new('RGB', (self.CARD_WIDTH, self.CARD_HEIGHT), color=(240, 240, 240))
        draw = ImageDraw.Draw(card)
        
        # Ajouter un titre
        try:
            font_title = ImageFont.truetype("arial.ttf", 40)
        except:
            font_title = ImageFont.load_default()
        
        draw.text((self.CARD_WIDTH // 2 - 250, 30), "CLUB DES JEUNES PROGRAMMEURS", 
                  fill=(30, 30, 30), font=font_title)
        
        return card
    
    def generate_pdf(self, output_path=None):
        """
        Génère un PDF contenant le recto et le verso de la carte.
        
        Args:
            output_path: Chemin de sortie du PDF (optionnel)
            
        Returns:
            BytesIO contenant le PDF
        """
        # Générer les cartes si ce n'est pas déjà fait
        if self.carte_recto_image is None:
            self.generate_card_front()
        if self.carte_verso_image is None:
            self.generate_card_back()
        
        # Créer un buffer pour le PDF
        buffer = BytesIO()
        
        # Créer le PDF
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Convertir les images PIL en format utilisable par ReportLab
        recto_buffer = BytesIO()
        self.carte_recto_image.save(recto_buffer, format='PNG')
        recto_buffer.seek(0)
        recto_img = ImageReader(recto_buffer)
        
        verso_buffer = BytesIO()
        self.carte_verso_image.save(verso_buffer, format='PNG')
        verso_buffer.seek(0)
        verso_img = ImageReader(verso_buffer)
        
        # Calculer les dimensions pour centrer les cartes
        # Format Carte de Crédit standard: 85.6mm x 53.98mm
        # Ratio: 1.585
        # En points (1 inch = 72 points) -> ~243 points de large
        
        card_width_pdf = 250  # Largeur confortable pour l'impression
        card_height_pdf = card_width_pdf * (self.CARD_HEIGHT / self.CARD_WIDTH)
        
        # Marge entre les deux cartes
        margin_x = 20
        
        # Largeur totale du bloc (Recto + Marge + Verso)
        total_width = (card_width_pdf * 2) + margin_x
        
        # Point de départ X pour centrer le tout sur la page
        start_x = (width - total_width) / 2
        
        # Position Y (centré verticalement ou un peu en haut)
        y_pos = height - card_height_pdf - 100
        
        # Coordonnées Recto
        x_recto = start_x
        
        # Coordonnées Verso (à droite du recto)
        x_verso = start_x + card_width_pdf + margin_x
        
        # Ajouter le recto
        c.drawImage(recto_img, x_recto, y_pos, width=card_width_pdf, height=card_height_pdf)
        c.drawCentredString(x_recto + (card_width_pdf / 2), y_pos - 20, "Recto")
        
        # Ajouter le verso
        c.drawImage(verso_img, x_verso, y_pos, width=card_width_pdf, height=card_height_pdf)
        c.drawCentredString(x_verso + (card_width_pdf / 2), y_pos - 20, "Verso")
        
        # Ajouter des informations
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 50, f"Carte générée pour: {self.membre.prenom} {self.membre.nom}")
        c.drawString(50, height - 65, f"Département: {self.membre.departement}")
        
        c.save()
        
        buffer.seek(0)
        
        # Sauvegarder dans un fichier si un chemin est fourni
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            buffer.seek(0)
        
        return buffer
    
    def save_to_bytes(self, image, format='PNG'):
        """
        Convertit une image PIL en BytesIO.
        
        Args:
            image: Image PIL
            format: Format de l'image (PNG, JPEG, etc.)
            
        Returns:
            BytesIO contenant l'image
        """
        buffer = BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        return buffer
