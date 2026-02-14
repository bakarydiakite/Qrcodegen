from django.urls import path
from cryptage import api_views

app_name = 'api'

urlpatterns = [
    # Health check
    path('health/', api_views.health_check, name='health_check'),
    
    # Card generation
    path('cards/generate/', api_views.generate_card, name='generate_card'),
    path('cards/generate-bulk/', api_views.generate_bulk_cards, name='generate_bulk_cards'),
    path('cards/<int:card_id>/', api_views.get_card, name='get_card'),
    path('cards/list/', api_views.list_cards, name='list_cards'),
    path('cards/download-all/', api_views.download_all_cards, name='download_all_cards'),
    
    # Templates
    path('templates/', api_views.list_templates, name='list_templates'),
    path('templates/active/', api_views.get_active_template, name='get_active_template'),
    path('templates/<int:template_id>/activate/', api_views.activate_template, name='activate_template'),
    
    # Members and Departments
    path('members/', api_views.list_members, name='list_members'),
    path('departments/', api_views.list_departments, name='list_departments'),
]
