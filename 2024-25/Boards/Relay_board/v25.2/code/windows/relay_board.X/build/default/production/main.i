# 1 "main.c"
# 1 "<built-in>" 1
# 1 "<built-in>" 3
# 285 "<built-in>" 3
# 1 "<command line>" 1
# 1 "<built-in>" 2
# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/language_support.h" 1 3
# 2 "<built-in>" 2
# 1 "main.c" 2
# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdint.h" 1 3



# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/musl_xc8.h" 1 3
# 5 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdint.h" 2 3
# 26 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdint.h" 3
# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/alltypes.h" 1 3
# 133 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/alltypes.h" 3
typedef unsigned short uintptr_t;
# 148 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/alltypes.h" 3
typedef short intptr_t;
# 164 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/alltypes.h" 3
typedef signed char int8_t;




typedef short int16_t;




typedef __int24 int24_t;




typedef long int32_t;
# 192 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/alltypes.h" 3
typedef int32_t intmax_t;







typedef unsigned char uint8_t;




typedef unsigned short uint16_t;




typedef __uint24 uint24_t;




typedef unsigned long uint32_t;
# 233 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/alltypes.h" 3
typedef uint32_t uintmax_t;
# 27 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdint.h" 2 3

typedef int8_t int_fast8_t;




typedef int8_t int_least8_t;
typedef int16_t int_least16_t;

typedef int24_t int_least24_t;
typedef int24_t int_fast24_t;

typedef int32_t int_least32_t;




typedef uint8_t uint_fast8_t;




typedef uint8_t uint_least8_t;
typedef uint16_t uint_least16_t;

typedef uint24_t uint_least24_t;
typedef uint24_t uint_fast24_t;

typedef uint32_t uint_least32_t;
# 148 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdint.h" 3
# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/stdint.h" 1 3
typedef int16_t int_fast16_t;
typedef int32_t int_fast32_t;
typedef uint16_t uint_fast16_t;
typedef uint32_t uint_fast32_t;
# 149 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdint.h" 2 3
# 2 "main.c" 2
# 1 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 1 3
# 44 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/__at.h" 1 3
# 45 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 2 3







extern volatile unsigned char INDF __attribute__((address(0x000)));

__asm("INDF equ 00h");




extern volatile unsigned char TMR0 __attribute__((address(0x001)));

__asm("TMR0 equ 01h");




extern volatile unsigned char PCL __attribute__((address(0x002)));

__asm("PCL equ 02h");




extern volatile unsigned char STATUS __attribute__((address(0x003)));

__asm("STATUS equ 03h");


typedef union {
    struct {
        unsigned C :1;
        unsigned DC :1;
        unsigned Z :1;
        unsigned nPD :1;
        unsigned nTO :1;
        unsigned RP :2;
        unsigned IRP :1;
    };
    struct {
        unsigned :5;
        unsigned RP0 :1;
        unsigned RP1 :1;
    };
    struct {
        unsigned CARRY :1;
        unsigned :1;
        unsigned ZERO :1;
    };
} STATUSbits_t;
extern volatile STATUSbits_t STATUSbits __attribute__((address(0x003)));
# 159 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char FSR __attribute__((address(0x004)));

__asm("FSR equ 04h");




extern volatile unsigned char GPIO __attribute__((address(0x005)));

__asm("GPIO equ 05h");


extern volatile unsigned char PORTA __attribute__((address(0x005)));

__asm("PORTA equ 05h");


