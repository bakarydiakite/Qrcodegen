from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.http import FileResponse
import os

from cryptage.models import Membres, Departement, Stock, CardTemplate
from cryptage.serializers import (
    MembreSerializer, DepartementSerializer, CardTemplateSerializer,
    StockSerializer, CardGenerationRequestSerializer,
    CardGenerationResponseSerializer, BulkCardGenerationRequestSerializer,
    BulkCardGenerationResponseSerializer, MembreCreateSerializer
)
from cryptage.card_generator import CardGenerator


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def generate_card(request):
    """
    Générer une carte pour un membre.
    
    POST /api/cards/generate
    Body: {
        "member_id": 123  // OU
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "profession": "Developer",
        "department": "IT",
        "photo_url": "https://...",
        "template_id": 1  // optionnel
    }
    """
    # Pré-traitement des données pour éviter les erreurs de longueur
    mutable_data = request.data.copy()
    if mutable_data.get('phone'):
        mutable_data['phone'] = mutable_data['phone'][:9]
    if mutable_data.get('first_name'):
        mutable_data['first_name'] = mutable_data['first_name'][:32]
    if mutable_data.get('last_name'):
        mutable_data['last_name'] = mutable_data['last_name'][:32]
    if mutable_data.get('profession'):
        mutable_data['profession'] = mutable_data['profession'][:32]
        
    serializer = CardGenerationRequestSerializer(data=mutable_data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Données invalides',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # Récupérer ou créer le membre
        if data.get('member_id'):
            membre = get_object_or_404(Membres, id=data['member_id'])
        else:
            # Créer le membre avec les données fournies
            dept_name = data['department']
            departement, _ = Departement.objects.get_or_create(nom_depart=dept_name)
            
            # Vérifier si le membre existe déjà
            membre, created = Membres.objects.get_or_create(
                email=data['email'],
                defaults={
                    'prenom': data['first_name'][:32],  # Truncate to 32
                    'nom': data['last_name'][:32],      # Truncate to 32
                    'telephone': data.get('phone', '')[:9] if data.get('phone') else '', # Truncate to 9 for safety
                    'profession': data.get('profession', '')[:32], # Truncate to 32
                    'departement': departement
                }
            )
        
        # Récupérer le template
        if data.get('template_id'):
            template = get_object_or_404(CardTemplate, id=data['template_id'])
        else:
            template = CardTemplate.get_active_template()
            if not template:
                return Response({
                    'success': False,
                    'message': 'Aucun template actif trouvé'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Générer la carte
        generator = CardGenerator(membre, template=template)
        
        # Générer QR code
        qr_img = generator.generate_qr_code()
        
        # Générer carte recto
        carte_recto = generator.generate_card_front()
        
        # Générer carte verso
        carte_verso = generator.generate_card_back()
        
        # Générer PDF
        pdf_buffer = generator.generate_pdf()
        
        # Créer l'objet Stock d'abord
        # NETTOYAGE: Supprimer les anciennes cartes de ce membre pour éviter les doublons
        Stock.objects.filter(membre=membre).delete()
        
        stock = Stock(
            membre=membre,
            template_utilise=template
        )
        
        # Sauvegarder les fichiers
        from django.core.files.base import ContentFile
        import uuid
        
        # QR Code
        qr_buffer = generator.save_to_bytes(qr_img)
        stock.qr_code.save(
            f"{membre.prenom}_{membre.nom}_qr_{uuid.uuid4().hex[:8]}.png",
            ContentFile(qr_buffer.read()),
            save=False
        )
        
        # Recto
        recto_buffer = generator.save_to_bytes(carte_recto)
        stock.carte_recto.save(
            f"{membre.prenom}_{membre.nom}_recto_{uuid.uuid4().hex[:8]}.png",
            ContentFile(recto_buffer.read()),
            save=False
        )
        
        # Verso
        verso_buffer = generator.save_to_bytes(carte_verso)
        stock.carte_verso.save(
            f"{membre.prenom}_{membre.nom}_verso_{uuid.uuid4().hex[:8]}.png",
            ContentFile(verso_buffer.read()),
            save=False
        )
        
        # PDF
        stock.carte_pdf.save(
            f"{membre.prenom}_{membre.nom}_carte_{uuid.uuid4().hex[:8]}.pdf",
            ContentFile(pdf_buffer.read()),
            save=False
        )
        
        stock.save()
        
        # Construire les URLs complètes
        base_url = request.build_absolute_uri('/')[:-1]
        
        return Response({
            'success': True,
            'message': 'Carte générée avec succès',
            'card_id': stock.id,
            'qr_code_url': base_url + stock.qr_code.url if stock.qr_code else None,
            'card_front_url': base_url + stock.carte_recto.url if stock.carte_recto else None,
            'card_back_url': base_url + stock.carte_verso.url if stock.carte_verso else None,
            'pdf_url': base_url + stock.carte_pdf.url if stock.carte_pdf else None,
            'member': MembreSerializer(membre).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erreur lors de la génération: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def generate_bulk_cards(request):
    """
    Générer plusieurs cartes en une fois.
    
    POST /api/cards/generate-bulk
    Body: {
        "member_ids": [1, 2, 3, ...]  // OU
        "members_data": [{...}, {...}, ...],
        "template_id": 1  // optionnel
    }
    """
    # Pré-traitement des données pour éviter les erreurs de longueur
    mutable_data = request.data.copy()
    if mutable_data.get('members_data'):
        for member in mutable_data['members_data']:
            if member.get('phone'): member['phone'] = member['phone'][:9]
            if member.get('first_name'): member['first_name'] = member['first_name'][:32]
            if member.get('last_name'): member['last_name'] = member['last_name'][:32]
            if member.get('profession'): member['profession'] = member['profession'][:32]

    serializer = BulkCardGenerationRequestSerializer(data=mutable_data)
    
    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Données invalides',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Récupérer le template
    if data.get('template_id'):
        template = get_object_or_404(CardTemplate, id=data['template_id'])
    else:
        template = CardTemplate.get_active_template()
        if not template:
            return Response({
                'success': False,
                'message': 'Aucun template actif trouvé'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    generated_cards = []
    errors = []
    
    # Imports
    from django.core.files.base import ContentFile
    import uuid
    
    # Générer pour les member_ids
    if data.get('member_ids'):
        for member_id in data['member_ids']:
            try:
                membre = Membres.objects.get(id=member_id)
                
                # Générer la carte
                generator = CardGenerator(membre, template=template)
                qr_img = generator.generate_qr_code()
                carte_recto = generator.generate_card_front()
                carte_verso = generator.generate_card_back()
                pdf_buffer = generator.generate_pdf()
                
                # Créer l'objet Stock d'abord
                # NETTOYAGE: Supprimer les anciennes cartes
                Stock.objects.filter(membre=membre).delete()
                
                stock = Stock(
                    membre=membre,
                    template_utilise=template
                )
                
                # Sauvegarder les fichiers
                qr_buffer = generator.save_to_bytes(qr_img)
                stock.qr_code.save(
                    f"{membre.prenom}_{membre.nom}_qr_{uuid.uuid4().hex[:8]}.png",
                    ContentFile(qr_buffer.read()),
                    save=False
                )
                
                recto_buffer = generator.save_to_bytes(carte_recto)
                stock.carte_recto.save(
                    f"{membre.prenom}_{membre.nom}_recto_{uuid.uuid4().hex[:8]}.png",
                    ContentFile(recto_buffer.read()),
                    save=False
                )
                
                verso_buffer = generator.save_to_bytes(carte_verso)
                stock.carte_verso.save(
                    f"{membre.prenom}_{membre.nom}_verso_{uuid.uuid4().hex[:8]}.png",
                    ContentFile(verso_buffer.read()),
                    save=False
                )
                
                stock.carte_pdf.save(
                    f"{membre.prenom}_{membre.nom}_carte_{uuid.uuid4().hex[:8]}.pdf",
                    ContentFile(pdf_buffer.read()),
                    save=False
                )
                
                stock.save()
                
                generated_cards.append(stock)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                errors.append({
                    'member_id': member_id,
                    'error': str(e)
                })
    
    # Générer pour les members_data
    if data.get('members_data'):
        for member_data in data['members_data']:
            try:
                # Créer ou récupérer le membre
                dept_name = member_data.get('department', 'Non spécifié')
                departement, _ = Departement.objects.get_or_create(nom_depart=dept_name)
                
                membre, _ = Membres.objects.get_or_create(
                    email=member_data['email'],
                    defaults={
                        'prenom': member_data.get('first_name', ''),
                        'nom': member_data.get('last_name', ''),
                        'telephone': member_data.get('phone', ''),
                        'profession': member_data.get('profession', ''),
                        'departement': departement
                    }
                )
                
                # Générer la carte
                generator = CardGenerator(membre, template=template)
                qr_img = generator.generate_qr_code()
                carte_recto = generator.generate_card_front()
                carte_verso = generator.generate_card_back()
                pdf_buffer = generator.generate_pdf()
                
                # Créer l'objet Stock d'abord
                # NETTOYAGE: Supprimer les anciennes cartes
                Stock.objects.filter(membre=membre).delete()
                
                stock = Stock(
                    membre=membre,
                    template_utilise=template
                )
                
                # Sauvegarder les fichiers
                qr_buffer = generator.save_to_bytes(qr_img)
                stock.qr_code.save(
                    f"{membre.prenom}_{membre.nom}_qr_{uuid.uuid4().hex[:8]}.png",
                    ContentFile(qr_buffer.read()),
                    save=False
                )
                
                recto_buffer = generator.save_to_bytes(carte_recto)
                stock.carte_recto.save(
                    f"{membre.prenom}_{membre.nom}_recto_{uuid.uuid4().hex[:8]}.png",
                    ContentFile(recto_buffer.read()),
                    save=False
                )
                
                verso_buffer = generator.save_to_bytes(carte_verso)
                stock.carte_verso.save(
                    f"{membre.prenom}_{membre.nom}_verso_{uuid.uuid4().hex[:8]}.png",
                    ContentFile(verso_buffer.read()),
                    save=False
                )
                
                stock.carte_pdf.save(
                    f"{membre.prenom}_{membre.nom}_carte_{uuid.uuid4().hex[:8]}.pdf",
                    ContentFile(pdf_buffer.read()),
                    save=False
                )
                
                stock.save()
                
                generated_cards.append(stock)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                errors.append({
                    'member_data': member_data,
                    'error': str(e)
                })
    
    base_url = request.build_absolute_uri('/')[:-1]
    
    return Response({
        'success': True,
        'message': f'{len(generated_cards)} carte(s) générée(s)',
        'total': len(data.get('member_ids', [])) + len(data.get('members_data', [])),
        'generated': len(generated_cards),
        'failed': len(errors),
        'cards': StockSerializer(generated_cards, many=True, context={'request': request}).data,
        'errors': errors if errors else None
    }, status=status.HTTP_201_CREATED)




@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def list_cards(request):
    """
    Liste l'historique des cartes générées.
    
    GET /api/cards/
    """
    try:
        # Pagination
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        search = request.GET.get('search', '')
        
        # Tri safest: ID décroissant (toujours présent)
        queryset = Stock.objects.all().order_by('-id')

        # Recherche
        if search:
            queryset = queryset.filter(
                membre__nom__icontains=search
            ) | queryset.filter(
                membre__prenom__icontains=search
            )
        
        # Pagination manuelle simple
        total = queryset.count()
        start = (page - 1) * limit
        end = start + limit
        data = queryset[start:end]
        
        serializer = StockSerializer(data, many=True, context={'request': request})
        
        return Response({
            'success': True,
            'cards': serializer.data,
            'pagination': {
                'total': total,
                'page': page,
                'limit': limit,
                'totalPages': (total + limit - 1) // limit if limit > 0 else 1
            }
        })
    except Exception as e:
        # Catch-all pour éviter le 500 HTML
        return Response({
            'success': False,
            'message': f'Erreur lors de la récupération de l\'historique: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_card(request, card_id):
    """
    Récupérer les informations d'une carte générée.
    
    GET /api/cards/:id
    """
    stock = get_object_or_404(Stock, id=card_id)
    serializer = StockSerializer(stock, context={'request': request})
    
    return Response({
        'success': True,
        'card': serializer.data
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def list_templates(request):
    """
    Liste tous les templates disponibles.
    
    GET /api/templates
    """
    templates = CardTemplate.objects.all().order_by('-actif', '-date_creation')
    serializer = CardTemplateSerializer(templates, many=True, context={'request': request})
    
    return Response({
        'success': True,
        'templates': serializer.data
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_active_template(request):
    """
    Récupérer le template actif.
    
    GET /api/templates/active
    """
    template = CardTemplate.get_active_template()
    
    if not template:
        return Response({
            'success': False,
            'message': 'Aucun template actif'
        }, status=status.HTTP_404_NOT_FOUND)
    
    serializer = CardTemplateSerializer(template, context={'request': request})
    
    return Response({
        'success': True,
        'template': serializer.data
    })


@api_view(['PATCH'])
@authentication_classes([])
@permission_classes([AllowAny])
def activate_template(request, template_id):
    """
    Activer un template.
    
    PATCH /api/templates/:id/activate
    """
    template = get_object_or_404(CardTemplate, id=template_id)
    template.actif = True
    template.save()  # La méthode save() désactive automatiquement les autres
    
    serializer = CardTemplateSerializer(template, context={'request': request})
    
    return Response({
        'success': True,
        'message': 'Template activé avec succès',
        'template': serializer.data
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def list_members(request):
    """
    Liste tous les membres.
    
    GET /api/members
    """
    membres = Membres.objects.all().select_related('departement')
    serializer = MembreSerializer(membres, many=True)
    
    return Response({
        'success': True,
        'members': serializer.data
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def list_departments(request):
    """
    Liste tous les départements.
    
    GET /api/departments
    """
    departements = Departement.objects.all()
    serializer = DepartementSerializer(departements, many=True)
    
    return Response({
        'success': True,
        'departments': serializer.data
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def health_check(request):
    """
    Vérifier que l'API fonctionne.
    
    GET /api/health
    """
    return Response({
        'success': True,
        'message': 'API CJP Card Generator is running',
        'version': '1.0.0'
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def download_all_cards(request):
    """
    Télécharger toutes les cartes dans un SEUL fichier PDF (Grille A4).
    Filtres optionnels par date: start_date, end_date (YYYY-MM-DD)
    
    GET /api/cards/download-all?start_date=2024-01-01&end_date=2024-12-31
    """
    import io
    from django.utils.dateparse import parse_date
    from datetime import datetime
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    
    try:
        # Filtres de date
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        queryset = Stock.objects.all().order_by('id')
        
        if start_date_str:
            start_date = parse_date(start_date_str)
            if start_date:
                queryset = queryset.filter(date_creation__date__gte=start_date)
                
        if end_date_str:
            end_date = parse_date(end_date_str)
            if end_date:
                queryset = queryset.filter(date_creation__date__lte=end_date)
        
        # Vérifier s'il y a des cartes
        if not queryset.exists():
            return Response({
                'success': False,
                'message': 'Aucune carte trouvée pour cette période.'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Créer le PDF en mémoire
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Dimensions carte (Format CR80: 85.60 x 53.98 mm)
        card_w = 8.56 * cm
        card_h = 5.4 * cm
        
        # Marges et espacement
        margin_x = 1.0 * cm
        margin_y = 1.5 * cm
        gap_x = 0.5 * cm  # Espace entre Recto et Verso
        gap_y = 0.5 * cm  # Espace entre les lignes
        
        # Position initiale (Haut de page)
        current_y = height - margin_y - card_h
        cards_on_page = 0
        
        count = 0
        for stock in queryset:
            try:
                # Vérifier les images
                if stock.carte_recto and stock.carte_verso:
                    recto_path = stock.carte_recto.path
                    verso_path = stock.carte_verso.path
                    
                    if os.path.exists(recto_path) and os.path.exists(verso_path):
                        # Dessiner Recto (Gauche)
                        c.drawImage(recto_path, margin_x, current_y, width=card_w, height=card_h, preserveAspectRatio=True)
                        
                        # Dessiner Verso (Droite)
                        c.drawImage(verso_path, margin_x + card_w + gap_x, current_y, width=card_w, height=card_h, preserveAspectRatio=True)
                        
                        # Légende (Nom du membre sous la carte recto)
                        c.setFont("Helvetica", 8)
                        c.drawString(margin_x, current_y - 0.3 * cm, f"{stock.membre.prenom} {stock.membre.nom} (#{stock.id})")
                        
                        count += 1
                        cards_on_page += 1
                        
                        # Avancer position Y
                        current_y -= (card_h + gap_y + 0.5 * cm) # +0.5 pour la légende
                        
                        # Nouvelle page si plus de place (on peut mettre 4-5 cartes par page)
                        # Page height ~29.7cm. Card+Gap ~6.5cm. 29.7 / 6.5 = ~4.5
                        if current_y < margin_y:
                            c.showPage()
                            current_y = height - margin_y - card_h
                            cards_on_page = 0
            except Exception as e:
                print(f"Erreur dessin carte {stock.id}: {e}")
                continue
        
        c.save()
        buffer.seek(0)
        
        if count == 0:
             return Response({
                'success': False,
                'message': 'Aucune image de carte trouvée sur le disque.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Nom du fichier PDF
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"toutes_les_cartes_{date_str}.pdf"
        
        response = FileResponse(buffer, as_attachment=True, filename=filename)
        return response
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'Erreur lors de la création du PDF: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
