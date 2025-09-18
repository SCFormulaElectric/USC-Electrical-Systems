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
uint8_t faulted = 0;

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

    uint8_t output_reg = 0x00;
    uint8_t fault_counter = 0x00;
    uint8_t current_fault = 0x00;

    while (1) {
        uint8_t gpio_reg = GPIO;
        uint8_t bms_gate_state = (gpio_reg >> BMS_fault_i) & 1; //  GP1 
        uint8_t imd_gate_state = (gpio_reg >> IMD_gate_i) & 1; //  GP4 
        uint8_t reset_button_state = (gpio_reg >> reset_button) & 1; // GP3
        
        // added counter because it was faulting when it shouldn't have before
        uint8_t potential_fault = (bms_gate_state == 1) || (imd_gate_state == 0);
        if(potential_fault){
            if(fault_counter < 20){
                fault_counter++;
            }
            else if(fault_counter == 20){
                current_fault = 1;
            }
            else {  // came from not faulted
                fault_counter = 0;
            }
        }
        else{
            if(fault_counter < 20){ // fake fault checker
                fault_counter = 0;  // fake fault, so reset counter
            }
            if(fault_counter < 40){ // fake reset of fault (20 to 40)
                fault_counter++;
            }
            else{       // real reset of fault (count of 40)
                current_fault = 0;
                fault_counter = 0;
            }
        }
        

        //inverted for BMS relay
        if (bms_gate_state) { 
            output_reg &= ~(1 << BMS_fault_o); // Set fault output LOW
        } else {
            output_reg |= (1 << BMS_fault_o); // Set fault output HIGH
        }
        if (reset_button_state & !current_fault) { // if we're not faulted and the reset button is pushed
           faulted = 0; // clear the faults
        }

        if (PIR1 & (1 << 0)) {  // TMR1F
            PIR1 &= (1<<0);   // TMR1F
            blink_counter++; // 8.2ms

                            
            if ((current_fault == 1) || faulted) {
                if (blink_counter >= FREQ_SCALAR) {
                    fault_counter = 0;
                    blink_counter = 0; 
                    output_reg ^= (1 << red_PIC_o);   // turn on/off output
                    output_reg &= ~(1 << green_PIC_o); // turn off green light
                    faulted = 1;    // set fault flag
                }
            } 
            if (!faulted && !(blink_counter % 2)) { // weird modulo stuff to PWM to get the light to be dimmer
                output_reg &= ~(1 << green_PIC_o);
                if(!(blink_counter % 9)){   // comes out to 5% duty cycle after the dust settles in compilation
                    output_reg |= (1 << green_PIC_o);
                }
                output_reg &= ~(1 << red_PIC_o);
            }
            
        }

        // write outputs to the register
        GPIO = output_reg;
    }

    return 0;
}


