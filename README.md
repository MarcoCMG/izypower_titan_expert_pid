# 🚀 Titan : Régulation Expert PID (v2.0)

Cette intégration remplace le pilotage automatique logiciel (soft) standard de l'Izypower Titan par un **moteur de régulation PID de précision**. Elle transforme votre batterie en un système ultra-réactif, capable de s'adapter à n'importe quel Smart Meter compatible avec Home Assistant.

## 🏆 Pourquoi choisir la Régulation Expert ?

L'algorithme interne d'origine du Titan peut s'avérer lent ou sujet à des oscillations (pompage). Cette version "Expert" apporte des améliorations majeures :

### 1. Compatibilité Universelle (Smart Meter Agnostic)
L'intégration utilise l'abstraction de Home Assistant pour piloter la batterie à partir de **n'importe quel capteur de puissance** déclaré :
* **Shelly** (EM, Pro 3EM, 1PM).
* **ZLinky / TIC** (Linky Zigbee).
* **Enphase, SolarEdge, Fronius** (Passerelles PV).
* **ESPHome**, **RT2**, ou tout autre compteur fournissant une mesure en Watts.

### 2. Précision PID + Terme Dérivé (D)
L'ajout du terme **Dérivé** agit comme un amortisseur intelligent. Il calcule la vitesse de variation de votre consommation pour "freiner" la puissance de la batterie avant qu'elle ne dépasse sa cible, éliminant ainsi les dépassements (overshoot).



### 3. Asymétrie Inversée & Priorité "Zéro Conso"
Le moteur gère la puissance de manière asymétrique pour coller à la réalité de votre facture :
* **Réaction Éclair (2500W/step) :** Pour compenser instantanément le démarrage d'un appareil.
* **Retrait Doux (400W/step) :** Pour réduire la puissance lentement et rester le plus proche possible du 0W réseau.

## ⚠️ Prérequis Indispensable

Cette intégration est une **extension avancée** qui pilote le driver de communication.
* **Dépendance :** Vous devez avoir installé au préalable l'intégration [izypower_titan_private](https://github.com/Charmg31/izypower_titan_private).
* **Fonctionnement :** L'Expert PID utilise les services `charge`, `discharge` et `stop` fournis par ce driver.

## ⚙️ Installation

### Option A : Via HACS (Recommandé) ⚡
1. Ouvrez **HACS** dans Home Assistant.
2. Cliquez sur les trois points en haut à droite et choisissez **Dépôts personnalisés**.
3. Ajoutez l'URL de ce dépôt GitHub.
4. Sélectionnez la catégorie **Intégration** et cliquez sur **Ajouter**.
5. Recherchez **Titan : Régulation Expert PID** et installez-le.

### Option B : Installation Manuelle
1. Téléchargez le dossier `titan_controller`.
2. Copiez-le dans votre répertoire `custom_components/`.
3. Redémarrez Home Assistant.

## 🚀 Configuration finale
1. Allez dans **Paramètres > Appareils et Services > Ajouter l'intégration**.
2. Recherchez **"Titan : Régulation Expert PID"**.
3. Sélectionnez votre **Smart Meter**, votre **Titan** et votre **Profil de régulation**.

## 📊 Profils de Régulation
| Profil | Cible Réseau | Philosophie |
| :--- | :--- | :--- |
| **Performance** | **-25W** | Priorité Facture 0€ (Légère injection pour garantir 0 conso). |
| **Équilibré** | **0W** | Le compromis idéal pour la stabilité. |
| **Eco** | **+15W** | Priorité Anti-Injection (Marge de sécurité réseau). |

## 🛠 Diagnostics Intégrés
L'intégration crée un appareil regroupant :
* **Puissance Cible (Sensor) :** Puissance demandée en temps réel au Titan.
* **Erreur Réseau (Sensor) :** Écart entre conso réelle et cible.
* **Pilotage Auto (Switch) :** Interrupteur maître. *L'extinction envoie un ordre d'arrêt (`stop`) immédiat et réinitialise les calculs.*

---
*Optimisez votre Izypower Titan avec la précision du PID (v2.0 - 30/12/2025).*