typedef union {
    struct {
        unsigned GP0 :1;
        unsigned GP1 :1;
        unsigned GP2 :1;
        unsigned GP3 :1;
        unsigned GP4 :1;
        unsigned GP5 :1;
    };
    struct {
        unsigned GPIO0 :1;
        unsigned GPIO1 :1;
        unsigned GPIO2 :1;
        unsigned GPIO3 :1;
        unsigned GPIO4 :1;
        unsigned GPIO5 :1;
    };
    struct {
        unsigned RA0 :1;
        unsigned RA1 :1;
        unsigned RA2 :1;
        unsigned RA3 :1;
        unsigned RA4 :1;
        unsigned RA5 :1;
    };
} GPIObits_t;
extern volatile GPIObits_t GPIObits __attribute__((address(0x005)));
# 295 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
typedef union {
    struct {
        unsigned GP0 :1;
        unsigned GP1 :1;
        unsigned GP2 :1;
        unsigned GP3 :1;
        unsigned GP4 :1;
        unsigned GP5 :1;
    };
    struct {
        unsigned GPIO0 :1;
        unsigned GPIO1 :1;
        unsigned GPIO2 :1;
        unsigned GPIO3 :1;
        unsigned GPIO4 :1;
        unsigned GPIO5 :1;
    };
    struct {
        unsigned RA0 :1;
        unsigned RA1 :1;
        unsigned RA2 :1;
        unsigned RA3 :1;
        unsigned RA4 :1;
        unsigned RA5 :1;
    };
} PORTAbits_t;
extern volatile PORTAbits_t PORTAbits __attribute__((address(0x005)));
# 416 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char PCLATH __attribute__((address(0x00A)));

__asm("PCLATH equ 0Ah");




extern volatile unsigned char INTCON __attribute__((address(0x00B)));

__asm("INTCON equ 0Bh");


typedef union {
    struct {
        unsigned GPIF :1;
        unsigned INTF :1;
        unsigned TMR0IF :1;
        unsigned GPIE :1;
        unsigned INTE :1;
        unsigned TMR0IE :1;
        unsigned PEIE :1;
        unsigned GIE :1;
    };
    struct {
        unsigned :2;
        unsigned T0IF :1;
        unsigned :2;
        unsigned T0IE :1;
    };
} INTCONbits_t;
extern volatile INTCONbits_t INTCONbits __attribute__((address(0x00B)));
# 501 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char PIR1 __attribute__((address(0x00C)));

__asm("PIR1 equ 0Ch");


typedef union {
    struct {
        unsigned TMR1IF :1;
        unsigned :2;
        unsigned C1IF :1;
    };
    struct {
        unsigned T1IF :1;
        unsigned :2;
        unsigned CMIF :1;
    };
} PIR1bits_t;
extern volatile PIR1bits_t PIR1bits __attribute__((address(0x00C)));
# 543 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned short TMR1 __attribute__((address(0x00E)));

__asm("TMR1 equ 0Eh");




extern volatile unsigned char TMR1L __attribute__((address(0x00E)));

__asm("TMR1L equ 0Eh");




extern volatile unsigned char TMR1H __attribute__((address(0x00F)));

__asm("TMR1H equ 0Fh");




extern volatile unsigned char T1CON __attribute__((address(0x010)));

__asm("T1CON equ 010h");


typedef union {
    struct {
        unsigned TMR1ON :1;
        unsigned TMR1CS :1;
        unsigned nT1SYNC :1;
        unsigned T1OSCEN :1;
        unsigned T1CKPS :2;
        unsigned TMR1GE :1;
        unsigned T1GINV :1;
    };
    struct {
        unsigned :4;
        unsigned T1CKPS0 :1;
        unsigned T1CKPS1 :1;
    };
} T1CONbits_t;
extern volatile T1CONbits_t T1CONbits __attribute__((address(0x010)));
# 635 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char VRCON __attribute__((address(0x019)));

__asm("VRCON equ 019h");


typedef union {
    struct {
        unsigned VR :4;
        unsigned FBREN :1;
        unsigned VRR :1;
        unsigned :1;
        unsigned C1VREN :1;
    };
    struct {
        unsigned VR0 :1;
        unsigned VR1 :1;
        unsigned VR2 :1;
        unsigned VR3 :1;
        unsigned FVREN :1;
        unsigned :2;
        unsigned CMVREN :1;
    };
    struct {
        unsigned :4;
        unsigned VP6EN :1;
    };
} VRCONbits_t;
extern volatile VRCONbits_t VRCONbits __attribute__((address(0x019)));
# 722 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char CMCON0 __attribute__((address(0x01A)));

