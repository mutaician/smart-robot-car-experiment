#include <ks_Matrix.h>
Matrix myMatrix(A4, A5);

// ==========================================
// 1. THE FONT DICTIONARY
// Standard 8x8 HEX representations for A-Z
// ==========================================
const uint8_t font_AZ[26][8] = {
  {0x18, 0x3C, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x00}, // A
  {0x7C, 0x66, 0x66, 0x7C, 0x66, 0x66, 0x7C, 0x00}, // B
  {0x3C, 0x66, 0x60, 0x60, 0x60, 0x66, 0x3C, 0x00}, // C
  {0x78, 0x6C, 0x66, 0x66, 0x66, 0x6C, 0x78, 0x00}, // D
  {0x7E, 0x60, 0x60, 0x7C, 0x60, 0x60, 0x7E, 0x00}, // E
  {0x7E, 0x60, 0x60, 0x7C, 0x60, 0x60, 0x60, 0x00}, // F
  {0x3C, 0x66, 0x60, 0x6E, 0x66, 0x66, 0x3E, 0x00}, // G
  {0x66, 0x66, 0x66, 0x7E, 0x66, 0x66, 0x66, 0x00}, // H
  {0x3C, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3C, 0x00}, // I
  {0x0E, 0x06, 0x06, 0x06, 0x66, 0x66, 0x3C, 0x00}, // J
  {0x66, 0x6C, 0x78, 0x70, 0x78, 0x6C, 0x66, 0x00}, // K
  {0x60, 0x60, 0x60, 0x60, 0x60, 0x60, 0x7E, 0x00}, // L
  {0x63, 0x77, 0x7F, 0x6B, 0x63, 0x63, 0x63, 0x00}, // M
  {0x66, 0x76, 0x7E, 0x7E, 0x6E, 0x66, 0x66, 0x00}, // N
  {0x3C, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00}, // O
  {0x7C, 0x66, 0x66, 0x7C, 0x60, 0x60, 0x60, 0x00}, // P
  {0x3C, 0x66, 0x66, 0x66, 0x6A, 0x64, 0x3A, 0x00}, // Q
  {0x7C, 0x66, 0x66, 0x7C, 0x6C, 0x66, 0x66, 0x00}, // R
  {0x3C, 0x66, 0x60, 0x3C, 0x06, 0x66, 0x3C, 0x00}, // S
  {0x7E, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x00}, // T
  {0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x00}, // U
  {0x66, 0x66, 0x66, 0x66, 0x66, 0x3C, 0x18, 0x00}, // V
  {0x63, 0x63, 0x63, 0x6B, 0x7F, 0x77, 0x63, 0x00}, // W
  {0x66, 0x66, 0x3C, 0x18, 0x3C, 0x66, 0x66, 0x00}, // X
  {0x66, 0x66, 0x66, 0x3C, 0x18, 0x18, 0x18, 0x00}, // Y
  {0x7E, 0x06, 0x0C, 0x18, 0x30, 0x60, 0x7E, 0x00}  // Z
};

void setup() {
  myMatrix.begin(0x70); 
  myMatrix.clear();
  randomSeed(analogRead(A0)); 
}

void loop() {
  animateStringWithRandomEffects("Mutaician");
  delay(3000); // Pauses longer before repeating the word
}

// ===================================================
// THE ANIMATION TEXT MANAGER
// ===================================================
void animateStringWithRandomEffects(String text) {
  text.toUpperCase(); 

  for (size_t i = 0; i < text.length(); i++) {
    char letter = text.charAt(i);
    
    if (letter >= 'A' && letter <= 'Z') {
      int fontIndex = letter - 'A';
      const uint8_t* currentLetterMap = font_AZ[fontIndex];

      int effectChoice = random(0, 5); 

      switch(effectChoice) {
        case 0:
          // Effect 0: Standard Reveal & Hold (Slower)
          drawStatic(currentLetterMap);
          delay(1500); 
          break;

        case 1:
          // Effect 1: Flip Gymnastics (Slower)
          drawStatic(currentLetterMap);
          delay(700);
          drawModified(currentLetterMap, 1); // Flip Horizontal
          delay(600);
          drawModified(currentLetterMap, 2); // Flip Vertical
          delay(600);
          drawStatic(currentLetterMap);      // Return to normal
          delay(700);
          break;

        case 2:
          // Effect 2: Laser Scanner Wipe (Bug Fixed & Slower)
          animationLaserWipe(currentLetterMap);
          break;

        case 3:
          // Effect 3: Explode outward (Slower)
          drawStatic(currentLetterMap);
          delay(1000);
          animationParticles(currentLetterMap, true);
          break;

        case 4:
          // Effect 4: Liquid Melt Down (Slower)
          drawStatic(currentLetterMap);
          delay(1000);
          animationMeltDown(currentLetterMap);
          break;
      }
    } else {
      myMatrix.clear();
      myMatrix.writeDisplay();
      delay(600); // Space between words is slower
    }
    
    // Clear screen before moving to next letter
    myMatrix.clear();
    myMatrix.writeDisplay();
    delay(300); // Dark screen beat between letters
  }
}

