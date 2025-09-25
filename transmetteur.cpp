#include <SPI.h>
#include <MFRC522.h>
#include <RCSwitch.h>

// ===== LED =====
#define LED_GREEN 16  // D0 correspond à GPIO16 sur ESP8266
#define LED_RED 2     // D4 correspond à GPIO2 sur ESP8266

// ===== RFID =====
#define RST_PIN  0    // D3 (GPIO0)
#define SS_PIN   4    // D2 (GPIO4)
MFRC522 mfrc522(SS_PIN, RST_PIN);

// ===== 433MHz =====
RCSwitch mySwitch = RCSwitch();
const int transmitPin = 5; // D1 (GPIO5)

// ===== UIDs AUTORISÉS =====
// Chaque ligne = un UID, chaque colonne = un octet
byte authorizedUIDs[][4] = {
  {0xC0, 0xA9, 0x72, 0xA3},  // Carte 1
  {0x0B, 0xE6, 0x8C, 0x33}   // Carte 2
};
const byte authorizedCount = sizeof(authorizedUIDs) / sizeof(authorizedUIDs[0]);
const byte authorizedUIDSize = 4; // Taille UID en octets

// ===== MESSAGE PERSONNALISÉ =====
String customMessage = "HELLO"; // Message par défaut
String serialBuffer = "";
bool messageUpdated = false;

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== RFID + 433MHz Transmitter avec Messages Personnalisés ===");
  Serial.println("DEBUG: Démarrage du système...");

  // Configuration LEDs
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
  Serial.println("DEBUG: LEDs initialisées");

  // RFID
  SPI.begin();
  mfrc522.PCD_Init();
  Serial.println("DEBUG: Lecteur RFID initialisé");

  // Affiche les UIDs autorisés
  Serial.println("DEBUG: UIDs autorisés :");
  for (byte c = 0; c < authorizedCount; c++) {
    Serial.print("  Carte ");
    Serial.print(c + 1);
    Serial.print(": ");
    for (byte i = 0; i < authorizedUIDSize; i++) {
      Serial.print(authorizedUIDs[c][i] < 0x10 ? " 0" : " ");
      Serial.print(authorizedUIDs[c][i], HEX);
    }
    Serial.println();
  }

  // 433MHz
  mySwitch.enableTransmit(transmitPin);
  mySwitch.setProtocol(1);
  mySwitch.setRepeatTransmit(3);
  Serial.println("DEBUG: Émetteur 433MHz configuré");

  Serial.println("DEBUG: Système prêt !");
  Serial.print("INFO: Message actuel: '");
  Serial.print(customMessage);
  Serial.println("'");
  Serial.println("INFO: Tapez 'MSG:votre message' pour changer le message");
  Serial.println("DEBUG: En attente de cartes ou commandes...\n");
}

void loop() {
  checkSerialCommands();

  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    delay(100);
    return;
  }

  Serial.println("DEBUG: Carte détectée !");
  Serial.print("UID scanné : ");
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(mfrc522.uid.uidByte[i], HEX);
  }
  Serial.println();

  bool isAuthorized = checkUID();

  if (isAuthorized) {
    Serial.print("DEBUG: UID AUTORISÉ - Envoi de '");
    Serial.print(customMessage);
    Serial.println("'");

    setLED(true);
    sendCustomMessage(customMessage);
  } else {
    Serial.println("DEBUG: UID NON AUTORISÉ - Aucune transmission");
    setLED(false);
  }

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();
  Serial.println("DEBUG: Communication RFID fermée\n");

  delay(2000);
  setLEDOff();
  delay(500);
}

// ===== LEDs =====
void setLED(bool isAuthorized) {
  digitalWrite(LED_GREEN, isAuthorized ? HIGH : LOW);
  digitalWrite(LED_RED, isAuthorized ? LOW : HIGH);
}

void setLEDOff() {
  digitalWrite(LED_GREEN, LOW);
  digitalWrite(LED_RED, LOW);
}

// ===== Vérification UIDs =====
bool checkUID() {
  Serial.println("DEBUG: Vérification de l'UID...");

  if (mfrc522.uid.size != authorizedUIDSize) {
    Serial.print("DEBUG: Taille UID incorrecte. Reçu: ");
    Serial.print(mfrc522.uid.size);
    Serial.print(", Attendu: ");
    Serial.println(authorizedUIDSize);
    return false;
  }

  for (byte c = 0; c < authorizedCount; c++) {
    bool match = true;
    for (byte i = 0; i < authorizedUIDSize; i++) {
      if (mfrc522.uid.uidByte[i] != authorizedUIDs[c][i]) {
        match = false;
        break;
      }
    }
    if (match) {
      Serial.print("DEBUG: UID correspond à la carte ");
      Serial.println(c + 1);
      return true;
    }
  }

  Serial.println("DEBUG: Aucun UID correspondant trouvé");
  return false;
}

// ===== Commandes série =====
void checkSerialCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      if (serialBuffer.startsWith("MSG:")) {
        String newMessage = serialBuffer.substring(4);
        if (newMessage.length() > 0) {
          if (newMessage.length() > 50) {
            newMessage = newMessage.substring(0, 50);
            Serial.println("INFO: Message limité à 50 caractères");
          }
          customMessage = newMessage;
          messageUpdated = true;
          Serial.print("INFO: Nouveau message défini: '");
          Serial.print(customMessage);
          Serial.println("'");
          Serial.println("INFO: Scannez une carte autorisée pour l'envoyer");
        }
      }
      serialBuffer = "";
    } else {
      serialBuffer += c;
    }
  }
}

// ===== Transmission message =====
void sendCustomMessage(String message) {
  Serial.print("DEBUG: Envoi du message personnalisé: '");
  Serial.print(message);
  Serial.print("' (");
  Serial.print(message.length());
  Serial.println(" caractères)");

  unsigned long startCode = 0xFF000000L | (message.length() & 0xFF);
  Serial.print("DEBUG: Envoi code de début: 0x");
  Serial.println(startCode, HEX);
  mySwitch.send(startCode, 32);
  delay(100);

  int packets = (message.length() + 2) / 3;

  for (int p = 0; p < packets; p++) {
    unsigned long code = ((unsigned long)(p & 0xFF)) << 24;

    for (int i = 0; i < 3; i++) {
      int charIndex = p * 3 + i;
      if (charIndex < message.length()) {
        byte charByte = (byte)message[charIndex];
        code |= ((unsigned long)charByte) << (16 - (i * 8));
      }
    }

    Serial.print("DEBUG: Paquet ");
    Serial.print(p + 1);
    Serial.print("/");
    Serial.print(packets);
    Serial.print(" - Code: 0x");
    Serial.println(code, HEX);

    mySwitch.send(code, 32);
    delay(50);
  }

  unsigned long endCode = 0xFE000000L;
  Serial.print("DEBUG: Envoi code de fin: 0x");
  Serial.println(endCode, HEX);
  mySwitch.send(endCode, 32);

  Serial.println("DEBUG: Transmission terminée avec succès !");
}
