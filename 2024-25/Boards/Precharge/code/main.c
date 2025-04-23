#include <stdint.h>  // For standard integer types like uint8_t, uint16_t
#include <pic12f609.h> // Include the SDCC header file for PIC12F609

// configuration bits, for PIC12F609 The CONFIG register is at address 0x2007
static __code uint16_t __at(0x2007) configword1 = 0x00D4;  // BOR disabled, 8MHz internal oscillator, Code protection disabled, MCLR tied to VDD, PWRT disabled, WDT disabled, Internal Oscillator selected with I/O outputs on GP4 and GP5
// 0x00D4 for 8MHz

#define F_PRE_PIN 0 // Pre-resistor voltage-to-frequency measurement
#define F_POST_PIN 1    // Post-resistor voltage-to-frequency measurement
#define SDC_PIN 3   // SDC in signal is on GP3
#define ERROR_PIN 5 // Error signal to dash is on GP5
#define AIR_PIN 4   // Mosfet for AIR+ is on GP4
#define CHR_PIN 2   // Mosfet for preCHaRge relay is on GP2

// define registers to be used in assembly
unsigned char __at(0x40) DelayCount;   // Used for the delay loop
unsigned char __at(0x41) Temp;         // temporary register for shifting the byte
unsigned char __at(0x42) BitCounter;   // counts 8 bits

// Global flag variable, accessible by both the ISR and the main loop.
volatile uint8_t isr_flag = 0;

// Function to introduce a delay (crude delay, can be improved)
void delay(uint16_t count) { // Changed to uint16_t to avoid overflow.
    uint16_t i;
    for (i = 0; i < count; i++) {
        // This loop does nothing but consume time - basic delay
    }
}

void nop(void){ // nop function, delays 1/4MHz seconds
    __asm
        nop
    __endasm;
}

void delay_cycles(uint16_t cycles) {
    while (cycles--) {
        __asm nop __endasm;
    }
}

// bit bang assembly uart (19200 baud), no parity, idle high, LSB first
// naked so that no prologue/epilogue is generated.
// it is assumed that the parameter (byte to transmit) is passed in the W register
// delay loops are precisely tuned for 8MHz baud rate of 19200
void uart_tx(uint8_t data) __naked {
    __asm
        ; ----- Start Bit: drive GP5 LOW -----
        BANKSEL _GPIO
        BCF     _GPIO, 5             ; Set GP5 low (start bit)

        MOVWF   _Temp               ; Save the transmitted byte into Temp (from W)

        BANKSEL _DelayCount
        MOVLW   32                   ; Load constant 34 into W
        MOVWF   _DelayCount         ; Store it in DelayCount (address 0x20)
DelayLoop_Start:
        DECFSZ  _DelayCount, F      ; Decrement DelayCount until zero
        GOTO    DelayLoop_Start
        
        ;BCF     _GPIO, 5
        ; ----- Transmit 8 Data Bits (LSB first) -----
        MOVLW   8
        MOVWF   _BitCounter         ; Set BitCounter = 8

UART_Send_Bit:
        BTFSS   _Temp, 0            ; Test LSB of Temp; if bit0 is 1, skip next instruction
        GOTO    Bit0_Zero           ; If bit is 0, branch to Bit0_Zero
        ; --- Bit is 1: set GP5 high ---
        BANKSEL _GPIO
        BSF     _GPIO, 5             ; Set GP5 high
        goto    BitDelay
Bit0_Zero:
        ; --- Bit is 0: ensure GP5 is low ---
        BANKSEL _GPIO
        BCF     _GPIO, 5             ; Set GP5 low
BitDelay:
        MOVLW   30
        MOVWF   _DelayCount         ; Reload DelayCount with 34
DelayLoop_Data:
        DECFSZ  _DelayCount, F
        GOTO    DelayLoop_Data

        RRF     _Temp, F            ; Shift Temp right through Carry (next bit becomes LSB)
        DECFSZ  _BitCounter, F
        GOTO    UART_Send_Bit       ; Loop for all 8 bits

        ; ----- Stop Bit: drive ERROR_PIN HIGH -----
        BANKSEL _GPIO
        BSF     GPIO, 5             ; Set GP5 high (stop bit)
        MOVLW   31
        MOVWF   _DelayCount
DelayLoop_Stop:
        DECFSZ  _DelayCount, F
        GOTO    DelayLoop_Stop
        RETURN
    __endasm;
}

// Transmit 16-bit count using UART
void transmit_count(uint16_t count) {
    uart_tx((count >> 8) & 0xFF);  // Send high byte
    uart_tx(count & 0xFF);         // Send low byte
}

