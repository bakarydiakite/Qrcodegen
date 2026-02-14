@echo off
chcp 65001 > nul
echo ===================================================
echo     MIGRATION DU GENERATEUR VERS POSTGRESQL
echo ===================================================
echo.

echo 1. Installation des dépendances (Django, psycopg2, etc.)...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors de l'installation des dépendances.
    pause
    exit /b
)
echo.

echo 2. Création de la base de données 'cjp_cards_db'...
python create_db.py
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors de la création de la base.
    pause
    exit /b
)
echo.

echo 3. Installation des tables Django dans PostgreSQL...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors des migrations. Vérifiez que Postgres tourne bien.
    pause
    exit /b
)

echo.
echo ===================================================
echo ✅ SUCCES ! VOTRE GENERATEUR EST MAINTENANT SUR POSTGRESQL
echo ===================================================
echo.
echo Vous pouvez maintenant relancer le serveur avec :
echo python manage.py runserver
echo.
pause
