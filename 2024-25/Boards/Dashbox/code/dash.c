#include <stdint.h>

// MCU: STM32F103C6T6A (32kB flash, 10kB SRAM) - "low density" mcu

// Define register base addresses
#define RCC_BASE    0x40021000
#define GPIOC_BASE  0x40011000
#define FLASH_BASE  0x40022000
#define GPIOA_BASE  0x40010800
#define USART1_BASE 0x40013800
#define CAN1_BASE   0x40006400  // CAN1 base address for STM32F103 devices

// Define memory addresses for GPIO registers
#define RCC_APB2ENR     (*(volatile unsigned int *)(RCC_BASE + 0x18))
#define GPIOC_CRH       (*(volatile unsigned int *)(GPIOC_BASE + 0x04)) // Port C high register
#define GPIOC_BSRR      (*(volatile unsigned int *)(GPIOC_BASE + 0x10))
#define GPIOA_CRH       (*(volatile unsigned int *)(GPIOA_BASE + 0x04)) // Port A high register
#define GPIOA_BSRR      (*(volatile unsigned int *)(GPIOA_BASE + 0x10))

// Define clock registers
#define RCC_CR          (*(volatile unsigned int *)(RCC_BASE + 0x00))
#define RCC_CFGR        (*(volatile unsigned int *)(RCC_BASE + 0x04))
#define FLASH_ACR       (*(volatile unsigned int *)(FLASH_BASE + 0x00))

// Define USART1 registers
#define USART1_BRR      (*(volatile unsigned int *)(USART1_BASE + 0x08))
#define USART1_CR1      (*(volatile unsigned int *)(USART1_BASE + 0x0C))
#define USART1_DR       (*(volatile unsigned int *)(USART1_BASE + 0x04))
#define USART1_SR       (*(volatile unsigned int *)(USART1_BASE + 0x00))

// Define RCC_APB1ENR for enabling CAN clock (located at offset 0x1C)
#define RCC_APB1ENR     (*(volatile unsigned int *)(RCC_BASE + 0x1C))

// Define CAN1 registers
#define CAN1_MCR        (*(volatile unsigned int *)(CAN1_BASE + 0x00))
#define CAN1_MSR        (*(volatile unsigned int *)(CAN1_BASE + 0x04))
#define CAN1_TSR        (*(volatile unsigned int *)(CAN1_BASE + 0x08))
#define CAN1_BTR        (*(volatile unsigned int *)(CAN1_BASE + 0x1C))

// Transmit mailbox 0 registers
#define CAN1_TIR0       (*(volatile unsigned int *)(CAN1_BASE + 0x180))
#define CAN1_TDT0R      (*(volatile unsigned int *)(CAN1_BASE + 0x184))
#define CAN1_TDL0R      (*(volatile unsigned int *)(CAN1_BASE + 0x188))
#define CAN1_TDH0R      (*(volatile unsigned int *)(CAN1_BASE + 0x18C))

// Baud rates
#define UART_BAUD_RATE  115200
#define CAN_BAUD_RATE   125000
#define LED_PIN         13         // PC13

void simpleDelay(int num) {
    for (int i = 0; i < num; i++) {
        asm("nop");
    }
}

void usart1_send_char(char data) {
    while (!(USART1_SR & (1 << 7))); // Wait until transmit buffer is empty
    USART1_DR = data;
}

    
// usage: usart1_send_string("bruh\n");
void usart1_send_string(char *str) {
    while (*str) {
        usart1_send_char(*str++);
    }
}

// Function to convert an unsigned integer to hexadecimal string
void uint_to_hex_string(unsigned int val, char *hex_str) {
    const char hex_digits[] = "0123456789ABCDEF";
    hex_str[0] = '0';
    hex_str[1] = 'x';
    for (int i = 0; i < 8; i++) {
        hex_str[9 - i] = hex_digits[val & 0x0F];
        val >>= 4;
    }
    hex_str[10] = '\n';
    hex_str[11] = '\0'; // Null terminate the string
}

// function for transmitting can messages (over mailbox 0)
void can1_transmit(unsigned char dlc, int data_low, int data_high, int id){
    // Check if transmit mailbox 0 is empty
    if (CAN1_TSR & (1<<26)) {
        // Load mailbox 0:
        // Set Data Length Code (DLC) to 1
        CAN1_TDT0R = dlc;
        // Load the lower bytes into the low data register
        CAN1_TDL0R = data_low;
        // Load the higher bytes into the high data register
        CAN1_TDH0R = data_high;
        // Set standard identifier (shifted into bits 31:21) and request transmission (TXRQ)
        CAN1_TIR0 = (id << 21) | (1 << 0);
    }
}

