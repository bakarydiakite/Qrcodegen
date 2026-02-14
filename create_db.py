import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuration de connexion (Utilisateur/Mdp standard de votre Docker)
db_params = {
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

print("Tentative de connexion à PostgreSQL...")

try:
    # Connexion à la base par défaut 'postgres'
    con = psycopg2.connect(dbname='postgres', **db_params)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = con.cursor()
    
    # Vérifier si la base existe déjà
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'cjp_cards_db'")
    exists = cur.fetchone()
    
    if not exists:
        print("Création de la base de données 'cjp_cards_db'...")
        cur.execute("CREATE DATABASE cjp_cards_db;")
        print("✅ Base de données 'cjp_cards_db' créée avec succès !")
    else:
        print("ℹ️ La base de données 'cjp_cards_db' existe déjà.")
        
except Exception as e:
    print(f"❌ Erreur : {e}")
    print("Assurez-vous que votre conteneur Docker PostgreSQL est bien lancé !")
finally:
    if 'con' in locals():
        con.close()
