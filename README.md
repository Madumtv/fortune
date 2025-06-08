# fortune
🪙 Estimation Fortune & Bio Personnalités – MegaGPT
Application Python permettant d’estimer la fortune d’une personnalité (sport, politique, célébrité, etc.) à partir de plusieurs sources web et d’afficher automatiquement :

La fortune estimée (calculée et recoupée sur différentes sources en ligne)

Le niveau de fiabilité de l’estimation (badge/couleur selon nombre de sources)

La biographie et la photo officielle (directement extraites de Wikipédia en français)

Les sources utilisées (liens cliquables pour transparence)

Lien Wikipédia direct

Copie rapide des résultats au presse-papier

✨ Fonctionnalités
Recherche automatique de la fortune via DuckDuckGo : parsing de pages, détection de montants, filtrage par pertinence du nom.

Calcul d’un indicateur de fiabilité selon le nombre et la cohérence des sources.

Extraction de la bio, photo et lien officiel via l’API Wikipédia (français).

Interface graphique moderne (Tkinter + Pillow), intuitive et responsive.

Possibilité d’afficher les sources utilisées, de copier le résultat, et d’ouvrir la fiche Wikipédia.

Résultat affiché en couleur selon la fiabilité :

🟢 : estimation fiable

🟠 : à prendre avec prudence

🔴 : estimation peu ou pas fiable

🛠️ Installation
Cloner le dépôt :

bash
Copier
Modifier
git clone https://github.com/votre-repo/fortune-bio-app.git
cd fortune-bio-app
Installer les dépendances :

bash
Copier
Modifier
pip install duckduckgo-search pillow requests beautifulsoup4
Lancer l’application :

bash
Copier
Modifier
python fortune_bio.py
🪟 Version Windows précompilée
Un exécutable .exe Windows prêt à l’emploi est disponible dans la section Releases du dépôt.
Aucun besoin d’installer Python ni les dépendances : il suffit de lancer le fichier téléchargé.

Idéal pour les utilisateurs non développeurs souhaitant tester l’application immédiatement.

💡 Technos utilisées
Python 3.8+

Tkinter (UI)

Pillow (affichage images)

requests, beautifulsoup4 (scraping web)

duckduckgo-search (recherche intelligente)

API Wikipédia (récupération bio et photo)

⚠️ Limites et précision
L’outil ne peut garantir l’exactitude absolue des fortunes détectées. Les chiffres proviennent de sources publiques parfois peu rigoureuses : l’indicateur de fiabilité est là pour informer l’utilisateur.

Les résultats sont purement informatifs et ne doivent pas servir à des fins juridiques ou financières.

📦 Compilation .exe
Peut être transformé en exécutable Windows avec auto-py-to-exe.

Possibilité de personnaliser l’icône de l’application.

Un fichier .exe prêt à l’emploi est déjà fourni dans les releases.

📝 Licence
MIT License
