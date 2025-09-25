#include <RCSwitch.h>

// ===== LED =====
#define LED_GREEN 5   // D1 = GPIO5 sur ESP8266

// ===== BUZZER =====
#define BUZZER_PIN 14 // D5 = GPIO14 sur ESP8266

RCSwitch mySwitch = RCSwitch();

// Buffer pour reconstituer les messages personnalisés
String messageBuffer = "";
int expectedLength = 0;
bool receivingMessage = false;
unsigned long lastPacketTime = 0;
bool ledState = LOW;
const unsigned long BLINK_INTERVAL = 100; // Intervalle de clignotement en ms

// Variables pour gestion des alertes
bool alertActive = false; // Indique si une alerte est en cours
String lastMessage = "";  // Stocke le dernier message reçu

// ⭐ NOUVELLE VARIABLE POUR CONTRÔLE DU SON ⭐
bool soundEnabled = true; // Contrôle global du son

// Variables pour la déduplication
unsigned long lastReceivedCode = 0;
unsigned long lastCodeTime = 0;
const unsigned long DUPLICATE_DELAY_MS = 200;

// ===== VARIABLES POUR ALERTE SONORE NUCLÉAIRE =====
unsigned long lastSoundChange = 0;
int currentTone = 0;
bool soundState = false;

// Séquence d'alerte nucléaire (fréquences en Hz)
const int NUCLEAR_TONES[] = {200, 300, 400, 500, 600, 700, 800, 900, 1000, 900, 800, 700, 600, 500, 400, 300};
const int NUM_TONES = sizeof(NUCLEAR_TONES) / sizeof(NUCLEAR_TONES[0]);
const unsigned long TONE_DURATION = 150; // Durée de chaque ton en ms

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Récepteur 433MHz Messages Personnalisés ===");
  Serial.println("DEBUG: Initialisation du récepteur...");

  // Configuration de la LED
  pinMode(LED_GREEN, OUTPUT);
  digitalWrite(LED_GREEN, LOW);
  Serial.println("DEBUG: LED verte initialisée (D1/GPIO5)");

  // Configuration du BUZZER
  Serial.println("DEBUG: Buzzer initialisé (D5/GPIO14)");

  mySwitch.enableReceive(4);  // D2 = GPIO4

  Serial.println("DEBUG: Récepteur configuré sur GPIO4");
  Serial.println("DEBUG: Récepteur prêt. En attente de messages personnalisés...");
  Serial.println("🔧 COMMANDES DISPONIBLES:");
  Serial.println("   - 'stopalert' : Arrêter l'alerte LED + SON");
  Serial.println("   - 'soundon'   : ⭐ ACTIVER le son");
  Serial.println("   - 'soundoff'  : ⭐ DÉSACTIVER le son");
  Serial.println("   - 'status'    : Vérifier l'état");
  Serial.println("   - 'help'      : Afficher l'aide");
  Serial.println("   - 'testsound' : Tester le son d'alerte\n");

  // Test rapide du buzzer au démarrage (si son activé)
  if (soundEnabled) {
    Serial.println("🔊 Test du buzzer...");
    playStartupSound();
  } else {
    Serial.println("🔇 Buzzer désactivé au démarrage");
  }
}

void loop() {
  // Gestion du clignotement de la LED ET du son d'alerte
  if (alertActive) {
    unsigned long currentTime = millis();
    
    // Clignotement LED
    static unsigned long lastBlinkTime = 0;
    if (currentTime - lastBlinkTime >= BLINK_INTERVAL) {
      ledState = !ledState;
      digitalWrite(LED_GREEN, ledState);
      lastBlinkTime = currentTime;
    }

    // ⭐ SON D'ALERTE NUCLÉAIRE CONTINU (SEULEMENT SI ACTIVÉ) ⭐
    if (soundEnabled) {
      playNuclearAlert();
    }
    
  } else {
    digitalWrite(LED_GREEN, LOW);
    if (soundEnabled) {
      noTone(BUZZER_PIN); // Arrêter le son seulement si il était activé
    }
  }

  // Timeout pour réinitialiser si on ne reçoit pas de paquet pendant 10 secondes
  if (receivingMessage && (millis() - lastPacketTime > 10000)) {
    Serial.println("DEBUG: Timeout - Réinitialisation du buffer");
    resetMessageBuffer();
  }

  // Traitement des commandes du terminal
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    command.toLowerCase();
    processTerminalCommand(command);
  }

  if (mySwitch.available()) {
    unsigned long code = mySwitch.getReceivedValue();
    int bitLength = mySwitch.getReceivedBitlength();

    // Déduplication
    unsigned long currentTime = millis();
    if (code == lastReceivedCode &&
        (currentTime - lastCodeTime) < DUPLICATE_DELAY_MS) {
      mySwitch.resetAvailable();
      return;
    }

    lastReceivedCode = code;
    lastCodeTime = currentTime;

    // Filtre les codes valides
    if (code != 0 && bitLength == 32) {
      processCode(code);
    }

    mySwitch.resetAvailable();
  }
}

