#!/usr/bin/env bash
# Convierte una Raspberry Pi en el reproductor de la segunda pantalla del stand.
# Al encender, abre sitio/stand/pantalla.html a pantalla completa en la pantalla HDMI, sin internet.
#
# Uso (en la Pi, con Raspberry Pi OS con escritorio):
#   git clone https://github.com/davixcky/medidor-energia-esp32.git
#   cd medidor-energia-esp32 && bash sitio/stand/pi/instalar.sh            # sin giro
#   GIRAR=90 bash sitio/stand/pi/instalar.sh                                # si la imagen sale de lado
set -euo pipefail

ORIGEN="$(cd "$(dirname "$0")/.." && pwd)"
DESTINO="$HOME/stand-medidor"
GIRAR="${GIRAR:-0}"
SEG="${SEG:-12}"

echo "→ Copiando la página a $DESTINO"
mkdir -p "$DESTINO/img"
cp "$ORIGEN/pantalla.html" "$DESTINO/"
cp "$ORIGEN/img/qr.svg" "$DESTINO/img/"

NAV="$(command -v chromium || command -v chromium-browser || true)"
if [ -z "$NAV" ]; then
  echo "→ Instalando Chromium"
  sudo apt-get update && sudo apt-get install -y chromium || sudo apt-get install -y chromium-browser
  NAV="$(command -v chromium || command -v chromium-browser)"
fi

URL="file://$DESTINO/pantalla.html?girar=$GIRAR&seg=$SEG"
ARGS="--kiosk --noerrdialogs --disable-infobars --no-first-run --disable-session-crashed-bubble --disable-features=Translate --check-for-update-interval=31536000 --password-store=basic --incognito"

# Lanzador que reinicia Chromium si se cierra
cat > "$DESTINO/iniciar.sh" <<LANZ
#!/usr/bin/env bash
# Solo una copia, aunque el escritorio lo lance por dos vías
exec 9>/tmp/stand-medidor.lock
flock -n 9 || exit 0
sleep 3
while true; do
  "$NAV" $ARGS "$URL"
  sleep 2
done
LANZ
chmod +x "$DESTINO/iniciar.sh"

echo "→ Arranque automático"
# Escritorio Wayland (labwc, Raspberry Pi OS Bookworm o posterior)
mkdir -p "$HOME/.config/labwc"
grep -qs "stand-medidor/iniciar.sh" "$HOME/.config/labwc/autostart" || echo "$DESTINO/iniciar.sh &" >> "$HOME/.config/labwc/autostart"
# Escritorio X11 / LXDE (versiones anteriores)
mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.config/autostart/stand-medidor.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Stand medidor
Exec=$DESTINO/iniciar.sh
X-GNOME-Autostart-enabled=true
DESK
if command -v raspi-config >/dev/null; then
  echo "→ Inicio de sesión automático en el escritorio y pantalla siempre encendida"
  sudo raspi-config nonint do_boot_behaviour B4 || true
  sudo raspi-config nonint do_blanking 1 || true
fi

echo
echo "Listo. Reinicia con: sudo reboot"
echo "La página es: $URL"
echo "Para cambiar el giro: GIRAR=90 bash sitio/stand/pi/instalar.sh (0, 90, 180 o 270)"
