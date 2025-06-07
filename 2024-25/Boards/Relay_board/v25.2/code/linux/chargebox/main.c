#include <stdint.h>    
#include <pic12f609.h> 

static __code uint16_t __at(0x2007) configword1 = 0x00D4;

// Pins 
enum GpioBit {
    BMS_fault_i,    //GP0 (Pin 7) - Inverted for BMS relay
    IMD_gate_i,     //GP1 (Pin 6)
    red_PIC_o,      //GP2 (Pin 5) - Blinks Not Faulted
    reset_button,   //GP3 (Pin 4) - reset button
    BMS_fault_o,     //GP4 (Pin 3) - Active low
    green_PIC_o      //GP5 (Pin 2) - Blinks Faulted
};

// --- Constants ---
#define FREQ_SCALAR 10000 // Number of Timer1 overflows for half blink period
                          // Approx. 570ms, 1.75 Hz

// --- Global Variables ---

uint16_t blink_counter = 0;

int main(void) {

    ANSEL = 0x00;
    CMCON0 = 0x07;

    //tristate register for i/o
    TRISIO = (1 << BMS_fault_i) | (1 << IMD_gate_i) | (1 << 3); // Set inputs
    TRISIO &= ~((1 << BMS_fault_o) | (1 << green_PIC_o) | (1 << red_PIC_o)); // Clear outputs

    WPU = 0x00;
    
    OPTION_REG = 0x00;  // enable pull-ups

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
    INTCON &= ~((1 << GIE) | (1 << PEIE)| (1 << 4));

    while (1) {

        uint8_t bms_gate_state = (GPIO >> BMS_fault_i) & 1; //  GP1 
        uint8_t imd_gate_state = (GPIO >> IMD_gate_i) & 1; //  GP4 

        uint8_t current_fault = (bms_gate_state == 1) || (imd_gate_state == 0); 

        //inverted for BMS relay
        if (bms_gate_state) { 
            GPIO &= ~(1 << BMS_fault_o); // Set fault output LOW
        } else {
            GPIO |= (1 << BMS_fault_o); // Set fault output HIGH
        }

        //if (PIR1 & (1 << 0)) {  // TMR1F
        //PIR1 &= (1<<0);   // TMR1F
        blink_counter++; // 8.2ms
        
        if (blink_counter >= FREQ_SCALAR) {
            if(current_fault){            
                blink_counter = 0; 
                // Weak pull-ups used instead of direct GPIO output
                // because the capacitive load of the MOSFET being
                // driven is higher than the PIC12 can handle
                TRISIO ^= (1 << red_PIC_o); // turn on/off output
                WPU ^= (1 << red_PIC_o); // turn on/off pull-up
                GPIO ^= (1 << red_PIC_o);   // turn on/off output
                GPIO &= ~(1 << green_PIC_o); // turn off green light
            }
            else{   // not faulted
                TRISIO &= ~(1 << red_PIC_o);  // make output
                GPIO &= ~(1 << red_PIC_o);  // set to 0
                WPU &= ~(1 << red_PIC_o);
            }
        }
            
        //}
    }

    return 0;
}


