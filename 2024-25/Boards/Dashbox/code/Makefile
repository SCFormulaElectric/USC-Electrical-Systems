PROJECT_NAME = dash
LD_FILE = bluepill.ld

CROSS_COMPILE = arm-none-eabi-
CC = $(CROSS_COMPILE)gcc
OBJCOPY = $(CROSS_COMPILE)objcopy
CPUFLAGS = -mcpu=cortex-m3 -mthumb
CFLAGS = -Wall -Wextra -g3 -O0 -MD $(CPUFLAGS)
LDFLAGS = $(CPUFLAGS) -nostartfiles -Wl,-T,$(LD_FILE)
LDLIBS = -lc -lnosys
FLASH_TOOL = st-flash

CSRC = $(PROJECT_NAME).c
OBJ = $(CSRC:.c=.o)
BIN = $(PROJECT_NAME).bin
ELF = $(PROJECT_NAME).elf

$(ELF): $(OBJ)
	$(CC) $(LDFLAGS) -o $@ $(OBJ) $(LDLIBS)

$(BIN): $(ELF)
	$(OBJCOPY) -O binary $< $@

all: $(BIN)

flash: $(BIN)
	$(FLASH_TOOL) write $(BIN) 0x08000000

.PHONY: clean flash all
clean:
	-rm -rf *.o *.bin *.elf *.map *.d