__asm("CMCON0 equ 01Ah");


typedef union {
    struct {
        unsigned C1CH :1;
        unsigned :1;
        unsigned C1R :1;
        unsigned :1;
        unsigned C1POL :1;
        unsigned C1OE :1;
        unsigned C1OUT :1;
        unsigned C1ON :1;
    };
    struct {
        unsigned C1CH0 :1;
        unsigned :1;
        unsigned CMR :1;
        unsigned :1;
        unsigned CMPOL :1;
        unsigned CMOE :1;
        unsigned COUT :1;
        unsigned CMON :1;
    };
    struct {
        unsigned CMCH :1;
    };
} CMCON0bits_t;
extern volatile CMCON0bits_t CMCON0bits __attribute__((address(0x01A)));
# 822 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char CMCON1 __attribute__((address(0x01C)));

__asm("CMCON1 equ 01Ch");


typedef union {
    struct {
        unsigned C1SYNC :1;
        unsigned T1GSS :1;
        unsigned :1;
        unsigned C1HYS :1;
        unsigned T1ACS :1;
    };
    struct {
        unsigned CMSYNC :1;
        unsigned :2;
        unsigned CMHYS :1;
    };
} CMCON1bits_t;
extern volatile CMCON1bits_t CMCON1bits __attribute__((address(0x01C)));
# 876 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char OPTION_REG __attribute__((address(0x081)));

__asm("OPTION_REG equ 081h");


typedef union {
    struct {
        unsigned PS :3;
        unsigned PSA :1;
        unsigned T0SE :1;
        unsigned T0CS :1;
        unsigned INTEDG :1;
        unsigned nGPPU :1;
    };
    struct {
        unsigned PS0 :1;
        unsigned PS1 :1;
        unsigned PS2 :1;
    };
} OPTION_REGbits_t;
extern volatile OPTION_REGbits_t OPTION_REGbits __attribute__((address(0x081)));
# 946 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char TRISIO __attribute__((address(0x085)));

__asm("TRISIO equ 085h");


extern volatile unsigned char TRISA __attribute__((address(0x085)));

__asm("TRISA equ 085h");


typedef union {
    struct {
        unsigned TRISIO0 :1;
        unsigned TRISIO1 :1;
        unsigned TRISIO2 :1;
        unsigned TRISIO3 :1;
        unsigned TRISIO4 :1;
        unsigned TRISIO5 :1;
    };
    struct {
        unsigned TRISA0 :1;
        unsigned TRISA1 :1;
        unsigned TRISA2 :1;
        unsigned TRISA3 :1;
        unsigned TRISA4 :1;
        unsigned TRISA5 :1;
    };
} TRISIObits_t;
extern volatile TRISIObits_t TRISIObits __attribute__((address(0x085)));
# 1037 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
typedef union {
    struct {
        unsigned TRISIO0 :1;
        unsigned TRISIO1 :1;
        unsigned TRISIO2 :1;
        unsigned TRISIO3 :1;
        unsigned TRISIO4 :1;
        unsigned TRISIO5 :1;
    };
    struct {
        unsigned TRISA0 :1;
        unsigned TRISA1 :1;
        unsigned TRISA2 :1;
        unsigned TRISA3 :1;
        unsigned TRISA4 :1;
        unsigned TRISA5 :1;
    };
} TRISAbits_t;
extern volatile TRISAbits_t TRISAbits __attribute__((address(0x085)));
# 1120 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char PIE1 __attribute__((address(0x08C)));

__asm("PIE1 equ 08Ch");


typedef union {
    struct {
        unsigned TMR1IE :1;
        unsigned :2;
        unsigned C1IE :1;
    };
    struct {
        unsigned T1IE :1;
        unsigned :2;
        unsigned CMIE :1;
    };
} PIE1bits_t;
extern volatile PIE1bits_t PIE1bits __attribute__((address(0x08C)));
# 1162 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char PCON __attribute__((address(0x08E)));

