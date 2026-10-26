# DBZ3 — première scène, présentation SB2 (v9)

La v9 se concentre sur l'entraînement Gohan/Goten : décor SB2 et fond violet,
apparitions successives, police française originale, texte progressif, musique
SB2 sélectionnable, choix du combattant et retour après victoire/défaite.
L'intro Goku/Vegeta et les modes natifs SB3 sont conservés. Aucune SRAM.

- [Télécharger l'atelier première scène SB2 v9](releases/Atelier_Premiere_Scene_SB2_v9.zip)
- [Installation, détails et limites](docs/first-scene-sb2-v9.md)
- [Résultats des essais](docs/first-scene-sb2-v9-runtime.json)

Décompressez dans un nouveau dossier et copiez votre dossier `assets/` existant
à côté de `app.py`. Installez les dépendances puis lancez le BAT :

```
py -3 -m pip install -r requirements.txt
```

Cliquez **Créer la première scène SB2**. Choisissez les deux ROMs françaises
originales de 2 Mio (SB2 La Légende Saien, puis SB3 Ultime Menace), et enregistrez
le nouveau projet JSON. Sélectionnez une piste SB2, enregistrez, puis construisez
la ROM avec la ROM SB3 originale sous un nouveau nom. Démarrez sans ancien état
émulateur. Il n'est pas nécessaire d'installer un émulateur pour préparer/exporter.

Le décor 13 d'origine est une bande centrale sur un fond violet dégradé. Les
personnages ont des poses fixes ; Gohan vient du catalogue SB2 et Goten de SB3,
en Super Saiyan. La musique SB2 est remplacée par le pilote SB3 avant le combat,
puis rechargée pour la réplique de résultat. Le combat utilise encore la plaine
rocheuse native. Les pistes 4 et 5 ont été vérifiées en jeu ; les autres numéros
extraits n'ont pas chacun fait l'objet d'un parcours complet.

Les sources de la v8 et son exemple de campagne restent disponibles. Le lecteur
local de l'éditeur simule le scénario ; il ne joue pas la musique ni le combat.
Les ROMs, polices et musiques extraites restent privées. Le ZIP contient les
outils d'extraction et de construction, sans ROM ni ressources commerciales.