// CAN setup code
void can_init(){

    // Enable CAN1 clock (CAN is on APB1; bit 25 in RCC_APB1ENR)
    RCC_APB1ENR |= (1 << 25);

    // Configure CAN pins:
    // PA11: CAN RX as input floating
    GPIOA_CRH &= ~(0xF << ((11 - 8) * 4));
    GPIOA_CRH |= (0b0100 << ((11 - 8) * 4));
    // PA12: CAN TX as alternate function push-pull, 50MHz
    GPIOA_CRH &= ~(0xF << ((12 - 8) * 4));
    GPIOA_CRH |= (0b1011 << ((12 - 8) * 4));
    
    // enable CAN loopback mode (if needed)
    //CAN1_BTR |= (1 << 30);  // LKBM bit, enables loopback mode

    // exit CAN sleep mode
    CAN1_MCR &= ~(1<<1);    

    // Enter CAN initialization mode
    CAN1_MCR |= (1<<0);
    
    while (!(CAN1_MSR & (1<<0)));  // wait until CAN acknowledges init mode
    
    // configure CAN bit timing for approximately 1 Mbit/s (assuming APB1 at 36MHz):
    // BRP = 2  => (BRP+1)=3, TS1 = 7 (i.e. 8 time quanta), TS2 = 2 (i.e. 3 time quanta), SJW = 0 (i.e. 1 time quantum)
    // Bit time = 1 (Sync) + 8 (TS1) + 3 (TS2) = 12 tq, so bit rate = 36MHz / (prescalar * 12) = 1 Mbit/s
    CAN1_BTR = (2 << 20) | (7 << 16);   // set time segment 2 to 3 time quanta, time segment 1 to 8 time quanta
    
    // set can baud rate
    CAN1_BTR |= (36000000 / (CAN_BAUD_RATE * 12)) - 1;  // baud rate prescalar

    // Exit CAN initialization mode
    CAN1_MCR &= ~(1 << 0);
    while (CAN1_MSR & (1 << 0));  // wait until it enters normal mode
}

void init_clks(){
    // System clock configuration
    RCC_CR |= (1 << 16);             // HSEON: Enable high-speed external oscillator
    while (!(RCC_CR & (1 << 17)));  // Wait until HSE is stable

    FLASH_ACR |= (0x02 << 0);       // Set flash latency to two wait states

    RCC_CFGR |= (1 << 16);          // PLLSRC: Use HSE as PLL source
    RCC_CFGR |= (0x07 << 18);       // PLLMUL: Multiply by 9 to achieve 72MHz


    RCC_CFGR |= (0b100 << 8);    // PPRE1 prescalar set to 2 (36MHz, max clk rate)

    RCC_CR |= (1 << 24);            // PLLON: Enable PLL
    while (!(RCC_CR & (1 << 25)));  // Wait for PLL ready

    RCC_CFGR |= (0x02 << 0);        // SW: Set PLL as system clock
    while ((RCC_CFGR & 0x03) != 0x02); // Wait until PLL is used as system clock

    // Enable clocks for GPIOA, GPIOC and USART1
    RCC_APB2ENR |= (1 << 2);        // IOPAEN: Enable GPIOA clock
    RCC_APB2ENR |= (1 << 4);        // IOPCEN: Enable GPIOC clock
    RCC_APB2ENR |= (1 << 14);       // USART1 clock enable
}

void uart1_init(){
    // Configure USART1 pins:
    // PA9 (USART1_TX) as alternate function push-pull, 50MHz
    GPIOA_CRH &= ~(0xF << ((9 - 8) * 4));
    GPIOA_CRH |= (0b1011 << ((9 - 8) * 4));
    // PA10 (USART1_RX) as floating input
    GPIOA_CRH &= ~(0xF << ((10 - 8) * 4));
    GPIOA_CRH |= (0b0100 << ((10 - 8) * 4));

    // Set USART1 baud rate and enable
    USART1_BRR = (72000000 / UART_BAUD_RATE);    // SYSCLK / baudrate
    USART1_CR1 |= (1 << 3);  // Enable transmitter
    USART1_CR1 |= (1 << 13); // Enable USART1
}

volatile float blink_multiplier = 0.5;

int main(void) {
    init_clks();

    // Configure PC13 as output, push-pull, 2MHz (for LED)
    GPIOC_CRH &= ~(0xF << ((LED_PIN - 8) * 4));
    GPIOC_CRH |= (0x02 << ((LED_PIN - 8) * 4));

    uart1_init();
    can_init();

    char msr_hex_string[12];

    while (1) {
        // Blink LED and send USART message
        GPIOC_BSRR = (1 << (LED_PIN + 16)); // Turn off LED
        
        // uart printing for debugging
        // uint_to_hex_string(CAN1_MCR, msr_hex_string); // Convert MSR to hex string
        // usart1_send_string(msr_hex_string); // Send MSR value over UART
        simpleDelay(500000 * blink_multiplier);
        GPIOC_BSRR = (1 << LED_PIN);  // Turn on LED
        simpleDelay(500000 * blink_multiplier);
        
        // usage: can1_transmit(dlc, lower_data, higher_data, id)
        // transmit with data length code of 8, with random data, and an ID of 123
        can1_transmit(8, 0x12345678, 0x9ABCDEF0, 0x123);
    }

    return 0;
}



void __attribute__((weak, naked)) reset_handler(void) {
    main();
}


__attribute__((section(".vectors")))
struct {
    unsigned int *initial_sp_value;
    void (*reset)(void);
    void (*nmi)(void);
    void (*hard_fault)(void);
    void (*memory_manage_fault)(void);
    void (*bus_fault)(void);
    void (*usage_fault)(void);
    void (*reserved_x001c[4])(void);
    void (*sv_call)(void);
    void (*debug_monitor)(void);
    void (*reserved_x0034)(void);
    void (*pend_sv)(void);
    void (*systick)(void);
    void (*irq[68])(void);
} vector_table = {
    .initial_sp_value = (unsigned int *)0x20002800,  // Initialize stack pointer to top of the sram (10*2^10)
    .reset = reset_handler,
};
