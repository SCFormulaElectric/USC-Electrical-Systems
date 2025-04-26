/*
 * File:   picmain.c
 * Author: timxw
 *
 * Created on April 25, 2025, 5:12 PM
 */
#pragma config FOSC = INTOSCIO // Oscillator Selection: Internal oscillator, I/O function on GP4/OSC2/CLKOUT pin and GP5/OSC1/CLKIN
#pragma config WDTE = OFF      // Watchdog Timer Enable: WDT disabled
#pragma config PWRTE = OFF     // Power-up Timer Enable: PWRT disabled
#pragma config MCLRE = OFF     // MCLR Pin Function Select: MCLR pin function is digital input, MCLR internally tied to VDD
#pragma config BOREN = OFF     // Brown-out Reset Enable: BOR disabled
#pragma config CP = OFF        // Code Protection bit: Program memory code protection is disabled
#pragma config CPD = OFF 

#include <xc.h>

void main(void) {
    return;
}
