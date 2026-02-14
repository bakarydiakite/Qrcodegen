from django.http import JsonResponse
from django.shortcuts import render, redirect
from PIL import Image
import random as rd
import os
from io import BytesIO
from django.contrib import messages

from cryptage.models import Departement, Stock, Membres
from django.core.files.base import ContentFile


def home(request):
    departement = Departement.objects.all()
    image_afficher=Stock.objects.first()
    context={
            'img':image_afficher,
            'departement':departement
            
        }
    error = False
    if request.method=='POST':
        id_dep = request.POST.get('departement')
        prenom=request.POST.get('prenom')
        nom=request.POST.get('nom')
        email=request.POST.get('email')
        telephone=request.POST.get('telephone')
        profession=request.POST.get('profession')
        departement =Departement.objects.get(id = id_dep)
        
        exist_membre = Membres.objects.filter(email = email).exists()
        
        if exist_membre:
            error = True
            messages.error(request,"ce membre existe déja ou (email ou telephone) ont étés répeter!")
        else:
            error = False
            membre_cjp = Membres.objects.create(
                nom=nom, 
                prenom=prenom,
                departement=departement, 
                email=email,
                telephone=telephone,
                profession=profession
            )
            membre_cjp.save()
            
            # Importer le générateur de cartes
            from cryptage.card_generator import CardGenerator
            from cryptage.models import CardTemplate
            
            # Récupérer le template actif
            active_template = CardTemplate.get_active_template()
            
            # Créer une instance du générateur (utilisera le template actif automatiquement)
            generator = CardGenerator(membre_cjp, template=active_template)
            
            # Générer le QR code
            qr_img = generator.generate_qr_code()
            
            # Générer la carte recto
            carte_recto = generator.generate_card_front()
            
            # Générer la carte verso avec QR code
            carte_verso = generator.generate_card_back()
            
            # Générer le PDF
            pdf_buffer = generator.generate_pdf()
            
            # Créer l'entrée Stock
            table = Stock()
            table.membre = membre_cjp
            table.template_utilise = active_template  # Sauvegarder le template utilisé
            
            # Sauvegarder le QR code
            qr_buffer = generator.save_to_bytes(qr_img)
            table.qr_code.save(
                f"{prenom}_{nom}_qr_{rd.randint(1,1000)}.png", 
                ContentFile(qr_buffer.read())
            )
            
            # Sauvegarder la carte recto
            recto_buffer = generator.save_to_bytes(carte_recto)
            table.carte_recto.save(
                f"{prenom}_{nom}_recto_{rd.randint(1,1000)}.png", 
                ContentFile(recto_buffer.read())
            )
            
            # Sauvegarder la carte verso
            verso_buffer = generator.save_to_bytes(carte_verso)
            table.carte_verso.save(
                f"{prenom}_{nom}_verso_{rd.randint(1,1000)}.png", 
                ContentFile(verso_buffer.read())
            )
            
            # Sauvegarder le PDF
            table.carte_pdf.save(
                f"{prenom}_{nom}_carte_{rd.randint(1,1000)}.pdf", 
                ContentFile(pdf_buffer.read())
            )
            
            table.save()
            messages.success(request, "La carte de membre a été générée avec succès !")
  
        error_messages = messages.get_messages(request)
        context['error_messages'] = error_messages
        context['error']= error
        print(error_messages)
        
        return render(request, 'cryptage/index.html',context)
        
    return render(request,'cryptage/index.html',context)



def list(request):
    images = Stock.objects.all()
    return render(request, 'cryptage/list.html', {'images': images})


def download_card_pdf(request, stock_id):
    """
    Télécharge la carte en format PDF.
    """
    from django.http import FileResponse, Http404
    
    try:
        stock = Stock.objects.get(id=stock_id)
        if stock.carte_pdf:
            response = FileResponse(stock.carte_pdf.open('rb'), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{stock.membre.prenom}_{stock.membre.nom}_carte.pdf"'
            return response
        else:
            raise Http404("PDF non disponible")
    except Stock.DoesNotExist:
        raise Http404("Carte non trouvée")


def preview_card(request, stock_id):
    """
    Prévisualise la carte (recto et verso) avant téléchargement.
    """
    try:
        stock = Stock.objects.get(id=stock_id)
        context = {
            'stock': stock,
            'membre': stock.membre
        }
        return render(request, 'cryptage/preview_card.html', context)
    except Stock.DoesNotExist:
        messages.error(request, "Carte non trouvée")
        return redirect('list')


def regenerate_card(request, membre_id):
    """
    Régénère la carte pour un membre existant.
    """
    try:
        membre = Membres.objects.get(id=membre_id)
        
        # Importer le générateur de cartes
        from cryptage.card_generator import CardGenerator
        from cryptage.models import CardTemplate
        
        # Récupérer le template actif
        active_template = CardTemplate.get_active_template()
        
        # Créer une instance du générateur
        generator = CardGenerator(membre, template=active_template)
        
        # Générer le QR code
        qr_img = generator.generate_qr_code()
        
        # Générer la carte recto
        carte_recto = generator.generate_card_front()
        
        # Générer la carte verso avec QR code
        carte_verso = generator.generate_card_back()
        
        # Générer le PDF
        pdf_buffer = generator.generate_pdf()
        
        # Créer une nouvelle entrée Stock
        table = Stock()
        table.membre = membre
        table.template_utilise = active_template
        
        # Sauvegarder le QR code
        qr_buffer = generator.save_to_bytes(qr_img)
        table.qr_code.save(
            f"{membre.prenom}_{membre.nom}_qr_{rd.randint(1,1000)}.png", 
            ContentFile(qr_buffer.read())
        )
        
        # Sauvegarder la carte recto
        recto_buffer = generator.save_to_bytes(carte_recto)
        table.carte_recto.save(
            f"{membre.prenom}_{membre.nom}_recto_{rd.randint(1,1000)}.png", 
            ContentFile(recto_buffer.read())
        )
        
        # Sauvegarder la carte verso
        verso_buffer = generator.save_to_bytes(carte_verso)
        table.carte_verso.save(
            f"{membre.prenom}_{membre.nom}_verso_{rd.randint(1,1000)}.png", 
            ContentFile(verso_buffer.read())
        )
        
        # Sauvegarder le PDF
        table.carte_pdf.save(
            f"{membre.prenom}_{membre.nom}_carte_{rd.randint(1,1000)}.pdf", 
            ContentFile(pdf_buffer.read())
        )
        
        table.save()
        messages.success(request, "La carte a été régénérée avec succès !")
        return redirect('list')
        
    except Membres.DoesNotExist:
        messages.error(request, "Membre non trouvé")
        return redirect('list')
