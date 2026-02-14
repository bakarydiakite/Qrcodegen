from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count
from cryptage.models import Membres, Departement, Stock, CardTemplate
from datetime import datetime, timedelta


def admin_dashboard(request):
    """
    Dashboard principal de l'administration.
    """
    # Statistiques
    total_membres = Membres.objects.count()
    total_departements = Departement.objects.count()
    total_cartes = Stock.objects.count()
    total_templates = CardTemplate.objects.count()
    
    # Cartes générées cette semaine
    une_semaine = datetime.now() - timedelta(days=7)
    cartes_semaine = Stock.objects.filter(date_generation__gte=une_semaine).count()
    
    # Dernières cartes générées
    dernieres_cartes = Stock.objects.select_related('membre', 'template_utilise').order_by('-date_generation')[:5]
    
    # Membres par département
    membres_par_dept = Departement.objects.annotate(
        nombre_membres=Count('membres')
    ).order_by('-nombre_membres')
    
    context = {
        'total_membres': total_membres,
        'total_departements': total_departements,
        'total_cartes': total_cartes,
        'total_templates': total_templates,
        'cartes_semaine': cartes_semaine,
        'dernieres_cartes': dernieres_cartes,
        'membres_par_dept': membres_par_dept,
    }
    
    return render(request, 'cryptage/admin/dashboard.html', context)


def admin_membres_list(request):
    """
    Liste tous les membres avec recherche et filtres.
    """
    membres = Membres.objects.select_related('departement').all()
    departements = Departement.objects.all()
    
    # Recherche
    search = request.GET.get('search', '')
    if search:
        membres = membres.filter(
            nom__icontains=search
        ) | membres.filter(
            prenom__icontains=search
        ) | membres.filter(
            email__icontains=search
        )
    
    # Filtre par département
    dept_filter = request.GET.get('departement', '')
    if dept_filter:
        membres = membres.filter(departement_id=dept_filter)
    
    context = {
        'membres': membres,
        'departements': departements,
        'search': search,
        'dept_filter': dept_filter,
    }
    
    return render(request, 'cryptage/admin/membres_list.html', context)


def admin_membre_detail(request, membre_id):
    """
    Affiche les détails d'un membre et ses cartes générées.
    """
    membre = get_object_or_404(Membres, id=membre_id)
    cartes = Stock.objects.filter(membre=membre).order_by('-date_generation')
    
    context = {
        'membre': membre,
        'cartes': cartes,
    }
    
    return render(request, 'cryptage/admin/membre_detail.html', context)


def admin_membre_add(request):
    """
    Ajouter un nouveau membre.
    """
    if request.method == 'POST':
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        departement_id = request.POST.get('departement')
        telephone = request.POST.get('telephone')
        email = request.POST.get('email')
        profession = request.POST.get('profession')
        photo = request.FILES.get('photo')
        
        # Validation
        if Membres.objects.filter(email=email).exists():
            messages.error(request, 'Un membre avec cet email existe déjà !')
            return redirect('admin_membres_list')
        
        # Créer le membre
        membre = Membres.objects.create(
            nom=nom,
            prenom=prenom,
            departement_id=departement_id,
            telephone=telephone,
            email=email,
            profession=profession,
            photo=photo
        )
        
        messages.success(request, f'Membre {prenom} {nom} ajouté avec succès !')
        return redirect('admin_membre_detail', membre_id=membre.id)
    
    departements = Departement.objects.all()
    context = {'departements': departements}
    return render(request, 'cryptage/admin/membre_form.html', context)


def admin_membre_edit(request, membre_id):
    """
    Modifier un membre existant.
    """
    membre = get_object_or_404(Membres, id=membre_id)
    
    if request.method == 'POST':
        membre.nom = request.POST.get('nom')
        membre.prenom = request.POST.get('prenom')
        membre.departement_id = request.POST.get('departement')
        membre.telephone = request.POST.get('telephone')
        membre.email = request.POST.get('email')
        membre.profession = request.POST.get('profession')
        
        if request.FILES.get('photo'):
            membre.photo = request.FILES.get('photo')
        
        membre.save()
        messages.success(request, f'Membre {membre.prenom} {membre.nom} modifié avec succès !')
        return redirect('admin_membre_detail', membre_id=membre.id)
    
    departements = Departement.objects.all()
    context = {
        'membre': membre,
        'departements': departements,
        'edit_mode': True
    }
    return render(request, 'cryptage/admin/membre_form.html', context)


