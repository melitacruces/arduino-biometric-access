/***************************************************************************
 *  ingresar.ino  -  Modo de verificación de acceso
 *
 *  Lee una huella, consulta el nombre al PC por serial, pide el PIN en el
 *  teclado y abre la cerradura (relé) si la combinación huella + PIN es
 *  válida. Se comunica con la app Python mediante mensajes de texto:
 *      ->  CONSULTAR_ID:<id>       (pide el nombre asociado a la huella)
 *      <-  nombre:<nombre>
 *      ->  VERIFICAR:<id>:<pin>    (pide validar huella + PIN)
 *      <-  permitido:<nombre> | denegado
 *
 *  Hardware: sensor AS608, teclado 4x4, LCD I2C 1602 y relé/cerradura.
 ***************************************************************************/

#include <Adafruit_Fingerprint.h>
#include <Keypad.h>
#include <SoftwareSerial.h>
#include <LiquidCrystal_I2C.h>

// --- Comunicación con el sensor de huellas ---
SoftwareSerial mySerial(10, 11);
Adafruit_Fingerprint finger(&mySerial);

// --- Pantalla LCD I2C ---
LiquidCrystal_I2C lcd(0x27, 16, 2);

// --- Teclado matricial 4x4 ---
const byte ROWS = 4, COLS = 4;
char keys[ROWS][COLS] = {
  {'1', '2', '3', 'A'},
  {'4', '5', '6', 'B'},
  {'7', '8', '9', 'C'},
  {'*', '0', '#', 'D'}
};
byte rowPins[ROWS] = {9, 8, 7, 6};
byte colPins[COLS] = {5, 4, 3, 2};
Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// --- Relé o cerradura ---
const int relePin = 13;

void setup() {
  Serial.begin(9600);
  mySerial.begin(57600);
  finger.begin(57600);

  lcd.init();
  lcd.backlight();

  pinMode(relePin, OUTPUT);
  digitalWrite(relePin, HIGH);  // Cerradura cerrada

  lcd.setCursor(0, 0);
  lcd.print("SISTEMA LISTO");
  delay(2000);
  lcd.clear();
}

void loop() {
  static bool esperandoHuella = true;

  if (esperandoHuella) {
    lcd.setCursor(0, 0);
    lcd.print("Coloque su dedo   ");
    lcd.setCursor(0, 1);
    lcd.print("para verificar    ");

    // Solo actuar si hay una imagen
    if (finger.getImage() == FINGERPRINT_OK) {
      int id = getFingerprintID();
      if (id > 0) {
        esperandoHuella = false;

        // Consultar nombre al PC
        Serial.print("CONSULTAR_ID:");
        Serial.println(id);
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Usuario");
        lcd.setCursor(0, 1);
        lcd.print("detectado");
        delay(500);

        // Esperar el nombre que envía el PC
        while (!Serial.available());
        String respuesta = Serial.readStringUntil('\n');
        String nombre = "desconocido";
        if (respuesta.startsWith("nombre:")) {
          nombre = respuesta.substring(respuesta.indexOf(":") + 1);
        }

        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("Bienvenido:");
        lcd.setCursor(0, 1);
        lcd.print(nombre);
        delay(2000);

        // Leer PIN
        if (!leerPIN(id)) {
          lcd.clear();
          lcd.setCursor(0, 0);
          lcd.print("PIN cancelado");
          delay(2000);
        }

        esperandoHuella = true;
      } else {
        lcd.clear();
        lcd.setCursor(0, 0);
        lcd.print("No reconocida");
        lcd.setCursor(0, 1);
        lcd.print("Intente otra vez");
        delay(3000);
        lcd.clear();
      }
    }
  }
}

int getFingerprintID() {
  if (finger.image2Tz() != FINGERPRINT_OK) return -1;
  if (finger.fingerFastSearch() != FINGERPRINT_OK) return -1;
  return finger.fingerID;
}

bool leerPIN(int idHuella) {
  String pin = "";
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Ingrese PIN:");

  while (true) {
    char key = keypad.getKey();
    if (key) {
      if (key == '#') {
        if (pin.length() > 0) break;  // Confirmar ingreso
      } else if (key == '*') {
        if (pin.length() > 0) {
          pin.remove(pin.length() - 1);
          lcd.setCursor(pin.length(), 1);
          lcd.print(" ");
          lcd.setCursor(pin.length(), 1);
        }
      } else if (key == 'B') {
        return false;  // Cancelar y volver al menú
      } else if (pin.length() < 5 && isDigit(key)) {
        pin += key;
        lcd.setCursor(pin.length() - 1, 1);
        lcd.print("*");
      }
    }
  }

  // Enviar verificación al PC
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Verificando...");
  Serial.print("VERIFICAR:");
  Serial.print(idHuella);
  Serial.print(":");
  Serial.println(pin);

  while (!Serial.available());
  String respuesta = Serial.readStringUntil('\n');

  if (respuesta.startsWith("permitido:")) {
    String nombre = respuesta.substring(respuesta.indexOf(":") + 1);
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Acceso permitido");
    lcd.setCursor(0, 1);
    lcd.print(nombre);
    digitalWrite(relePin, LOW);   // Abrir cerradura
    delay(3000);
    digitalWrite(relePin, HIGH);  // Cerrar
    return true;
  } else {
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("PIN o Huella");
    lcd.setCursor(0, 1);
    lcd.print("incorrectos");
    delay(3000);
    return false;
  }
}
