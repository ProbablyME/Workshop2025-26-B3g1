# WAVE-CONNECT 

## Contenu du Projet

### Applications Windows
- `WAVE_Connect_Gov.exe` - Interface gouvernementale d'émission d'alertes
- `WAVE_Recepteur.exe` - Interface de réception et monitoring des alertes

### Code Arduino/ESP8266
- `transmetteur.cpp` - Code pour ESP8266 émetteur (avec lecteur RFID)
- `recepteur.cpp` - Code pour ESP8266 récepteur (avec LED d'alerte)

### Code Source Python
- `wave_connect_gov.py` - Source de l'interface gouvernementale
- `wave_recepteur.py` - Source de l'interface de réception

## Installation et Configuration

### 1. Matériel utilisé

#### ESP8266 Émetteur 
```
Composants requis:
├── ESP8266
├── Module RFID RC522
├── Module émetteur 433MHz
├── LEDs 
└── Cartes RFID d'autorisation
```

#### ESP8266 Récepteur 
```
Composants requis:
├── ESP8266
├── Module récepteur 433MHz
└── LED d'alerte 
└── Buzzer
```

### 2. Installation Arduino/ESP8266

#### Étape 1: Installation IDE Arduino
1. Téléchargez [Arduino IDE](https://www.arduino.cc/en/software)
2. Installez le support ESP8266 :
   - `Fichier` → `Préférences`
   - URL de gestionnaire : `http://arduino.esp8266.com/stable/package_esp8266com_index.json`
   - `Outils` → `Type de carte` → `Gestionnaire de cartes`
   - Recherchez "ESP8266" et installez

#### Étape 2: Installation des bibliothèques
Dans l'IDE Arduino : `Outils` → `Gérer les bibliothèques`

Installez ces bibliothèques :
```
- MFRC522 (pour RFID)
- RCSwitch (pour 433MHz)
```

#### Étape 3: Configuration ESP8266 Émetteur
1. Ouvrez `transmetteur.cpp` dans Arduino IDE
2. **Configurez les UIDs autorisés** (ligne 20-23) :
   ```cpp
   byte authorizedUIDs[][4] = {
     {0xC0, 0xA9, 0x72, 0xA3},  // Remplacez par votre carte 1
     {0x0B, 0xE6, 0x8C, 0x33}   // Remplacez par votre carte 2
   };
   ```
3. Sélectionnez votre carte ESP8266 et le port COM
4. Uploadez le code

#### Étape 4: Configuration ESP8266 Récepteur
1. Ouvrez `recepteur.cpp` dans Arduino IDE
2. Sélectionnez votre carte ESP8266 et le port COM
3. Uploadez le code

### 3. Installation des Applications 

#### Interface Emetteur
1. **Copiez** `WAVE_Connect_Gov.exe` 
2. **Connectez** l'ESP8266 émetteur en USB
3. **Lancez** `WAVE_Connect_Gov.exe`
4. **Configurez** le port COM (ex: COM4) selon le port USB branché
5. **Testez** la connexion avec le bouton "TESTER CONNEXION"

#### Interface Récepteur
1. **Copiez** `WAVE_Recepteur.exe` 
2. **Connectez** l'ESP8266 récepteur en USB
3. **Lancez** `WAVE_Recepteur.exe`
4. **Configurez** le port COM (ex: COM8)
5. **Connectez** pour commencer la surveillance

## Utilisation

### Émission d'Alerte
1. **Connectez-vous** au système via l'interface
2. **Rédigez** votre message d'alerte (max 50 caractères)
3. **Cliquez** sur "ÉTABLIR MESSAGE ET ATTENDRE CARTE"
4. **Passez** votre carte RFID autorisée sur le lecteur
5. **Succès** : Message "CARTE VALIDÉE - MESSAGE ENVOYÉ"
6. **Échec** : Message "CARTE REFUSÉE"

### Réception d'Alerte
1. **Surveillez** l'interface de réception
2. **Alerte reçue** :
   - LED clignote sur l'ESP8266
   - Message apparaît avec alerte dans la liste
   - Son d'alerte
3. **Lecture du message** :
   - Sélectionnez le message dans la liste
   - Cliquez "STOP ALERTE"
   - LED s'arrête de clignoter
   - Message passe à "alerte arrêtée"
