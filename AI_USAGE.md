# Utilisation de l'IA

J'ai utilisé Cursor avec Claude comme assistant de programmation tout au long de ce projet. Voici un portrait honnête de ce qu'il a aidé à faire et de ce que j'ai fait moi-même.

## Où l'IA a aidé

**Boilerplate et structure initiale** : j'ai fait générer par l'IA la structure du projet FastAPI, les définitions des modèles Pydantic et le Dockerfile. Ce sont des choses que j'ai écrites plusieurs fois auparavant, l'IA a juste accéléré le processus. J'ai revu le résultat et ajusté les contraintes de champs (ex : rendre le rendement `gt=0, le=1` au lieu de `ge=0`).

**Configuration Plotly** : j'ai décrit ce que je voulais (barres pour la charge, ligne pour le SoC, thème sombre) et l'IA a généré les objets traces/layout Plotly. L'API de Plotly est verbeuse et je finis toujours par consulter la doc de toute façon, donc ça m'a fait gagner du temps réel. J'ai ajusté les couleurs et les étiquettes d'axes après avoir vu le premier rendu.

**Structure des composants React** : l'IA a créé le layout des composants (formulaire en sidebar + zone de graphiques principale) et le CSS inline. J'ai restructuré la gestion d'état pour utiliser `useReducer` après que la version initiale utilisait du simple `useState`, parce que je voulais des transitions d'état explicites.

**Docker et configuration de déploiement** : Dockerfile, docker-compose et fichiers de configuration Railway/Vercel. J'ai rencontré des problèmes de build sur Railway (Nixpacks ne trouvait pas pip, liaison de port) qui ont nécessité quelques itérations pour être résolus.

**Structure des tests** : l'IA a généré la structure initiale du fichier de tests. J'ai ajouté des cas de test spécifiques pour les conditions limites (bornes du SoC, charge/décharge simultanée, rendement = 1.0).

## Ce que j'ai fait moi-même

**Le modèle d'optimisation** : j'ai formulé le MILP à partir de zéro. Les décisions clés comme utiliser une variable binaire pour l'exclusion mutuelle, appliquer le rendement uniquement du côté de la charge, exprimer le SoC comme des sommes cumulatives etc sont les miennes. J'ai vérifié la formulation à la main sur un exemple de 3 heures avant de passer à 24.

**Validation mathématique** : j'ai exécuté le scénario par défaut et vérifié que l'optimiseur charge pendant les heures creuses (00:00-05:00 à 0,06 $/kWh) et décharge pendant la pointe du soir (17:00-19:00 à 0,25-0,28 $/kWh). J'ai aussi vérifié les cas limites : batterie partant à 0 de SoC, tarification plate (ne devrait produire aucune action), et rendement = 1.0.

**Décisions de conception** : le choix du MILP par rapport au glouton, la séparation entre `/optimize` et `/visualize`, le compromis du limiteur de débit en mémoire, ce sont des décisions que j'ai raisonnées et que je peux défendre. Voir DESIGN.md.

**Débogage du déploiement** : les déploiements Railway et Vercel ont nécessité plusieurs étapes de dépannage (liaison de port, CORS, variables d'environnement) que j'ai résolues de manière itérative.

**Revue de code** : j'ai lu chaque fichier généré par l'IA, supprimé les commentaires inutiles et vérifié que l'implémentation des contraintes correspond à la formulation mathématique dans DESIGN.md.

## Résumé

L'IA a surtout été un outil de productivité ici. Elle a tapé plus vite que je ne l'aurais fait, surtout pour les parties lourdes en boilerplate. Le raisonnement mathématique, les décisions architecturales et la validation ont été faits par moi. Je suis à l'aise pour expliquer et défendre n'importe quelle partie du code.