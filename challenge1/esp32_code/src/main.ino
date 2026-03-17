#include <WiFi.h>
#include <esp_now.h>

/*
  Internet of Things - First Challenge
  Project Title: Smart Home Motion & Light Sensor
  Pietro Pizzoccheri: 10797420
  Lorenzo Bardelli: 10831941
*/

#define TEAM_LEADER_CODE 10797420 
#define AB (TEAM_LEADER_CODE % 100)
#define SLEEP_TIME_SEC ((AB % 50 + 5) / 10.0) 

#define S_uS_CONV 1000000       // conversion factor from us to s

// sensor Pinout
#define PIR_PIN 12
#define LDR_PIN 34

long long int startTime;

// broadcast address required by the challenge: FF:FF:FF:FF:FF:FF
uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};

esp_now_peer_info_t ESP_sink; // peer data

//  functions' prototypes  //
void wifiInit();
void onDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status);
void sendMessage(String message);


void setup()
{
    startTime = micros();
    // open serial port: 115200
    Serial.begin(115200);
    Serial.printf("[0] -- Booting\r\n");

    // sensor configuration
    pinMode(PIR_PIN, INPUT);
    pinMode(LDR_PIN, INPUT);
    
    Serial.printf("[%d] -- Setup completed\r\n", (int)(micros() - startTime));
}

void loop()
{
    //  loop will be executed only once per cycle due to deep sleep call  //

    // fetch data from sensors
    bool motionDetected = digitalRead(PIR_PIN) == HIGH;
    int luminosity = analogRead(LDR_PIN); // Reads 0-4095 on ESP32

    // format the message according to requirements
    String motionStr = motionDetected ? "MOTION_DETECTED" : "MOTION_NOT_DETECTED";
    String message = motionStr + "-LUMINOSITY:" + String(luminosity);
    
    Serial.printf("[%d] -- Sensor reading complete: %s\r\n", (int)(micros() - startTime), message.c_str());

    // configure WiFi for transmission and send message to sink
    wifiInit();
    Serial.printf("[%d] -- Wifi initialized\r\n", (int)(micros() - startTime));

    sendMessage(message);
    Serial.printf("[%d] -- Message sent\r\n", (int)(micros() - startTime));

    delay(50); // small delay to ensure transmission completes

    WiFi.mode(WIFI_OFF);
    Serial.printf("[%d] -- WiFi turned off\r\n", (int)(micros() - startTime));

    Serial.printf("[%d] -- Entering deep sleep for %.1f seconds...\r\n", (int)(micros() - startTime), SLEEP_TIME_SEC);
    Serial.flush(); // flush serial buffer before entering deep sleep

    // set wakeup timer and sleep
    esp_sleep_enable_timer_wakeup(SLEEP_TIME_SEC * S_uS_CONV);
    esp_deep_sleep_start();
}

// functions' definition //

void wifiInit()
{
    WiFi.mode(WIFI_STA);
    WiFi.setTxPower(WIFI_POWER_2dBm); // set wifi transmission power
    esp_now_init();                   // init ESP-NOW communication protocol

    esp_now_register_send_cb(onDataSent); // set sending callback

    // peer registration
    memcpy(ESP_sink.peer_addr, broadcastAddress, 6);
    ESP_sink.channel = 0;
    ESP_sink.encrypt = false;

    esp_now_add_peer(&ESP_sink); // add sink to peers
}

// sending callback
void onDataSent(const wifi_tx_info_t *tx_info, esp_now_send_status_t status)
{
    (void)tx_info;
    Serial.printf("Message status: ");
    Serial.printf(status == ESP_NOW_SEND_SUCCESS ? "SENT\r\n" : "ERROR\r\n");
}

// send message through WiFi with ESP-NOW protocol
void sendMessage(String message)
{
    uint8_t *addr = broadcastAddress;
    uint8_t *data = (uint8_t *)message.c_str(); // casting string to uint8_t

    int len = message.length() + 1;
    esp_now_send(addr, data, len);
}

// top of the morning 