// ===== FONCTIONS SONORES MODIFIÉES =====
void playStartupSound() {
  if (!soundEnabled) return; // ⭐ Vérifier si son activé
  
  // Son de démarrage - 3 bips courts
  for (int i = 0; i < 3; i++) {
    tone(BUZZER_PIN, 800);
    delay(100);
    noTone(BUZZER_PIN);
    delay(100);
  }
}

void playNuclearAlert() {
  if (!soundEnabled) return; // ⭐ Vérifier si son activé
  
  unsigned long currentTime = millis();
  
  if (currentTime - lastSoundChange >= TONE_DURATION) {
    tone(BUZZER_PIN, NUCLEAR_TONES[currentTone]);
    currentTone = (currentTone + 1) % NUM_TONES;
    lastSoundChange = currentTime;
  }
}

void playMessageReceivedSound() {
  if (!soundEnabled) return; // ⭐ Vérifier si son activé
  
  // Son d'alerte d'urgence quand message reçu
  Serial.println("🚨 SIGNAL D'ALERTE NUCLÉAIRE ACTIVÉ !");
  noTone(BUZZER_PIN);
  
  // Sirène d'urgence
  for (int i = 0; i < 5; i++) {
    // Montée
    for (int freq = 200; freq <= 1000; freq += 50) {
      tone(BUZZER_PIN, freq);
      delay(20);
    }
    // Descente
    for (int freq = 1000; freq >= 200; freq -= 50) {
      tone(BUZZER_PIN, freq);
      delay(20);
    }
  }
  
  // Reset pour l'alerte continue
  currentTone = 0;
  lastSoundChange = millis();
}

void playConfirmationSound() {
  if (!soundEnabled) return; // ⭐ Vérifier si son activé
  
  tone(BUZZER_PIN, 440);
  delay(200);
  noTone(BUZZER_PIN);
}

void processTerminalCommand(String command) {
  Serial.print("📝 Commande reçue: '");
  Serial.print(command);
  Serial.println("'");

  // ⭐⭐ NOUVELLES COMMANDES POUR CONTRÔLE DU SON ⭐⭐
  if (command == "soundon") {
    soundEnabled = true;
    Serial.println("🔊 SON ACTIVÉ - Les alertes sonores sont maintenant actives");
    playConfirmationSound(); // Jouer un son de confirmation
  }
  else if (command == "soundoff") {
    soundEnabled = false;
    noTone(BUZZER_PIN); // Arrêter immédiatement tout son en cours
    Serial.println("🔇 SON DÉSACTIVÉ - Les alertes sont maintenant silencieuses");
    Serial.println("💡 La LED continuera à clignoter lors des alertes");
  }
  else if (command == "stopalert") {
    if (alertActive) {
      alertActive = false;
      digitalWrite(LED_GREEN, LOW);
      noTone(BUZZER_PIN); // Arrêter le son
      Serial.println("✅ ALERTE ARRÊTÉE - LED + SON ÉTEINTS");
      Serial.print("📄 Message lu: '");
      Serial.print(lastMessage);
      Serial.println("'");
      
      // Son de confirmation (si son activé)
      playConfirmationSound();
    } else {
      Serial.println("⚠️ Aucune alerte active à arrêter");
    }
  } 
  else if (command == "status") {
    Serial.println("📊 === ÉTAT DU SYSTÈME ===");
    Serial.print("🚨 Alerte active: ");
    Serial.println(alertActive ? "OUI" : "NON");
    Serial.print("🔊 Son: ");
    Serial.println(soundEnabled ? "ACTIVÉ" : "DÉSACTIVÉ"); // ⭐ Afficher l'état du son
    
    if (alertActive) {
      Serial.print("📩 Message en attente: '");
      Serial.print(lastMessage);
      Serial.println("'");
      Serial.println("💡 LED: Clignotante");
      if (soundEnabled) {
        Serial.println("🔊 SON: Alerte nucléaire active");
      } else {
        Serial.println("🔇 SON: Désactivé (alerte silencieuse)");
      }
    } else {
      Serial.println("💡 LED: Éteinte");
      Serial.println("🔊 SON: Arrêté");
    }
    Serial.println("========================");
  }
  else if (command == "testsound") {
    if (soundEnabled) {
      Serial.println("🧪 TEST: Son d'alerte nucléaire...");
      playMessageReceivedSound();
      Serial.println("✅ Test sonore terminé");
    } else {
      Serial.println("🔇 Son désactivé - Tapez 'soundon' pour activer le son");
    }
  }
  else if (command == "help") {
    showHelp();
  }
  else if (command == "test") {
    Serial.println("🧪 TEST: Simulation d'une alerte complète...");
    alertActive = true;
    lastMessage = "Message de test nucléaire";
    
    // Jouer le son de réception seulement si activé
    if (soundEnabled) {
      playMessageReceivedSound();
      Serial.println("✅ Alerte de test activée avec son");
    } else {
      Serial.println("✅ Alerte de test activée (silencieuse)");
    }
    Serial.println("💡 Tapez 'stopalert' pour arrêter");
  }
  else if (command == "clear") {
    Serial.print("\033[2J\033[H");
    Serial.println("🧹 Terminal effacé");
  }
  else if (command == "") {
    return;
  }
  else {
    Serial.print("❌ Commande inconnue: '");
    Serial.print(command);
    Serial.println("'");
    Serial.println("💡 Tapez 'help' pour voir les commandes disponibles");
  }
}

