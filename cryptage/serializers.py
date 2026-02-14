from rest_framework import serializers
from cryptage.models import Membres, Departement, Stock, CardTemplate


class DepartementSerializer(serializers.ModelSerializer):
    """Serializer pour les départements."""
    
    class Meta:
        model = Departement
        fields = ['id', 'nom_depart']


class CardTemplateSerializer(serializers.ModelSerializer):
    """Serializer pour les templates de cartes."""
    
    class Meta:
        model = CardTemplate
        fields = ['id', 'nom', 'template_recto', 'template_verso', 'actif', 'date_creation']
        read_only_fields = ['date_creation']


class MembreSerializer(serializers.ModelSerializer):
    """Serializer pour les membres."""
    
    departement_name = serializers.CharField(source='departement.nom_depart', read_only=True)
    
    class Meta:
        model = Membres
        fields = [
            'id', 'nom', 'prenom', 'email', 'telephone', 
            'profession', 'photo', 'departement', 'departement_name'
        ]


class MembreCreateSerializer(serializers.Serializer):
    """Serializer pour créer un membre depuis l'API externe."""
    
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    profession = serializers.CharField(max_length=100, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100)
    photo_url = serializers.URLField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        """Créer ou récupérer un membre."""
        # Récupérer ou créer le département
        dept_name = validated_data.pop('department')
        departement, _ = Departement.objects.get_or_create(nom_depart=dept_name)
        
        # Créer le membre
        membre = Membres.objects.create(
            prenom=validated_data['first_name'],
            nom=validated_data['last_name'],
            email=validated_data['email'],
            telephone=validated_data.get('phone', ''),
            profession=validated_data.get('profession', ''),
            departement=departement
        )
        
        return membre


class CardGenerationRequestSerializer(serializers.Serializer):
    """Serializer pour la requête de génération de carte."""
    
    # Option 1: Utiliser un membre existant
    member_id = serializers.IntegerField(required=False)
    
    # Option 2: Fournir les données du membre
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    profession = serializers.CharField(max_length=100, required=False, allow_blank=True)
    department = serializers.CharField(max_length=100, required=False)
    photo_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Template à utiliser (optionnel, sinon utilise le template actif)
    template_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        """Valider qu'on a soit member_id, soit les données complètes."""
        if not data.get('member_id'):
            required_fields = ['first_name', 'last_name', 'email', 'department']
            missing_fields = [f for f in required_fields if not data.get(f)]
            if missing_fields:
                raise serializers.ValidationError(
                    f"Si member_id n'est pas fourni, les champs suivants sont requis: {', '.join(missing_fields)}"
                )
        return data


class StockSerializer(serializers.ModelSerializer):
    """Serializer pour les cartes générées."""
    
    membre = MembreSerializer(read_only=True)
    template = CardTemplateSerializer(source='template_utilise', read_only=True)
    
    class Meta:
        model = Stock
        fields = [
            'id', 'membre', 'qr_code', 'carte_recto', 'carte_verso', 
            'carte_pdf', 'template', 'date_generation'
        ]
        read_only_fields = fields


class CardGenerationResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de génération de carte."""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    card_id = serializers.IntegerField(required=False)
    qr_code_url = serializers.URLField(required=False)
    card_front_url = serializers.URLField(required=False)
    card_back_url = serializers.URLField(required=False)
    pdf_url = serializers.URLField(required=False)
    member = MembreSerializer(required=False)


class BulkCardGenerationRequestSerializer(serializers.Serializer):
    """Serializer pour la génération en masse de cartes."""
    
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Liste des IDs de membres"
    )
    
    members_data = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Liste des données de membres"
    )
    
    template_id = serializers.IntegerField(required=False)
    
    def validate(self, data):
        """Valider qu'on a au moins une liste."""
        if not data.get('member_ids') and not data.get('members_data'):
            raise serializers.ValidationError(
                "Vous devez fournir soit member_ids, soit members_data"
            )
        return data


class BulkCardGenerationResponseSerializer(serializers.Serializer):
    """Serializer pour la réponse de génération en masse."""
    
    success = serializers.BooleanField()
    message = serializers.CharField()
    total = serializers.IntegerField()
    generated = serializers.IntegerField()
    failed = serializers.IntegerField()
    cards = StockSerializer(many=True, required=False)
    errors = serializers.ListField(required=False)