__asm("PCON equ 08Eh");


typedef union {
    struct {
        unsigned nBOR :1;
        unsigned nPOR :1;
    };
    struct {
        unsigned nBOD :1;
    };
} PCONbits_t;
extern volatile PCONbits_t PCONbits __attribute__((address(0x08E)));
# 1196 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char OSCTUNE __attribute__((address(0x090)));

__asm("OSCTUNE equ 090h");


typedef union {
    struct {
        unsigned TUN :5;
    };
    struct {
        unsigned TUN0 :1;
        unsigned TUN1 :1;
        unsigned TUN2 :1;
        unsigned TUN3 :1;
        unsigned TUN4 :1;
    };
} OSCTUNEbits_t;
extern volatile OSCTUNEbits_t OSCTUNEbits __attribute__((address(0x090)));
# 1248 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char WPU __attribute__((address(0x095)));

__asm("WPU equ 095h");


extern volatile unsigned char WPUA __attribute__((address(0x095)));

__asm("WPUA equ 095h");


typedef union {
    struct {
        unsigned WPUA0 :1;
        unsigned WPUA1 :1;
        unsigned WPUA2 :1;
        unsigned :1;
        unsigned WPUA4 :1;
        unsigned WPUA5 :1;
    };
    struct {
        unsigned WPU0 :1;
        unsigned WPU1 :1;
        unsigned WPU2 :1;
        unsigned :1;
        unsigned WPU4 :1;
        unsigned WPU5 :1;
    };
} WPUbits_t;
extern volatile WPUbits_t WPUbits __attribute__((address(0x095)));
# 1329 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
typedef union {
    struct {
        unsigned WPUA0 :1;
        unsigned WPUA1 :1;
        unsigned WPUA2 :1;
        unsigned :1;
        unsigned WPUA4 :1;
        unsigned WPUA5 :1;
    };
    struct {
        unsigned WPU0 :1;
        unsigned WPU1 :1;
        unsigned WPU2 :1;
        unsigned :1;
        unsigned WPU4 :1;
        unsigned WPU5 :1;
    };
} WPUAbits_t;
extern volatile WPUAbits_t WPUAbits __attribute__((address(0x095)));
# 1402 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char IOC __attribute__((address(0x096)));

__asm("IOC equ 096h");


extern volatile unsigned char IOCA __attribute__((address(0x096)));

__asm("IOCA equ 096h");


typedef union {
    struct {
        unsigned IOC0 :1;
        unsigned IOC1 :1;
        unsigned IOC2 :1;
        unsigned IOC3 :1;
        unsigned IOC4 :1;
        unsigned IOC5 :1;
    };
    struct {
        unsigned IOCA0 :1;
        unsigned IOCA1 :1;
        unsigned IOCA2 :1;
        unsigned IOCA3 :1;
        unsigned IOCA4 :1;
        unsigned IOCA5 :1;
    };
} IOCbits_t;
extern volatile IOCbits_t IOCbits __attribute__((address(0x096)));
# 1493 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
typedef union {
    struct {
        unsigned IOC0 :1;
        unsigned IOC1 :1;
        unsigned IOC2 :1;
        unsigned IOC3 :1;
        unsigned IOC4 :1;
        unsigned IOC5 :1;
    };
    struct {
        unsigned IOCA0 :1;
        unsigned IOCA1 :1;
        unsigned IOCA2 :1;
        unsigned IOCA3 :1;
        unsigned IOCA4 :1;
        unsigned IOCA5 :1;
    };
} IOCAbits_t;
extern volatile IOCAbits_t IOCAbits __attribute__((address(0x096)));
# 1576 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile unsigned char ANSEL __attribute__((address(0x09F)));

__asm("ANSEL equ 09Fh");