int main(void) {
    // Configure outputs, error signal to dash, controls for relays
    TRISIO &= ~((1 << ERROR_PIN)|(1 << AIR_PIN)|(1 << CHR_PIN));  // Clear the appropriate TRISIO bit to make it an output.
    // Configure inputs: two frequency measurements, SDC pin
    TRISIO |= ((1 << F_PRE_PIN)|(1 << F_POST_PIN)|(1 << SDC_PIN));
     

    // Error pin idles high for sending info
    GPIO |= (1 << ERROR_PIN);

    // turn off all interrupts on change
    IOC = 0; 

    // timer 1 enabled, 1:1 prescalar
    T1CON = 0x01;    
    
    // timer 1 clock source Fosc
    CMCON1 = 0x10;

    // Timer 1 interrupt enable
    PIE1 = 0x01;
    
    PIR1 |= 0;
    // GPIO pullups disabled
    OPTION_REG = 0x80;
    
    // Global and peripheral interrupts enabled, GPIO pin change interrupts disabled
    INTCON = 0xC0;
     
    delay_cycles(50000);
    //uart_tx(INTCON);
    delay_cycles(50000);
    // Enable TIMER1 Interrupt
    PIE1 |= (1 << TMR1IE);

    // disable all weak pull-ups
    WPU = 0;
    // switch to digital i/o for gp0, 1, 3
    ANSEL = 0;

    // Variables for keeping track of old pin values
    unsigned char pre_pin_old = 0;
    unsigned char post_pin_old = 0;
    
    // Variables for storing newly read pin values
    unsigned char pre_pin_new = 0;
    unsigned char post_pin_new = 0;
   
    unsigned char gpio_reg = 0; 
    unsigned char start_flag = 0;
    unsigned char charged_flag = 0;

    unsigned char start_count = 0;
    unsigned char ratio = 0;

    // Variables for counting transitions
    unsigned int pre_pin_count = 0;
    unsigned int post_pin_count = 0;
    
    // Interrupts weren't working due to the microcontroller refusing to call the ISR
    // Perhaps because of a compilation issue with SDCC
    // So resorted to polling
    while (1) {
        gpio_reg = GPIO;
        if(gpio_reg & (1 << SDC_PIN) & !start_flag){
            GPIO |= (1 << CHR_PIN); // start precharging
            
            start_flag = 1;
            post_pin_new = gpio_reg & (1 << F_POST_PIN);
            pre_pin_new = gpio_reg & (1 << F_PRE_PIN);
            //uart_tx(post_pin_new);
            //uart_tx(pre_pin_new); 
            if(pre_pin_new != pre_pin_old){ // if the value on pre_pin has changed
                pre_pin_count += 1;
                pre_pin_old = pre_pin_new;
            }
            if(post_pin_new != post_pin_old){ // if the value on post_pin has changed
                post_pin_count += 1;
                post_pin_old = post_pin_new;
            }
        }
        else{   // SDC went low
            pre_pin_count = 0;
            post_pin_count = 0;
            start_flag = 0;
            charged_flag = 0;
            start_count = 0;
            GPIO &= ~((1 << AIR_PIN)|(1 << CHR_PIN));
        }
        if(isr_flag){
            // send the values over the error pin
            pre_pin_count >>= 2;
            post_pin_count <<= 3;
            
            ratio = post_pin_count / pre_pin_count;
            transmit_count(ratio);
            isr_flag = 0;
            
            pre_pin_count = 0;
            post_pin_count = 0;
            
            // Clear timer count
            TMR1H = 0;
            TMR1L = 0;         
            
            if(start_flag & !charged_flag){
                start_count++;
                if(start_count <= 3){
                    if((ratio >= 30) & (ratio <= 32)){  // if we charged up too fast
                        GPIO &= ~((1 << AIR_PIN)|(1 << CHR_PIN));   // turn off relays
                        while(1);   // enter infinite loop, precharge relay possibly welded
                    }
                }
                else if((start_count >= 7) & (start_count <= 10)){  // correct timing
                    if((ratio >= 31) & (ratio <= 32)) { // succesfully precharged
                        GPIO |= (1 << AIR_PIN); // turn on AIR
                        GPIO &= ~(1 << CHR_PIN);    // turn off Precharge relay
                        charged_flag = 1;
                    }
                    else{   // charged up too slow, possible that discharge is welded
                        GPIO &= ~((1 << AIR_PIN)|(1 << CHR_PIN));   // turn off relays
                        while(1);   // enter infinite loop, discharge relay possible welded
                    }
                }
            }
        }
    }
    return 0;
}

// SDCC fucks up the compilation of this ISR, so it has to be coded in assembly
// ISR called once every 8.2ms
// ISR_period = 65,536 * 1 / 8,000,000
void isr(void) __interrupt(0) __naked {
    __asm
        ; Send 0x53 over UART for debugging
        ;MOVLW  0xFF
        ;CALL   _uart_tx
;        BTFSS   _GPIO, 5
;        GOTO    set_bit
;        BCF     _GPIO, 5
;        GOTO    toggle_end
;set_bit:
;        BSF _GPIO, 5
;toggle_end:
        MOVLW   0x01
        MOVWF   _isr_flag

        ; clear GPIO interrupt flag 
        BCF     _INTCON, 0
        ; clear timer0 interrupt flag
        ;BCF     _INTCON, 2
        ; clear timer1 interrupt flag
        BCF     _PIR1, 0

        RETFIE
    __endasm;
}

