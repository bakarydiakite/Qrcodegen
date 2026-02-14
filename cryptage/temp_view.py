
@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def download_all_cards(request):
    """
    Télécharger toutes les cartes (PDF) dans un fichier ZIP.
    Filtres optionnels par date: start_date, end_date (YYYY-MM-DD)
    
    GET /api/cards/download-all?start_date=2024-01-01&end_date=2024-12-31
    """
    import zipfile
    import io
    from django.utils.dateparse import parse_date
    from datetime import datetime, timedelta
    
    try:
        # Filtres de date
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        queryset = Stock.objects.all()
        
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
            
        # Créer le ZIP en mémoire
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            for stock in queryset:
                if stock.carte_pdf:
                    try:
                        file_path = stock.carte_pdf.path
                        if os.path.exists(file_path):
                            # Nom du fichier dans le ZIP
                            zip_filename = f"{stock.membre.prenom}_{stock.membre.nom}_{stock.id}.pdf"
                            zip_file.write(file_path, zip_filename)
                    except Exception as e:
                        print(f"Erreur ajout fichier {stock.id}: {e}")
                        continue
                        
        buffer.seek(0)
        
        # Nom du fichier ZIP
        date_str = datetime.now().strftime('%Y-%m-%d_%H%M')
        filename = f"cartes_membres_{date_str}.zip"
        
        response = FileResponse(buffer, as_attachment=True, filename=filename)
        return response
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erreur lors de la création du ZIP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
