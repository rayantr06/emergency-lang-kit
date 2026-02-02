# 🛡️ Hardening Report: ELK (Emergency Lang Kit)

Ce rapport détaille les mesures de durcissement technique implémentées suite à l'audit de sécurité "Adversarial". L'objectif est de garantir que le noyau ELK peut opérer dans des environnements haute-disponibilité et critiques.

## 1. Sécurité de l'API (Gateway)

### Authentification
- **Mécanisme** : Implémentation d'un middleware propriétaire `APIKeyMiddleware`.
- **Enforcement** : Tous les endpoints (sauf `/health` et `/metrics`) exigent un header `X-API-Key`.
- **Protection contre les fuites** : Les exceptions d'authentification sont interceptées pour éviter de révéler des traces système (retour synchrone JSON).

### Contrôle d'Accès & Réseau
- **CORS** : Configuration restrictive via `ALLOWED_ORIGINS` dans `config.py`.
- **Trusted Host** : Validation automatique du header `Host` via `ALLOWED_HOSTS`.
- **Injection Audio** : Validation systématique du header MIME et de l'intégrité Base64 avant écriture disque.

## 2. Résilience & Antifragilité (Backpressure)

En cas de pic d'appels (ex: catastrophe naturelle localisée), le système doit rester stable sans saturer les workers.

- **Queue Depth Limiter** : Avant d'accepter un nouveau job, l'API interroge Redis (`llen`). Si la file dépasse `MAX_QUEUE_SIZE`, l'API retourne un code **429 Too Many Requests**.
- **Timeouts Stricts** : Limitation des opérations Redis à `QUEUE_OP_TIMEOUT` (2s) pour éviter les blocages en cascade.
- **Background Cleanup** : Le nettoyage des fichiers uploads (`_cleanup_old_uploads`) a été déporté dans des `BackgroundTasks` FastAPI pour minimiser la latence d'ingestion.

## 3. Traçabilité & Observabilité

- **Correlation ID** : Un `correlation_id` est généré/propagé dès l'entrée API et voyage jusqu'au connector final (ERP).
- **Health Check étendu** : Le endpoint `/health` vérifie désormais la connectivité active vers Redis et la Base de Données.

## 4. Infrastructure & DevOps

- **Non-Root Execution** : Le `Dockerfile` a été durci. L'application s'exécute désormais sous l'utilisateur `elkuser` (UID non-privilégié).
- **Principle of Least Privilege** : Les permissions sur le répertoire `/tmp/elk/uploads` sont restreintes.

---
**Verdict Audit : CONFORME**
