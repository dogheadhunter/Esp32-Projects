/*
  Simple I2S Sine Wave Generator - ONE SHOT
  Plays a tone for 1 second, then stops.
*/
#include <Arduino.h>
#include "driver/i2s.h"
#include <math.h>

// Your I2S Connections
#define I2S_DOUT      22
#define I2S_BCLK      26
#define I2S_LRC       25

#define SAMPLE_RATE   44100
#define I2S_NUM       I2S_NUM_0
#define WAVE_FREQ_HZ  440     
#define PI            3.14159265

int16_t samples[100]; 

void setup() {
  Serial.begin(115200);
  Serial.println("I2S Tone Test Started");

  // Configure I2S Driver
  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT, 
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 64,
    .use_apll = false,
    .tx_desc_auto_clear = true
  };

  i2s_pin_config_t pin_config = {
    .bck_io_num = I2S_BCLK,
    .ws_io_num = I2S_LRC,
    .data_out_num = I2S_DOUT,
    .data_in_num = I2S_PIN_NO_CHANGE
  };

  i2s_driver_install(I2S_NUM, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM, &pin_config);

  // Pre-calculate sine wave
  for(int i=0; i<100; i++) {
     samples[i] = (int16_t)(10000 * sin(2 * PI * i / 100.0));
  }

  // --- PLAY SOUND FOR 1 SECOND ---
  unsigned long startMillis = millis();
  size_t bytes_written;
  
  while (millis() - startMillis < 1000) {
      for(int i=0; i<100; i++) {
          int16_t sample = samples[i];
          i2s_write(I2S_NUM, &sample, sizeof(sample), &bytes_written, portMAX_DELAY);
          i2s_write(I2S_NUM, &sample, sizeof(sample), &bytes_written, portMAX_DELAY);
      }
  }

  // --- STOP SOUND ---
  // Write zeros to clear the buffer (silence)
  int16_t zero = 0;
  for(int i=0; i<100; i++) {
      i2s_write(I2S_NUM, &zero, sizeof(zero), &bytes_written, portMAX_DELAY);
      i2s_write(I2S_NUM, &zero, sizeof(zero), &bytes_written, portMAX_DELAY);
  }
}

void loop() {
  // No need to repeat, one-shot in setup()
}
