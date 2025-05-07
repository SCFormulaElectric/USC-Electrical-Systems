#include <stdint.h>    
#include <pic12f609.h> 

static __code uint16_t __at(0x2007) configword1 = 0x00D4;

// Pins 
enum GpioBit {
    BMS_fault_o,    //GP0 (Pin 7) - Inverted for BMS relay
    BMS_gate_i,     //GP1 (Pin 6)
    green_PIC_o,    //GP2 (Pin 5) - Blinks Not Faulted
    reserved, 
    IMD_gate_i,     //GP4 (Pin 3) - Active low
    red_PIC_o       //GP5 (Pin 2) - Blinks Faulted
};

// --- Constants ---
#define FREQ_SCALAR 20 // Number of Timer1 overflows for half blink period
                             // Approx: 30 * 8.192ms = 245.76ms (~2Hz blink rate)

// --- Global Variables ---

uint8_t system_fault_state = 0;
uint8_t blink_counter = 0;

int main(void) {

    ANSEL = 0x00;
    CMCON0 = 0x07;

    //tristate register for i/o
    TRISIO = (1 << BMS_gate_i) | (1 << IMD_gate_i) | (1 << 3); // Set inputs
    TRISIO &= ~((1 << BMS_fault_o) | (1 << green_PIC_o) | (1 << red_PIC_o)); // Clear outputs

    WPU = 0x00;
    OPTION_REG = 0x80; // Disable global pull-ups

    GPIO &= ~((1 << BMS_fault_o) | (1 << green_PIC_o) | (1 << red_PIC_o));

    // turn off all interrupts on change
    IOC = 0;

    // timer 1
    T1CON = 0x01;

    // timer 1 clock source Fosc
    CMCON1 = 0x10; //8 Mhz

    // Clear Timer1 Interrupt Flag
    PIR1 &= ~(1 << TMR1IF);

    //disable intreupts
    PIE1 &= ~(1 << TMR1IE);
    INTCON &= ~((1 << GIE) | (1 << PEIE));

    while (1) {

        uint8_t bms_gate_state = (GPIO >> BMS_gate_i) & 1; //  GP1 
        uint8_t imd_gate_state = (GPIO >> IMD_gate_i) & 1; //  GP4 

        uint8_t current_fault = (bms_gate_state == 1) || (imd_gate_state == 0);
        
        //inverted for BMS relay
        if (bms_gate_state) { 
            GPIO &= ~(1 << BMS_fault_o); // Set fault output LOW
        } else {
            GPIO |= (1 << BMS_fault_o); // Set fault output HIGH
        }


        if (PIR1 & (1 << 0)) {  // TMR1F
            PIR1 &= (1<<0);   // TMR1F

            blink_counter++; // 8.2ms

            if (blink_counter >= FREQ_SCALAR) {
                blink_counter = 0; 

                
                if (current_fault == 1) {
                    GPIO ^= (1 << red_PIC_o);
                    GPIO &= ~(1 << green_PIC_o);
                } else {
                    GPIO |= (1 << green_PIC_o);
                    GPIO &= ~(1 << red_PIC_o);
                }
            }
        }

    }

    return 0;
}


