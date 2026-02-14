

def template_manager(request):
    """
    Interface de gestion des templates de cartes.
    """
    from cryptage.models import CardTemplate
    
    templates = CardTemplate.objects.all().order_by('-date_creation')
    active_template = CardTemplate.get_active_template()
    
    context = {
        'templates': templates,
        'active_template': active_template
    }
    
    return render(request, 'cryptage/template_manager.html', context)


def activate_template(request, template_id):
    """
    Active un template spécifique.
    """
    from cryptage.models import CardTemplate
    
    try:
        template = CardTemplate.objects.get(id=template_id)
        template.actif = True
        template.save()  # La méthode save() désactivera automatiquement les autres
        messages.success(request, f'Template "{template.nom}" activé avec succès !')
    except CardTemplate.DoesNotExist:
        messages.error(request, 'Template non trouvé')
    
    return redirect('template_manager')


def upload_template(request):
    """
    Upload un nouveau template de carte.
    """
    from cryptage.models import CardTemplate
    
    if request.method == 'POST':
        nom = request.POST.get('nom')
        template_recto = request.FILES.get('template_recto')
        template_verso = request.FILES.get('template_verso')
        actif = request.POST.get('actif') == 'on'
        
        if not nom or not template_recto or not template_verso:
            messages.error(request, 'Tous les champs sont requis')
            return redirect('template_manager')
        
        # Créer le nouveau template
        template = CardTemplate(
            nom=nom,
            template_recto=template_recto,
            template_verso=template_verso,
            actif=actif
        )
        template.save()
        
        messages.success(request, f'Template "{nom}" créé avec succès !')
        return redirect('template_manager')
    
    return redirect('template_manager')
