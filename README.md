# Trouve ton Master — Outil d'orientation L3 → Master, Application Streamlit

## Ce que c'est

Une application Streamlit complète qui pose le questionnaire d'orientation,
calcule le score en utilisant exactement le barème de
`Base_Donnees_Questionnaire_Complete_V2.xlsx`, et affiche le top 3 des
masters recommandés avec leurs débouchés (jamais le taux d'insertion ni le
salaire, conformément à la décision de conception).

## Nouveautés de cette version

- **Ouvert aux L1, L2 et L3**, et aux étudiants d'une autre université que
  Rennes 1 (avec une question de licence précise posée uniquement pour les
  étudiants de Rennes 1).
- **Traitement différencié de « Jamais suivi »** : neutre pour un étudiant de
  L1/L2 (qui n'a structurellement pas encore rencontré la matière), léger
  malus conservé pour un L3.
- **Module « Je ne sais pas »** : un étudiant indécis à la question du domaine
  répond à 8 questions générales, puis voit un classement des 6 domaines, du
  plus proche au moins proche de ses réponses, et choisit librement par lequel
  commencer.
- **Nouvel habillage visuel** : palette dédiée (encre/pin/or), typographies
  Fraunces (titres) et Public Sans (texte), cartes de résultat, curseurs et
  barre de progression stylés.

## Comment la lancer sur ton ordinateur

1. Installer Python (3.9 ou plus récent) si ce n'est pas déjà fait.
2. Ouvrir un terminal dans ce dossier (celui qui contient `app.py`).
3. Installer les dépendances :
   ```
   pip install -r requirements.txt
   ```
4. Lancer l'application :
   ```
   streamlit run app.py
   ```
5. Une page va s'ouvrir automatiquement dans ton navigateur (sinon, l'adresse
   s'affiche dans le terminal, généralement `http://localhost:8501`).

## Important

- Le fichier `Base_Donnees_Questionnaire_Complete_V2.xlsx` doit rester dans le
  même dossier que `app.py` — c'est lui qui contient toutes les questions et
  le barème du questionnaire principal (80 questions, 6 destinations). Si tu
  modifies les questions dans ce fichier Excel, l'application les reflètera
  automatiquement au prochain lancement.
- Les 8 questions du module « Je ne sais pas » sont, elles, directement dans
  `app.py` (variable `JNS_QUESTIONS`) : elles ne portent pas sur un master en
  particulier mais sur une famille entière, donc elles n'ont pas leur place
  dans les mêmes feuilles Excel que le reste du barème.
- Testée avec succès en local (démarrage sans erreur, calculs vérifiés).

## Ce qui n'est pas encore fait

- Sauvegarde des réponses des étudiants (actuellement, rien n'est enregistré :
  chaque passage est indépendant).
- Version en ligne accessible sans installation (actuellement, il faut lancer
  l'app soi-même en local ; hébergement gratuit envisagé via Streamlit
  Community Cloud).
