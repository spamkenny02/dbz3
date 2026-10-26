# Atelier scénario — graphismes v8

Les décors et les personnages placés dans l'éditeur sont maintenant convertis
et intégrés dans les scènes de la ROM, avec position, taille, miroir et ordre
des calques. Ils restent fixes pendant chaque page de dialogue.

## Windows

Installez les dépendances puis lancez le BAT :

```
py -3 -m pip install -r requirements.txt
```

Copiez votre dossier `assets/` existant à côté de `app.py`, puis ouvrez votre
projet JSON dans l'éditeur. Si le projet a changé de dossier, chargez son
catalogue et enregistrez-le. `prelude_decor13.json` est un exemple avec le
fond « Décor scène 13 » sur les deux premières scènes ; il nécessite le
catalogue SB2 précédemment extrait.

## Composer et exporter

- Double-cliquez un décor pour l'appliquer à la scène, ou un personnage pour
  ajouter un calque. Déplacez-le et réglez X/Y, taille, miroir et calque.
- Écrivez les dialogues, créez les choix et leurs destinations. Le texte est
  paginé lors de l'export ; les titres et panneaux couvrent une partie du décor.
- Pour un combat, définissez les deux combattants, la possibilité de choisir
  son personnage, l'arène et les suites victoire/défaite.
- Enregistrez votre JSON. `Tester depuis le début` simule les parcours locaux.
- `Construire ROM / IPS` demande votre ROM française originale de 2 Mio et un
  nouveau nom de sortie. Il exporte les compositions et les vrais combats.
  Le message final indique le nombre d'écrans graphiques et de palettes réduites.

La ROM reste à 4 Mio et n'utilise pas de SRAM. L'intro Goku/Vegeta et les modes
natifs restent présents. Le décor narratif choisi ne remplace pas l'arène du
combat. Les changements ne s'appliquent pas aux anciennes ROMs déjà générées :
il faut construire une nouvelle sortie et redémarrer sans ancien état émulateur.

## Limites

Maximum 256 couleurs RGB555 par écran composé. Les couleurs sont préservées
si elles tiennent ; sinon une réduction sans tramage est signalée. Si la ROM
ou la banque de code n'a plus assez de place, la construction échoue clairement.
Les accents sont encore translittérés dans la police prototype de la ROM.

Le catalogue extrait couvre 31 compositions de décor et 35 éléments transparents
issus de 222 identifiants de scène SB2 validés. Certains personnages superposés
restent groupés ; les images ne constituent pas un catalogue complet d'animations.
Il peut manquer des personnages et poses propres à la saga Buu.

Le nouveau GUI et l'export ont été testés sous Linux/Tk. Le lancement Windows
avait été confirmé pour les versions précédentes ; cette mise à jour reste à
tester sous Windows. Voir `GRAPHIQUES_V8.md` dans le ZIP pour les détails.