def admin_membre_delete(request, membre_id):
    """
    Supprimer un membre.
    """
    membre = get_object_or_404(Membres, id=membre_id)
    nom_complet = f"{membre.prenom} {membre.nom}"
    membre.delete()
    messages.success(request, f'Membre {nom_complet} supprimé avec succès !')
    return redirect('admin_membres_list')


def admin_departements_list(request):
    """
    Liste tous les départements.
    """
    departements = Departement.objects.annotate(
        nombre_membres=Count('membres')
    ).order_by('nom_depart')
    
    context = {'departements': departements}
    return render(request, 'cryptage/admin/departements_list.html', context)


def admin_departement_detail(request, dept_id):
    """
    Affiche les détails d'un département et ses membres.
    """
    departement = get_object_or_404(Departement, id=dept_id)
    membres = Membres.objects.filter(departement=departement)
    
    context = {
        'departement': departement,
        'membres': membres,
    }
    
    return render(request, 'cryptage/admin/departement_detail.html', context)


def admin_departement_add(request):
    """
    Ajouter un nouveau département.
    """
    if request.method == 'POST':
        nom_depart = request.POST.get('nom_depart')
        
        if Departement.objects.filter(nom_depart=nom_depart).exists():
            messages.error(request, 'Ce département existe déjà !')
            return redirect('admin_departements_list')
        
        dept = Departement.objects.create(nom_depart=nom_depart)
        messages.success(request, f'Département {nom_depart} ajouté avec succès !')
        return redirect('admin_departement_detail', dept_id=dept.id)
    
    return render(request, 'cryptage/admin/departement_form.html', {})


def admin_departement_edit(request, dept_id):
    """
    Modifier un département.
    """
    departement = get_object_or_404(Departement, id=dept_id)
    
    if request.method == 'POST':
        departement.nom_depart = request.POST.get('nom_depart')
        departement.save()
        messages.success(request, f'Département modifié avec succès !')
        return redirect('admin_departement_detail', dept_id=departement.id)
    
    context = {
        'departement': departement,
        'edit_mode': True
    }
    return render(request, 'cryptage/admin/departement_form.html', context)


def admin_departement_delete(request, dept_id):
    """
    Supprimer un département.
    """
    departement = get_object_or_404(Departement, id=dept_id)
    
    # Vérifier s'il y a des membres
    if departement.membres.count() > 0:
        messages.error(request, 'Impossible de supprimer ce département car il contient des membres !')
        return redirect('admin_departements_list')
    
    nom = departement.nom_depart
    departement.delete()
    messages.success(request, f'Département {nom} supprimé avec succès !')
    return redirect('admin_departements_list')


def admin_cartes_list(request):
    """
    Liste toutes les cartes générées.
    """
    cartes = Stock.objects.select_related('membre', 'template_utilise').order_by('-date_generation')
    
    # Filtre par membre
    membre_filter = request.GET.get('membre', '')
    if membre_filter:
        cartes = cartes.filter(membre_id=membre_filter)
    
    # Filtre par template
    template_filter = request.GET.get('template', '')
    if template_filter:
        cartes = cartes.filter(template_utilise_id=template_filter)
    
    membres = Membres.objects.all()
    templates = CardTemplate.objects.all()
    
    context = {
        'cartes': cartes,
        'membres': membres,
        'templates': templates,
        'membre_filter': membre_filter,
        'template_filter': template_filter,
    }
    
    return render(request, 'cryptage/admin/cartes_list.html', context)


def admin_carte_detail(request, carte_id):
    """
    Affiche les détails d'une carte générée.
    """
    carte = get_object_or_404(Stock, id=carte_id)
    
    context = {
        'carte': carte,
    }
    
    return render(request, 'cryptage/admin/carte_detail.html', context)
