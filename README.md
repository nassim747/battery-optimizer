# API d'optimisation de batterie

Un microservice qui planifie la charge/décharge d'une batterie sur 24 heures pour minimiser le coût d'électricité, accompagné d'un tableau de bord React pour la visualisation.

## Déploiement en ligne

- **Frontend** : https://battery-optimizer-iota.vercel.app
- **Backend API** : https://battery-optimizer-api-production-d051.up.railway.app
- **Documentation API (Swagger)** : https://battery-optimizer-api-production-d051.up.railway.app/docs
- **Clé API pour le relecteur** : `dev-key-abc123`

## Structure du projet

```
backend/
  main.py             App FastAPI, auth, limitation de débit, journalisation
  optimizer.py         Solveur MILP (PuLP + CBC)
  models.py            Schémas Pydantic
  tests/               Suite pytest
  Dockerfile
  requirements.txt

frontend/
  src/
    App.tsx            Mise en page principale
    api.ts             Client API
    types.ts           Interfaces TypeScript
    hooks/             useOptimizer (machine d'état useReducer)
    components/        InputForm, ChartPanel, SummaryCard
  Dockerfile
  package.json
```

## Exécution locale

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

L'API sera sur http://localhost:8000. Documentation interactive sur http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

S'ouvre sur http://localhost:5173. Le serveur Vite proxy `/api` vers `localhost:8000`.

### Docker

```bash
docker compose up --build
# Backend  → http://localhost:8000
# Frontend → http://localhost:3000
```

## Utilisation de l'API

Tous les endpoints sauf `/health` exigent le header `x-api-key`.

```bash
# Vérification de santé
curl http://localhost:8000/health

# Lancer une optimisation
curl -X POST http://localhost:8000/optimize \
  -H "x-api-key: dev-key-abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "load_kwh": [0.4,0.3,0.3,0.3,0.4,0.6,1.2,1.5,1.3,1.0,0.9,0.8,0.9,0.8,0.8,1.0,1.4,2.0,2.5,2.2,1.8,1.4,1.0,0.6],
    "price_per_kwh": [0.06,0.06,0.06,0.06,0.06,0.08,0.12,0.18,0.20,0.18,0.15,0.14,0.14,0.13,0.14,0.16,0.20,0.25,0.28,0.26,0.22,0.18,0.12,0.08],
    "battery": {
      "capacity_kwh": 10,
      "max_charge_kw": 3,
      "max_discharge_kw": 3,
      "efficiency": 0.92,
      "initial_soc_kwh": 2
    }
  }'
```

## Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `API_KEYS` | `dev-key-abc123,test-key-xyz789` | Clés valides, séparées par virgule |
| `RATE_LIMIT_PER_MINUTE` | `30` | Requêtes/min par clé |
| `LOG_LEVEL` | `INFO` | Niveau de journalisation Python |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | Origines CORS |
| `VITE_API_URL` | `http://localhost:8000` | URL du backend (frontend, build-time) |
| `VITE_API_KEY` | `dev-key-abc123` | Clé API (frontend, build-time) |

## Tests

```bash
cd backend
pip install pytest httpx
pytest tests/ -v
```

21 tests couvrant la justesse de l'optimiseur, la validation des contraintes, l'authentification, la limitation de débit et les réponses des endpoints.

## Déploiement

- **Backend** : Railway (build Docker, déploiement auto sur push)
- **Frontend** : Vercel (build Vite, répertoire racine = `frontend`)

Pour un nouveau déploiement, configurer `API_KEYS` et `ALLOWED_ORIGINS` dans Railway, `VITE_API_URL` et `VITE_API_KEY` dans Vercel, puis pousser sur main.
