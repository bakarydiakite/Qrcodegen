from django.contrib import admin
from django.utils.html import format_html
from .models import Departement, Membres, Stock, CardTemplate


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ['nom_depart']
    search_fields = ['nom_depart']


@admin.register(Membres)
class MembresAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'departement', 'email', 'telephone', 'profession']
    list_filter = ['departement']
    search_fields = ['nom', 'prenom', 'email']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['membre', 'template_utilise', 'date_generation', 'preview_qr']
    list_filter = ['date_generation', 'template_utilise']
    search_fields = ['membre__nom', 'membre__prenom']
    readonly_fields = ['preview_recto', 'preview_verso', 'preview_qr', 'date_generation']
    
    def preview_qr(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="100" height="100" />', obj.qr_code.url)
        return "Pas de QR code"
    preview_qr.short_description = "Aperçu QR"
    
    def preview_recto(self, obj):
        if obj.carte_recto:
            return format_html('<img src="{}" width="300" />', obj.carte_recto.url)
        return "Pas de carte recto"
    preview_recto.short_description = "Aperçu Recto"
    
    def preview_verso(self, obj):
        if obj.carte_verso:
            return format_html('<img src="{}" width="300" />', obj.carte_verso.url)
        return "Pas de carte verso"
    preview_verso.short_description = "Aperçu Verso"


@admin.register(CardTemplate)
class CardTemplateAdmin(admin.ModelAdmin):
    list_display = ['nom', 'actif', 'date_creation', 'preview_recto_thumb', 'preview_verso_thumb']
    list_filter = ['actif', 'date_creation']
    search_fields = ['nom']
    readonly_fields = ['date_creation', 'preview_recto_large', 'preview_verso_large']
    
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'actif', 'date_creation')
        }),
        ('Templates', {
            'fields': ('template_recto', 'preview_recto_large', 'template_verso', 'preview_verso_large')
        }),
    )
    
    def preview_recto_thumb(self, obj):
        if obj.template_recto:
            return format_html('<img src="{}" width="100" />', obj.template_recto.url)
        return "Pas d'image"
    preview_recto_thumb.short_description = "Recto"
    
    def preview_verso_thumb(self, obj):
        if obj.template_verso:
            return format_html('<img src="{}" width="100" />', obj.template_verso.url)
        return "Pas d'image"
    preview_verso_thumb.short_description = "Verso"
    
    def preview_recto_large(self, obj):
        if obj.template_recto:
            return format_html('<img src="{}" width="400" />', obj.template_recto.url)
        return "Pas d'image"
    preview_recto_large.short_description = "Aperçu Recto"
    
    def preview_verso_large(self, obj):
        if obj.template_verso:
            return format_html('<img src="{}" width="400" />', obj.template_verso.url)
        return "Pas d'image"
    preview_verso_large.short_description = "Aperçu Verso"
    
    def save_model(self, request, obj, form, change):
        # Si ce template est marqué comme actif, désactiver tous les autres
        if obj.actif:
            CardTemplate.objects.exclude(pk=obj.pk).update(actif=False)
        super().save_model(request, obj, form, change)

