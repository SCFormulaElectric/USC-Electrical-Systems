COMPILER = sdcc
MCU = pic12f609
CFLAGS = -mpic14 -p$(MCU) --use-non-free
PROGRAMMER = ./pk2cmd
PROG_FLAGS = -M -P$(MCU)

SRC = main.c
HEX_FILE = main.hex
CLEAN_FILES = main.asm main.cod main.hex main.lst main.o

all: compile

compile: $(HEX_FILE)
	@echo "Compilation successful."

$(HEX_FILE): $(SRC)
	@echo "Compiling $(SRC) for $(MCU)..."
	$(COMPILER) $(CFLAGS) $(SRC)
	@echo "Generated $(HEX_FILE)"

flash: $(HEX_FILE)
	@echo "Flashing $(MCU) with $(HEX_FILE)..."
	sudo $(PROGRAMMER) $(PROG_FLAGS) -F$(HEX_FILE)
	@echo "Flashing complete."

clean:
	@echo "Cleaning up project files..."
	rm -f $(CLEAN_FILES)
	@echo "Cleanup complete."

.PHONY: all compile flash clean

