# 🚀 Titan : Régulation Expert PID

Cette intégration transforme une automatisation complexe de pilotage de batterie en un composant natif Home Assistant. Elle implémente une **régulation PI (Proportionnelle-Intégrale)** réactive pour optimiser l'autoconsommation.

## ✨ Fonctionnalités
- **Régulation PI Asynchrone** : Calcul ultra-rapide basé sur les changements d'état du Shelly.
- **Anti-Injection Réactif** : Vitesse de descente (600W/step) et de montée (2500W/step) asymétrique pour éviter d'injecter sur le réseau.
- **Filtrage Intelligent** : Moyenne glissante sur 2 points pour lisser les pics du Shelly.
- **Zéro Configuration YAML** : Tout se configure via l'interface utilisateur (Config Flow).

## 📂 Structure des fichiers
- `manifest.json` : Identité de l'intégration et dépendances.
- `const.py` : Constantes partagées (DOMAIN).
- `config_flow.py` : Interface de configuration (Choix du Shelly, du Titan et des facteurs P/I).
- `__init__.py` : Cœur de l'algorithme et surveillance des capteurs.
- `switch.py` : Interrupteur pour activer/désactiver le pilotage automatique.

## ⚙️ Installation
1. Copiez le dossier `titan_controller` dans votre dossier `custom_components/`.
2. Redémarrez Home Assistant.
3. Allez dans **Paramètres** > **Appareils et Services**.
4. Cliquez sur **Ajouter l'intégration** et recherchez "Titan : Régulation Master".
5. Sélectionnez votre capteur de puissance Shelly et votre appareil Titan.

## 🧮 Logique de Régulation
L'algorithme vise une puissance réseau de **0W** :
- **Erreur** = (Puissance Shelly filtrée) - 0.
- **Intégrale** = Somme des erreurs (bornée à ±500 pour éviter l'emballement).
- **Correction** = (P * erreur) + (I * intégrale).
- **Consigne** = Limitée à ±4800W.

## 🛠 Maintenance
Pour modifier les paramètres P ou I après l'installation, vous pouvez actuellement supprimer et réinstaller l'intégration (les paramètres sont sauvegardés dans l'UI lors de la configuration).

---
*Développé pour optimiser les performances des batteries Titan avec les compteurs Shelly Pro 3EM.*
