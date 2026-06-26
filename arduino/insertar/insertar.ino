/***************************************************************************
 *  insertar.ino  -  Modo de enrolamiento de huellas
 *
 *  Registra una nueva huella en el sensor a partir de un ID que envía la app
 *  Python por serial. Protocolo de mensajes:
 *      <-  READY               (sensor listo, esperando ID)
 *      ->  <id>                (ID donde guardar la huella)
 *      <-  ENROLL_OK | ENROLL_FAIL
 *
 *  Hardware: sensor de huellas AS608 conectado por SoftwareSerial (pines 10/11).
 ***************************************************************************/

#include <Adafruit_Fingerprint.h>
#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11); // RX, TX
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&mySerial);

uint8_t id;

void setup() {
  Serial.begin(9600);
  while (!Serial);  // For Leonardo/Micro/Zero

  finger.begin(57600);

  if (finger.verifyPassword()) {
    Serial.println("READY");  // <- Mensaje que espera Python para comenzar
  } else {
    Serial.println("Sensor no detectado");
    while (1);
  }
}

void loop() {
  if (Serial.available()) {
    id = Serial.parseInt();  // Recibe el ID desde Python
    if (id > 0) {
      if (enrollFingerprint(id)) {
        Serial.println("ENROLL_OK");    // <- Confirmación de éxito
      } else {
        Serial.println("ENROLL_FAIL");  // <- Mensaje de error
      }
    }
  }
}

bool enrollFingerprint(uint8_t id) {
  int p = -1;
  Serial.println("Coloque el dedo");  // Primer mensaje visible para el usuario

  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
    if (p == FINGERPRINT_NOFINGER) continue;
    if (p == FINGERPRINT_OK) break;
    return false;
  }

  p = finger.image2Tz(1);
  if (p != FINGERPRINT_OK) return false;

  Serial.println("Retire el dedo");  // Aviso para quitar el dedo
  delay(2000);

  p = 0;
  while (p != FINGERPRINT_NOFINGER) {
    p = finger.getImage();
  }

  Serial.println("Coloque el mismo dedo nuevamente");  // Segundo escaneo
  p = -1;
  while (p != FINGERPRINT_OK) {
    p = finger.getImage();
    if (p == FINGERPRINT_NOFINGER) continue;
    if (p == FINGERPRINT_OK) break;
    return false;
  }

  p = finger.image2Tz(2);
  if (p != FINGERPRINT_OK) return false;

  p = finger.createModel();
  if (p != FINGERPRINT_OK) return false;

  p = finger.storeModel(id);
  if (p == FINGERPRINT_OK) {
    return true;
  } else {
    return false;
  }
}