typedef union {
    struct {
        unsigned ANS :4;
        unsigned ADCS :3;
    };
    struct {
        unsigned ANS0 :1;
        unsigned ANS1 :1;
        unsigned :1;
        unsigned ANS3 :1;
    };
} ANSELbits_t;
extern volatile ANSELbits_t ANSELbits __attribute__((address(0x09F)));
# 1633 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include\\proc/pic12f609.h" 3
extern volatile __bit ANS0 __attribute__((address(0x4F8)));


extern volatile __bit ANS1 __attribute__((address(0x4F9)));


extern volatile __bit ANS3 __attribute__((address(0x4FB)));


extern volatile __bit C1CH __attribute__((address(0xD0)));


extern volatile __bit C1CH0 __attribute__((address(0xD0)));


extern volatile __bit C1HYS __attribute__((address(0xE3)));


extern volatile __bit C1IE __attribute__((address(0x463)));


extern volatile __bit C1IF __attribute__((address(0x63)));


extern volatile __bit C1OE __attribute__((address(0xD5)));


extern volatile __bit C1ON __attribute__((address(0xD7)));


extern volatile __bit C1OUT __attribute__((address(0xD6)));


extern volatile __bit C1POL __attribute__((address(0xD4)));


extern volatile __bit C1R __attribute__((address(0xD2)));


extern volatile __bit C1SYNC __attribute__((address(0xE0)));


extern volatile __bit C1VREN __attribute__((address(0xCF)));


extern volatile __bit CARRY __attribute__((address(0x18)));


extern volatile __bit CMCH __attribute__((address(0xD0)));


extern volatile __bit CMHYS __attribute__((address(0xE3)));


extern volatile __bit CMIE __attribute__((address(0x463)));


extern volatile __bit CMIF __attribute__((address(0x63)));


extern volatile __bit CMOE __attribute__((address(0xD5)));


extern volatile __bit CMON __attribute__((address(0xD7)));


extern volatile __bit CMPOL __attribute__((address(0xD4)));


extern volatile __bit CMR __attribute__((address(0xD2)));


extern volatile __bit CMSYNC __attribute__((address(0xE0)));


extern volatile __bit CMVREN __attribute__((address(0xCF)));


extern volatile __bit COUT __attribute__((address(0xD6)));


extern volatile __bit DC __attribute__((address(0x19)));


extern volatile __bit FBREN __attribute__((address(0xCC)));


extern volatile __bit FVREN __attribute__((address(0xCC)));


extern volatile __bit GIE __attribute__((address(0x5F)));


extern volatile __bit GP0 __attribute__((address(0x28)));


extern volatile __bit GP1 __attribute__((address(0x29)));


extern volatile __bit GP2 __attribute__((address(0x2A)));


extern volatile __bit GP3 __attribute__((address(0x2B)));


extern volatile __bit GP4 __attribute__((address(0x2C)));


extern volatile __bit GP5 __attribute__((address(0x2D)));


extern volatile __bit GPIE __attribute__((address(0x5B)));


extern volatile __bit GPIF __attribute__((address(0x58)));


extern volatile __bit GPIO0 __attribute__((address(0x28)));


extern volatile __bit GPIO1 __attribute__((address(0x29)));


extern volatile __bit GPIO2 __attribute__((address(0x2A)));


extern volatile __bit GPIO3 __attribute__((address(0x2B)));


extern volatile __bit GPIO4 __attribute__((address(0x2C)));


extern volatile __bit GPIO5 __attribute__((address(0x2D)));


extern volatile __bit INTE __attribute__((address(0x5C)));


extern volatile __bit INTEDG __attribute__((address(0x40E)));


extern volatile __bit INTF __attribute__((address(0x59)));


extern volatile __bit IOC0 __attribute__((address(0x4B0)));


extern volatile __bit IOC1 __attribute__((address(0x4B1)));


extern volatile __bit IOC2 __attribute__((address(0x4B2)));


extern volatile __bit IOC3 __attribute__((address(0x4B3)));


extern volatile __bit IOC4 __attribute__((address(0x4B4)));


extern volatile __bit IOC5 __attribute__((address(0x4B5)));


