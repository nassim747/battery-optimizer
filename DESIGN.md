# Document de conception

## Problème

Étant donné un profil de charge sur 24 heures, des prix d'électricité horaires et une batterie avec des contraintes physiques, trouver le plan de charge/décharge qui minimise le coût total d'électricité.

## Pourquoi un MILP

Mon premier réflexe était cette approche : charger pendant les heures pas chères, décharger pendant les heures chères. Ça fonctionne pour des cas simples, mais ça casse dès qu'il faut raisonner sur les contraintes futures du SoC, par exemple, décider si on garde de la charge pour une heure chère plus tard au lieu de décharger maintenant.

La programmation linéaire gère ça naturellement puisqu'elle optimise sur les 24 heures simultanément. J'ai opté pour un LP en nombres mixtes (MILP) spécifiquement à cause de la contrainte « pas de charge et décharge simultanées ». Avec un rendement < 1, un LP pur ne chargerait et déchargerait jamais en même temps (c'est toujours gaspilleur), mais à rendement = 1.0, le LP pourrait retourner des solutions dégénérées où les deux sont non nuls. La variable binaire élimine ce cas limite proprement.

## Formulation

**Variables** : `charge[t]`, `discharge[t]` (continues), `z[t]` (binaire)

**Objectif** :

```
minimiser  Σ  price[t] × (charge[t] - discharge[t])
```

Le coût de la charge de base est constant peu importe la batterie, donc j'optimise seulement le delta.

**Contraintes** :

- `charge[t] ≤ max_charge_kw × z[t]` (charge possible uniquement quand z=1)
- `discharge[t] ≤ max_discharge_kw × (1 - z[t])` (décharge possible uniquement quand z=0)
- `0 ≤ SoC[t] ≤ capacity_kwh` où le SoC s'accumule comme `soc_initial + Σ(charge×η - discharge)`

## Modèle de rendement

J'applique le rendement du côté de la charge : `énergie_stockée = charge_kw × η`. La décharge est sans perte en sortie. C'est une convention à un seul η, simple à comprendre, et ça correspond à la façon dont la plupart des fiches techniques de batteries présentent les pertes aller-retour. Un modèle à deux η (rendements de charge/décharge séparés) serait une extension directe, mais j'ai gardé ça simple ici.

## Choix du solveur

PuLP avec CBC. C'est open-source, livré avec PuLP (pas d'installation externe nécessaire sur la plupart des systèmes), et résout un MILP à 24 variables en moins de 100 ms. J'ai considéré Google OR-Tools, mais PuLP est plus léger et CBC est amplement suffisant pour cette taille de problème.

## Conception de l'API

**FastAPI** était le choix évident pour une API Python qui a besoin de docs OpenAPI auto-générées. Pydantic gère la validation des entrées (exactement 24 valeurs, rendement dans (0,1], SoC dans la capacité) pour que l'optimiseur ne reçoive que des entrées valides.

J'ai séparé `/optimize` et `/visualize` intentionnellement. Un client headless (pipeline CI, autre service) n'a besoin que du planning brut de `/optimize`. Le frontend a besoin des traces formatées pour Plotly de `/visualize`. Les deux exécutent le même solveur  `/visualize` ajoute juste le formatage par-dessus.

## Authentification et limitation de débit

Clé API via le header `x-api-key`, validée contre un ensemble chargé depuis la variable d'environnement `API_KEYS`. Simple, sans état, facile à renouveler.

La limitation de débit est une fenêtre glissante en mémoire par clé. Je conserve les timestamps des requêtes récentes et j'élimine tout ce qui a plus de 60 secondes. Ça fonctionne bien pour un déploiement mono-processus. La limitation évidente : ça ne fonctionne pas entre plusieurs workers ou conteneurs, il faudrait Redis pour ça. J'ai jugé que la complexité n'en valait pas la peine pour cette portée.

## Frontend

React avec `useReducer` pour la gestion d'état. L'application a quatre états : idle, loading, success, error. Je n'ai pas utilisé Redux ou Zustand parce qu'il y a un seul flux de données (formulaire → appel API → affichage des résultats) et useReducer gère ça correctement.

Les traces Plotly arrivent pré-formatées du backend, donc le frontend les passe directement à `react-plotly.js` telles quelles. J'ai utilisé `plotly.js-dist-min` pour garder le bundle plus petit puisque je n'ai besoin que de types de graphiques de base.

Le style est en objets CSS inline. J'utiliserais normalement Tailwind, mais je voulais garder le setup minimal et éviter d'ajouter une étape de build CSS pour ce qui est essentiellement un outil d'une seule page.

## Ce que je changerais avec plus de temps

- **Limitation de débit persistante** : basée sur Redis au lieu de la mémoire
- **Gestion des clés** : base de données ou gestionnaire de secrets au lieu de variables d'env
- **Solveur asynchrone** : pour du trafic élevé, exécuter l'optimiseur dans un worker Celery
- **Rendement bidirectionnel** : η_charge et η_discharge séparés
- **Contrainte d'export réseau** : option pour empêcher net_load < 0 (batterie qui réinjecte dans le réseau)
- **Frontend** : layout responsive, squelette de chargement, menu déroulant de presets