void showHelp() {
  Serial.println("🔧 === AIDE - COMMANDES DISPONIBLES ===");
  Serial.println("stopalert  - Arrêter l'alerte LED + SON");
  Serial.println("soundon    - ⭐ ACTIVER le son des alertes");
  Serial.println("soundoff   - ⭐ DÉSACTIVER le son des alertes");
  Serial.println("status     - Afficher l'état du système");
  Serial.println("test       - Simuler une alerte complète");
  Serial.println("testsound  - Tester uniquement le son");
  Serial.println("clear      - Effacer l'écran du terminal");
  Serial.println("help       - Afficher cette aide");
  Serial.println("=====================================");
  Serial.println("💡 Les commandes ne sont pas sensibles à la casse");
  Serial.println("🔊 BUZZER connecté sur pin D5 (GPIO14)");
  
  // ⭐ Afficher l'état actuel du son
  Serial.print("🔊 État du son: ");
  Serial.println(soundEnabled ? "ACTIVÉ" : "DÉSACTIVÉ");
}

void processCode(unsigned long code) {
  byte byte0 = (code >> 24) & 0xFF;
  byte byte1 = (code >> 16) & 0xFF;
  byte byte2 = (code >> 8) & 0xFF;
  byte byte3 = code & 0xFF;

  // Code de début (0xFF)
  if (byte0 == 0xFF) {
    expectedLength = code & 0xFF;
    messageBuffer = "";
    receivingMessage = true;
    lastPacketTime = millis();
    Serial.print("DEBUG: Début de message - Longueur attendue: ");
    Serial.println(expectedLength);
    return;
  }

  // Code de fin (0xFE)
  if (byte0 == 0xFE) {
    if (receivingMessage) {
      Serial.print("✅ MESSAGE PERSONNALISÉ REÇU: '");
      Serial.print(messageBuffer);
      Serial.print("' (");
      Serial.print(messageBuffer.length());
      Serial.println(" caractères)");

      // ⭐ ACTIVER L'ALERTE COMPLÈTE (LED + SON SI ACTIVÉ) ⭐
      alertActive = true;
      lastMessage = messageBuffer;
      
      Serial.println("🚨 ALERTE NUCLÉAIRE ACTIVÉE !");
      Serial.println("💡 LED: Clignotante");
      
      if (soundEnabled) {
        Serial.println("🔊 SON: Alerte nucléaire continue");
        // Jouer le son d'alerte lors de la réception
        playMessageReceivedSound();
      } else {
        Serial.println("🔇 SON: Désactivé (alerte silencieuse)");
      }
      
      Serial.println("💡 Tapez 'stopalert' dans le terminal pour arrêter l'alerte");
    }
    resetMessageBuffer();
    return;
  }

  // Paquet de données
  if (receivingMessage) {
    int packetNumber = byte0;

    Serial.print("DEBUG: Paquet ");
    Serial.print(packetNumber + 1);
    Serial.print(" reçu: 0x");
    Serial.println(code, HEX);

    if (byte1 != 0x00 && messageBuffer.length() < expectedLength) {
      if (byte1 >= 32 && byte1 <= 126) messageBuffer += (char)byte1;
    }
    if (byte2 != 0x00 && messageBuffer.length() < expectedLength) {
      if (byte2 >= 32 && byte2 <= 126) messageBuffer += (char)byte2;
    }
    if (byte3 != 0x00 && messageBuffer.length() < expectedLength) {
      if (byte3 >= 32 && byte3 <= 126) messageBuffer += (char)byte3;
    }

    Serial.print("  Buffer actuel: '");
    Serial.print(messageBuffer);
    Serial.print("' (");
    Serial.print(messageBuffer.length());
    Serial.print("/");
    Serial.print(expectedLength);
    Serial.println(" chars)");

    lastPacketTime = millis();
    return;
  }

  // Signal hors séquence
  Serial.print("DEBUG: Signal hors séquence: 0x");
  Serial.print(code, HEX);
  Serial.print(" (byte0=0x");
  Serial.print(byte0, HEX);
  Serial.println(")");
}

void resetMessageBuffer() {
  messageBuffer = "";
  expectedLength = 0;
  receivingMessage = false;
  Serial.println("DEBUG: Buffer réinitialisé");
}