extern volatile __bit IOCA0 __attribute__((address(0x4B0)));


extern volatile __bit IOCA1 __attribute__((address(0x4B1)));


extern volatile __bit IOCA2 __attribute__((address(0x4B2)));


extern volatile __bit IOCA3 __attribute__((address(0x4B3)));


extern volatile __bit IOCA4 __attribute__((address(0x4B4)));


extern volatile __bit IOCA5 __attribute__((address(0x4B5)));


extern volatile __bit IRP __attribute__((address(0x1F)));


extern volatile __bit PEIE __attribute__((address(0x5E)));


extern volatile __bit PS0 __attribute__((address(0x408)));


extern volatile __bit PS1 __attribute__((address(0x409)));


extern volatile __bit PS2 __attribute__((address(0x40A)));


extern volatile __bit PSA __attribute__((address(0x40B)));


extern volatile __bit RA0 __attribute__((address(0x28)));


extern volatile __bit RA1 __attribute__((address(0x29)));


extern volatile __bit RA2 __attribute__((address(0x2A)));


extern volatile __bit RA3 __attribute__((address(0x2B)));


extern volatile __bit RA4 __attribute__((address(0x2C)));


extern volatile __bit RA5 __attribute__((address(0x2D)));


extern volatile __bit RP0 __attribute__((address(0x1D)));


extern volatile __bit RP1 __attribute__((address(0x1E)));


extern volatile __bit T0CS __attribute__((address(0x40D)));


extern volatile __bit T0IE __attribute__((address(0x5D)));


extern volatile __bit T0IF __attribute__((address(0x5A)));


extern volatile __bit T0SE __attribute__((address(0x40C)));


extern volatile __bit T1ACS __attribute__((address(0xE4)));


extern volatile __bit T1CKPS0 __attribute__((address(0x84)));


extern volatile __bit T1CKPS1 __attribute__((address(0x85)));


extern volatile __bit T1GINV __attribute__((address(0x87)));


extern volatile __bit T1GSS __attribute__((address(0xE1)));


extern volatile __bit T1IE __attribute__((address(0x460)));


extern volatile __bit T1IF __attribute__((address(0x60)));


extern volatile __bit T1OSCEN __attribute__((address(0x83)));


extern volatile __bit TMR0IE __attribute__((address(0x5D)));


extern volatile __bit TMR0IF __attribute__((address(0x5A)));


extern volatile __bit TMR1CS __attribute__((address(0x81)));


extern volatile __bit TMR1GE __attribute__((address(0x86)));


extern volatile __bit TMR1IE __attribute__((address(0x460)));


extern volatile __bit TMR1IF __attribute__((address(0x60)));


extern volatile __bit TMR1ON __attribute__((address(0x80)));


extern volatile __bit TRISA0 __attribute__((address(0x428)));


extern volatile __bit TRISA1 __attribute__((address(0x429)));


extern volatile __bit TRISA2 __attribute__((address(0x42A)));


extern volatile __bit TRISA3 __attribute__((address(0x42B)));


extern volatile __bit TRISA4 __attribute__((address(0x42C)));


extern volatile __bit TRISA5 __attribute__((address(0x42D)));


extern volatile __bit TRISIO0 __attribute__((address(0x428)));


extern volatile __bit TRISIO1 __attribute__((address(0x429)));


extern volatile __bit TRISIO2 __attribute__((address(0x42A)));


extern volatile __bit TRISIO3 __attribute__((address(0x42B)));


extern volatile __bit TRISIO4 __attribute__((address(0x42C)));


extern volatile __bit TRISIO5 __attribute__((address(0x42D)));


extern volatile __bit TUN0 __attribute__((address(0x480)));


extern volatile __bit TUN1 __attribute__((address(0x481)));


extern volatile __bit TUN2 __attribute__((address(0x482)));


extern volatile __bit TUN3 __attribute__((address(0x483)));


extern volatile __bit TUN4 __attribute__((address(0x484)));


