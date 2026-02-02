# 🚀 Secure Deployment Guide

Ce guide détaille comment déployer ELK dans un environnement de production sécurisé.

## 1. Pré-requis Sécurité
- Ne jamais utiliser de clés API par défaut en production.
- Utiliser un certificat TLS (HTTPS) via un reverse-proxy (Nginx, Traefik).
- Isoler le réseau Redis pour qu'il ne soit accessible que par l'API et les Workers.

## 2. Configuration Environnement
Copiez le fichier d'exemple et générez des secrets forts :
```bash
cp .env.example .env
# Génération d'une clé API forte
openssl rand -base64 32 > .env (ajouter à API_KEY)
```

## 3. Déploiement Docker
Lancer le cluster ELK en mode détaché :
```bash
docker-compose up -d --build
```

### Vérifier le durcissement du conteneur
Vérifiez que l'application ne tourne pas en root :
```bash
docker exec -it elk_api whoami
# Résultat attendu : elkuser
```

## 4. Maintenance
- **Rotation des Logs** : Les logs sont configurés pour tourner quotidiennement.
- **Auto-Cleanup** : Le système purge les fichiers audio plus vieux que `UPLOAD_TTL_SECONDS` (86400s par défaut).

## 5. Monitoring
Surveillez le endpoint `http://localhost:8000/health` pour vérifier l'état des dépendances (Redis/DB).
