# 🚀 Démarrage Rapide - Génération de Cartes

## ⚡ Lancement en 3 Étapes

### 1️⃣ Démarrer Django (Terminal 1)

```bash
cd C:\Users\SHERLOCK\Desktop\Qrcodegen\generateur
python manage.py runserver
```

✅ **Vérification** : http://localhost:8000/api/health/

---

### 2️⃣ Démarrer Node.js Backend (Terminal 2)

```bash
cd C:\Users\SHERLOCK\Desktop\Qrcodegen\generateur\cjp-backend
npm run dev
```

✅ **Vérification** : http://localhost:3000/api/v1/health

---

### 3️⃣ Démarrer React Frontend (Terminal 3)

```bash
cd C:\Users\SHERLOCK\Desktop\Qrcodegen\generateur\cjp-front
npm run dev
```

✅ **Vérification** : http://localhost:5173

---

## 🎯 Accès Rapide

1. **Connectez-vous** à l'application React
2. **Cliquez sur "Cartes"** dans le menu (icône QR code)
3. **Sélectionnez des membres** et cliquez "Générer"

---

## 📁 Fichiers Créés

### Frontend React
- ✅ `cjp-front/src/services/card.service.ts`
- ✅ `cjp-front/src/pages/admin/Cards.tsx`
- ✅ `cjp-front/.env` (mis à jour)

### Backend Django
- ✅ `cryptage/serializers.py`
- ✅ `cryptage/api_views.py`
- ✅ `cryptage/api_urls.py`
- ✅ `generateur/settings.py` (CORS configuré)

---

## 🔧 Configuration

### Variables d'Environnement

**`.env` (React)** :
```env
VITE_API_URL=http://localhost:3000/api/v1
VITE_DJANGO_API_URL=http://localhost:8000/api
```

**`settings.py` (Django)** :
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
]
```

---

## 🧪 Tests Rapides

### Test API Django
```bash
curl http://localhost:8000/api/health/
```

### Test Génération Carte
```bash
curl -X POST http://localhost:8000/api/cards/generate/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"User","email":"test@test.com","department":"IT"}'
```

---

## ❓ Problèmes Courants

### "API Django non accessible"
➡️ Vérifiez que Django tourne : `python manage.py runserver`

### "CORS Error"
➡️ Vérifiez `CORS_ALLOWED_ORIGINS` dans `settings.py`

### "Aucun template actif"
➡️ Uploadez un template via http://localhost:8000/admin-panel/templates/

---

## 📚 Documentation Complète

- 📖 [Guide d'Installation Complet](./setup_guide.md)
- 📖 [Documentation API](./api_documentation.md)
- 📖 [Architecture](./architecture_explanation.md)

---

## ✅ Checklist

- [ ] Django API accessible
- [ ] Node.js API accessible
- [ ] React frontend accessible
- [ ] Template actif dans Django
- [ ] Génération de carte fonctionne
- [ ] Téléchargement PDF fonctionne

---

**Prêt à générer des cartes ! 🎉**