extern volatile __bit VP6EN __attribute__((address(0xCC)));


extern volatile __bit VR0 __attribute__((address(0xC8)));


extern volatile __bit VR1 __attribute__((address(0xC9)));


extern volatile __bit VR2 __attribute__((address(0xCA)));


extern volatile __bit VR3 __attribute__((address(0xCB)));


extern volatile __bit VRR __attribute__((address(0xCD)));


extern volatile __bit WPU0 __attribute__((address(0x4A8)));


extern volatile __bit WPU1 __attribute__((address(0x4A9)));


extern volatile __bit WPU2 __attribute__((address(0x4AA)));


extern volatile __bit WPU4 __attribute__((address(0x4AC)));


extern volatile __bit WPU5 __attribute__((address(0x4AD)));


extern volatile __bit WPUA0 __attribute__((address(0x4A8)));


extern volatile __bit WPUA1 __attribute__((address(0x4A9)));


extern volatile __bit WPUA2 __attribute__((address(0x4AA)));


extern volatile __bit WPUA4 __attribute__((address(0x4AC)));


extern volatile __bit WPUA5 __attribute__((address(0x4AD)));


extern volatile __bit ZERO __attribute__((address(0x1A)));


extern volatile __bit nBOD __attribute__((address(0x470)));


extern volatile __bit nBOR __attribute__((address(0x470)));


extern volatile __bit nGPPU __attribute__((address(0x40F)));


extern volatile __bit nPD __attribute__((address(0x1B)));


extern volatile __bit nPOR __attribute__((address(0x471)));


extern volatile __bit nT1SYNC __attribute__((address(0x82)));


extern volatile __bit nTO __attribute__((address(0x1C)));
# 3 "main.c" 2
# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/xc.h" 1 3
# 18 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/xc.h" 3
extern const char __xc8_OPTIM_SPEED;

extern double __fpnormalize(double);


# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/xc8debug.h" 1 3



# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdlib.h" 1 3
# 10 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdlib.h" 3
# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/features.h" 1 3
# 11 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdlib.h" 2 3
# 21 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdlib.h" 3
# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/alltypes.h" 1 3
# 24 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/alltypes.h" 3
typedef long int wchar_t;
# 128 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/bits/alltypes.h" 3
typedef unsigned size_t;
# 22 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdlib.h" 2 3

int atoi (const char *);
long atol (const char *);



double atof (const char *);


float strtof (const char *restrict, char **restrict);
double strtod (const char *restrict, char **restrict);
long double strtold (const char *restrict, char **restrict);



long strtol (const char *restrict, char **restrict, int);
unsigned long strtoul (const char *restrict, char **restrict, int);





unsigned long __strtoxl(const char * s, char ** endptr, int base, char is_signed);
# 55 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/stdlib.h" 3
int rand (void);
void srand (unsigned);

void *malloc (size_t);
void *calloc (size_t, size_t);
void *realloc (void *, size_t);
void free (void *);

          void abort (void);
int atexit (void (*) (void));
          void exit (int);
          void _Exit (int);

void *bsearch (const void *, const void *, size_t, size_t, int (*)(const void *, const void *));







__attribute__((nonreentrant)) void qsort (void *, size_t, size_t, int (*)(const void *, const void *));

int abs (int);
long labs (long);




typedef struct { int quot, rem; } div_t;
typedef struct { long quot, rem; } ldiv_t;




div_t div (int, int);
ldiv_t ldiv (long, long);




typedef struct { unsigned int quot, rem; } udiv_t;
typedef struct { unsigned long quot, rem; } uldiv_t;
udiv_t udiv (unsigned int, unsigned int);
uldiv_t uldiv (unsigned long, unsigned long);
# 5 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include\\c99/xc8debug.h" 2 3







#pragma intrinsic(__builtin_software_breakpoint)
extern void __builtin_software_breakpoint(void);
# 24 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/xc.h" 2 3
# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/builtins.h" 1 3






