MEMORY

{

    rom (rx) : ORIGIN = 0x08000000, LENGTH = 32K

    ram (rwx) : ORIGIN = 0x20000000, LENGTH = 10K

}


EXTERN(vector_table);

ENTRY(reset_handler);


SECTIONS

{

    .text : {

        *(.vectors)

        *(.text*)

        . = ALIGN(4);

    } >rom

} 
