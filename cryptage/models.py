from django.db import models


# Create your models here.
class Departement(models.Model):
    nom_depart = models.CharField(max_length = 64)
    
    def __str__(self):
        return self.nom_depart

class Membres(models.Model):
    nom = models.CharField(max_length = 32)
    prenom = models.CharField(max_length = 32)
    departement = models.ForeignKey(Departement, on_delete = models.CASCADE)
    telephone = models.CharField(max_length = 9)
    email = models.EmailField(unique = True)
    profession = models.CharField(max_length = 32)
    photo = models.ImageField(upload_to='membres/photos/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.nom} {self.prenom}"

class CardTemplate(models.Model):
    nom = models.CharField(max_length=64, unique=True)
    template_recto = models.ImageField(upload_to='card_templates/')
    template_verso = models.ImageField(upload_to='card_templates/')
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Template de Carte"
        verbose_name_plural = "Templates de Cartes"
    
    def __str__(self):
        return f"{self.nom} {'(Actif)' if self.actif else ''}"
    
    @classmethod
    def get_active_template(cls):
        """Récupère le template actif. Retourne None si aucun template n'est actif."""
        return cls.objects.filter(actif=True).first()
    
    def save(self, *args, **kwargs):
        # Si ce template est marqué comme actif, désactiver tous les autres
        if self.actif:
            CardTemplate.objects.exclude(pk=self.pk).update(actif=False)
        super().save(*args, **kwargs)

class Stock(models.Model):
    membre = models.ForeignKey(Membres, on_delete = models.CASCADE)
    qr_code = models.ImageField(upload_to='qrcodes/', null=True, blank=True)  # QR code seul
    carte_recto = models.ImageField(upload_to='cartes/recto/', null=True, blank=True)  # Face avant
    carte_verso = models.ImageField(upload_to='cartes/verso/', null=True, blank=True)  # Face arrière avec QR
    carte_pdf = models.FileField(upload_to='cartes/pdf/', null=True, blank=True)  # PDF recto-verso
    template_utilise = models.ForeignKey(CardTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    date_generation = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date_generation']