#pragma intrinsic(__nop)
extern void __nop(void);
# 19 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/builtins.h" 3
#pragma intrinsic(_delay)
extern __attribute__((nonreentrant)) void _delay(uint32_t);
#pragma intrinsic(_delaywdt)
extern __attribute__((nonreentrant)) void _delaywdt(uint32_t);
# 25 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/xc.h" 2 3



# 1 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include/pic.h" 1 3




# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/htc.h" 1 3






# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/xc.h" 1 3
# 8 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/htc.h" 2 3
# 6 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include/pic.h" 2 3







# 1 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include/pic_chip_select.h" 1 3
# 14 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include/pic.h" 2 3
# 76 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include/pic.h" 3
__attribute__((__unsupported__("The " "FLASH_READ" " macro function is no longer supported. Please use the MPLAB X MCC."))) unsigned char __flash_read(unsigned short addr);

__attribute__((__unsupported__("The " "FLASH_WRITE" " macro function is no longer supported. Please use the MPLAB X MCC."))) void __flash_write(unsigned short addr, unsigned short data);

__attribute__((__unsupported__("The " "FLASH_ERASE" " macro function is no longer supported. Please use the MPLAB X MCC."))) void __flash_erase(unsigned short addr);


# 1 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/eeprom_routines.h" 1 3
# 84 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include/pic.h" 2 3
# 118 "C:/Program Files/Microchip/MPLABX/v6.25/packs/Microchip/PIC10-12Fxxx_DFP/1.7.178/xc8\\pic\\include/pic.h" 3
extern __bank0 unsigned char __resetbits;
extern __bank0 __bit __powerdown;
extern __bank0 __bit __timeout;
# 29 "C:\\Program Files\\Microchip\\xc8\\v3.00\\pic\\include/xc.h" 2 3
# 4 "main.c" 2

#pragma config FOSC = INTOSCIO
#pragma config WDTE = OFF
#pragma config PWRTE = OFF
#pragma config MCLRE = OFF
#pragma config CP = OFF

#pragma config BOREN = OFF


enum GpioBit {
    BMS_fault_o,
    BMS_gate_i,
    green_PIC_o,
    reserved,
    IMD_gate_i,
    red_PIC_o
};







uint8_t system_fault_state = 0;
uint8_t blink_counter = 0;

int main(void) {

    ANSEL = 0x00;
    CMCON0 = 0x07;


    TRISIO = (1 << BMS_gate_i) | (1 << IMD_gate_i) | (1 << 3);
    TRISIO &= ~((1 << BMS_fault_o) | (1 << green_PIC_o) | (1 << red_PIC_o));

    WPU = 0x00;
    OPTION_REG = 0x80;

    GPIO &= ~((1 << BMS_fault_o) | (1 << green_PIC_o) | (1 << red_PIC_o));


    IOC = 0;


    T1CON = 0x01;


    CMCON1 = 0x10;


    PIR1 &= ~(1 << TMR1IF);


    PIE1 &= ~(1 << TMR1IE);
    INTCON &= ~((1 << GIE) | (1 << PEIE));

    while (1) {

        uint8_t bms_gate_state = (GPIO >> BMS_gate_i) & 1;
        uint8_t imd_gate_state = (GPIO >> IMD_gate_i) & 1;

        uint8_t current_fault = (bms_gate_state == 1) || (imd_gate_state == 0);


        if (current_fault) {
            GPIO &= ~(1 << BMS_fault_o);
        } else {
            GPIO |= (1 << BMS_fault_o);
        }


        if (PIR1bits.TMR1IF) {
            PIR1bits.TMR1IF = 0;

            blink_counter++;

            if (blink_counter >= 20) {
                blink_counter = 0;


                if (current_fault == 1) {
                    GPIO ^= (1 << red_PIC_o);
                    GPIO &= ~(1 << green_PIC_o);
                } else {
                    GPIO ^= (1 << green_PIC_o);
                    GPIO &= ~(1 << red_PIC_o);
                }
            }
        }

    }

    return 0;
}
