compile: main.hex
	sdcc -mpic14 -p12f609 main.c --use-non-free

flash: main.hex
	sudo ./pk2cmd -M -PPIC12F609 -Fmain.hex

main.hex: main.c
	sdcc -mpic14 -p12f609 main.c --use-non-free

.PHONY: compile flash