// ===================================================
// GRAPHICS RUNTIME FUNCTIONS (Core Drawing Math)
// ===================================================

void drawStatic(const uint8_t frame[]) {
  myMatrix.clear();
  for (int y = 0; y < 8; y++) {
    for (int x = 0; x < 8; x++) {
      if ((frame[y] & (1 << (7 - x))) > 0) {
        myMatrix.drawPixel(7 - x, y, 1); 
      }
    }
  }
  myMatrix.writeDisplay();
}

void drawModified(const uint8_t frame[], int mode) {
  myMatrix.clear();
  for (int y = 0; y < 8; y++) {
    for (int x = 0; x < 8; x++) {
      if ((frame[y] & (1 << (7 - x))) > 0) {
        int targetX = 7 - x;
        int targetY = y;

        if (mode == 1) targetX = x;     
        if (mode == 2) targetY = 7 - y; 

        myMatrix.drawPixel(targetX, targetY, 1);
      }
    }
  }
  myMatrix.writeDisplay();
}

// ===================================================
// TRANSITION EFFECTS MODULES
// ===================================================

// Sci-Fi Laser Sweep Reveal (BUG FIXED)
void animationLaserWipe(const uint8_t frame[]) {
  // FIX: Loop now goes up to 8 so the laser sweeps completely off screen
  for (int sweepRow = 0; sweepRow <= 8; sweepRow++) { 
    myMatrix.clear();
    for (int y = 0; y < 8; y++) {
      for (int x = 0; x < 8; x++) {
        
        // Draw the blinding sweep line (only if it is still on the grid)
        if (y == sweepRow && sweepRow < 8) {
          myMatrix.drawPixel(7 - x, y, 1);
        } 
        // Keep rows above the line turned on with the letter's shape
        else if (y < sweepRow) {
          if ((frame[y] & (1 << (7 - x))) > 0) {
            myMatrix.drawPixel(7 - x, y, 1);
          }
        }
      }
    }
    myMatrix.writeDisplay();
    delay(120); // Slower sweep speed (was 60)
  }
  delay(1200); // Hold full character visibility at end of sweep (was 600)
}

// Particle Engine 
void animationParticles(const uint8_t frame[], bool isDispersing) {
  for (int step = 0; step <= 4; step++) {
    myMatrix.clear();
    for (int y = 0; y < 8; y++) {
      for (int x = 0; x < 8; x++) {
        if ((frame[y] & (1 << (7 - x))) > 0) {
          
          float distanceX = x - 3.5;
          float distanceY = y - 3.5;

          int currentStep = isDispersing ? step : (4 - step);
          
          int newX = x + (distanceX > 0 ? currentStep : -currentStep);
          int newY = y + (distanceY > 0 ? currentStep : -currentStep);
          int correctedX = 7 - newX;

          if (correctedX >= 0 && correctedX <= 7 && newY >= 0 && newY <= 7) {
            myMatrix.drawPixel(correctedX, newY, 1);
          }
        }
      }
    }
    myMatrix.writeDisplay();
    delay(120); // Slower particle movement (was 70)
  }
}

// Liquid Gravitational Melting Slide Out
void animationMeltDown(const uint8_t frame[]) {
  for (int shiftAmount = 0; shiftAmount < 8; shiftAmount++) {
    myMatrix.clear();
    for (int y = 0; y < 8; y++) {
      int targetY = y + shiftAmount;
      if (targetY < 8) {
        for (int x = 0; x < 8; x++) {
          if ((frame[y] & (1 << (7 - x))) > 0) {
            myMatrix.drawPixel(7 - x, targetY, 1);
          }
        }
      }
    }
    myMatrix.writeDisplay();
    delay(100); // Slower melt speed (was 50)
  }
}