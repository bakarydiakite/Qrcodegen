from django.urls import path
from cryptage import views
from cryptage import views_templates
from cryptage import views_admin

urlpatterns = [
    path('', views.home, name="home"),
    path('list/', views.list, name='list'),
    path('download-card/<int:stock_id>/', views.download_card_pdf, name='download_card'),
    path('preview-card/<int:stock_id>/', views.preview_card, name='preview_card'),
    path('regenerate-card/<int:membre_id>/', views.regenerate_card, name='regenerate_card'),
    
    # Gestion des templates
    path('templates/', views_templates.template_manager, name='template_manager'),
    path('templates/activate/<int:template_id>/', views_templates.activate_template, name='activate_template'),
    path('templates/upload/', views_templates.upload_template, name='upload_template'),
    
    # Administration personnalisée
    path('admin-panel/', views_admin.admin_dashboard, name='admin_dashboard'),
    
    # Gestion des membres
    path('admin-panel/membres/', views_admin.admin_membres_list, name='admin_membres_list'),
    path('admin-panel/membres/add/', views_admin.admin_membre_add, name='admin_membre_add'),
    path('admin-panel/membres/<int:membre_id>/', views_admin.admin_membre_detail, name='admin_membre_detail'),
    path('admin-panel/membres/edit/<int:membre_id>/', views_admin.admin_membre_edit, name='admin_membre_edit'),
    path('admin-panel/membres/delete/<int:membre_id>/', views_admin.admin_membre_delete, name='admin_membre_delete'),
    
    # Gestion des départements
    path('admin-panel/departements/', views_admin.admin_departements_list, name='admin_departements_list'),
    path('admin-panel/departements/add/', views_admin.admin_departement_add, name='admin_departement_add'),
    path('admin-panel/departements/<int:dept_id>/', views_admin.admin_departement_detail, name='admin_departement_detail'),
    path('admin-panel/departements/edit/<int:dept_id>/', views_admin.admin_departement_edit, name='admin_departement_edit'),
    path('admin-panel/departements/delete/<int:dept_id>/', views_admin.admin_departement_delete, name='admin_departement_delete'),
    
    # Gestion des cartes
    path('admin-panel/cartes/', views_admin.admin_cartes_list, name='admin_cartes_list'),
    path('admin-panel/cartes/<int:carte_id>/', views_admin.admin_carte_detail, name='admin_carte_detail'),
]


