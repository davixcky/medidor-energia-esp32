prueba: prueba_medicion.cpp ../lib/medicion/medicion.cpp ../lib/medicion/medicion.h ../lib/adr001/adr001.h
	g++ -std=c++17 -O2 -Wall -o prueba prueba_medicion.cpp ../lib/medicion/medicion.cpp
	./prueba

trama: trama_prueba.cpp ../lib/adr001/adr001.h
	g++ -std=c++17 -O2 -Wall -o trama trama_prueba.cpp

# Pantallas de la LCD dibujadas en el PC. Requiere las bibliotecas de PlatformIO (pio pkg install).
GFX ?= ../.pio/libdeps/esp32dev/Adafruit GFX Library
pantallas: pantallas.cpp ../lib/interfaz/interfaz.cpp ../lib/interfaz/interfaz.h
	g++ -std=c++17 -O2 -Wall -DARDUINO=100 -Iarduino -I"$(GFX)" -I../lib/interfaz -I../lib/medicion \
	    -o pantallas pantallas.cpp ../lib/interfaz/interfaz.cpp "$(GFX)/Adafruit_GFX.cpp"
	mkdir -p salida
	./pantallas salida
	python3 componer_pantallas.py salida ../../img
