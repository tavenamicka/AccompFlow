# AccompFlow

Application de suivi pour coachs et consultants : gestion des clients, des interventions et des forfaits (paliers N1/N2), alertes de dépassement, rapports PDF/Excel, et portail client dédié (documents, suivi de consommation en temps réel).

> **Statut** : prototype fonctionnel, utilisé en production sur un déploiement personnel. Publié pour être partagé avec la communauté — les retours, issues et PR sont bienvenus.

## Origine du projet

AccompFlow est une **évolution de ForfaitFlow**, qui fusionne son moteur de suivi de forfaits avec un portail client (documents, invitations, jauges de consommation) et y ajoute de nouvelles fonctionnalités : gestion des rôles (owner/staff/client), architecture prête pour du multi-organisation, rapports enrichis, etc.

**ForfaitFlow reste un outil indépendant**, maintenu séparément — AccompFlow n'est pas un remplacement mais un produit distinct qui a repris et étendu son cœur métier.

## Fonctionnalités

- Gestion des clients et de leurs forfaits (paliers N1/N2)
- Suivi des interventions et calcul de consommation par période
- Alertes automatiques de dépassement de forfait
- Descriptions d'intervention multi-ligne (retours à la ligne conservés à l'écran et dans les exports)
- Génération de rapports PDF et Excel
- Portail client : documents partagés, jauges de consommation, invitations par email
- Échéanciers de paiement multiples par client, activables par l'admin
- Date de début de contrat modifiable (les périodes sont recalculées) et email de connexion modifiable par chaque utilisateur
- Authentification par rôles (owner / staff / client)
- Architecture multi-organisation (SaaS-ready)

## Stack technique

- **Backend** : FastAPI (Python), SQLAlchemy + Alembic, PostgreSQL, WeasyPrint (PDF), openpyxl (Excel)
- **Frontend** : Next.js (React, TypeScript), Tailwind CSS
- **Déploiement** : Docker Compose

## Démarrage rapide

```bash
git clone <url-du-repo>
cd AccompFlow
cp .env.example .env
# éditer .env : JWT_SECRET, DB_PASSWORD, ADMIN_EMAIL/ADMIN_PASSWORD au minimum
docker compose up -d --build
```

- Frontend : http://localhost:8102
- Backend / API : http://localhost:8101 (docs interactives sur `/docs` en dev)

Le compte owner est créé via :

```bash
docker compose exec accompflow-backend python -m app.scripts.create_admin
```

Voir [.env.example](.env.example) et [backend/.env.example](backend/.env.example) pour le détail des variables (base de données, JWT, SMTP, CORS, etc.).

## Tests

```bash
# backend
docker compose exec accompflow-backend pytest

# frontend
cd frontend && npm test
```

## Licence

[MIT](LICENSE) — voir le fichier `LICENSE`.
