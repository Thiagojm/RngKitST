#!/bin/bash

# Linux setup for RngKit Python Streamlit App
# - Installs udev rules for BitBabbler and TrueRNG devices
# - Creates required groups (bit-babbler)
# - Installs Python dependencies
# - Reloads udev so devices are ready without reboot

set -e

echo "🐍 Setting up RngKit Python Streamlit App for Linux..."
echo ""

# Must be root for system-level setup
if [[ $EUID -ne 0 ]]; then
  echo "❌ This script must be run as root (sudo) for system setup"
  echo "   Run: sudo $0"
  exit 1
fi



########################################
# BitBabbler setup
########################################
echo ""
echo "📦 Ensuring 'bit-babbler' system group exists..."
if ! getent group bit-babbler > /dev/null 2>&1; then
  groupadd --system bit-babbler
  echo "✅ Created bit-babbler group"
else
  echo "ℹ️  bit-babbler group already exists"
fi

echo ""
echo "🔧 Installing BitBabbler udev rules..."
BB_UDEV_DST="/etc/udev/rules.d/60-bit-babbler.rules"

# Create BitBabbler udev rules if they don't exist
if [[ ! -f "$BB_UDEV_DST" ]]; then
    cat > "$BB_UDEV_DST" << 'EOF'
# BitBabbler USB device rules
# Allows access to BitBabbler devices for users in bit-babbler group

# FTDI FT232H (BitBabbler Black/White)
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6014", GROUP="bit-babbler", MODE="0664"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6015", GROUP="bit-babbler", MODE="0664"

# Alternative VID:PID combinations for BitBabbler
SUBSYSTEM=="usb", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="7840", GROUP="bit-babbler", MODE="0664"
EOF
    chmod 644 "$BB_UDEV_DST"
    echo "✅ Created BitBabbler udev rules at $BB_UDEV_DST"
else
    echo "ℹ️  BitBabbler udev rules already exist"
fi

########################################
# TrueRNG setup
########################################
echo ""
echo "🔧 Installing TrueRNG udev rules..."
TRNG_UDEV_DST="/etc/udev/rules.d/99-TrueRNG.rules"

# Create TrueRNG udev rules if they don't exist
if [[ ! -f "$TRNG_UDEV_DST" ]]; then
    cat > "$TRNG_UDEV_DST" << 'EOF'
# TrueRNG USB device rules
# Allows access to TrueRNG devices for all users

# TrueRNG3 (04D8:F5FE)
SUBSYSTEM=="usb", ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="f5fe", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="f5fe", MODE="0666"

# TrueRNGpro (16D0:0AA0)
SUBSYSTEM=="usb", ATTRS{idVendor}=="16d0", ATTRS{idProduct}=="0aa0", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="16d0", ATTRS{idProduct}=="0aa0", MODE="0666"

# TrueRNGproV2 (04D8:EBB5)
SUBSYSTEM=="usb", ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="ebb5", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="04d8", ATTRS{idProduct}=="ebb5", MODE="0666"
EOF
    chmod 644 "$TRNG_UDEV_DST"
    echo "✅ Created TrueRNG udev rules at $TRNG_UDEV_DST"
else
    echo "ℹ️  TrueRNG udev rules already exist"
fi

########################################
# Apply settings
########################################
echo ""
echo "🔄 Reloading udev rules & triggering..."
udevadm control --reload-rules
udevadm trigger
echo "✅ udev reloaded"

########################################
# Add invoking user to bit-babbler group
########################################
TARGET_USER="${SUDO_USER:-$USER}"
if [[ -n "$TARGET_USER" && "$TARGET_USER" != "root" ]]; then
  echo ""
  echo "👥 Ensuring user '$TARGET_USER' is in 'bit-babbler' group..."
  if id -nG "$TARGET_USER" | tr " " "\n" | grep -qx "bit-babbler"; then
    echo "ℹ️  $TARGET_USER already in bit-babbler group"
  else
    usermod -aG bit-babbler "$TARGET_USER"
    echo "✅ Added $TARGET_USER to bit-babbler group"
  fi
else
  echo ""
  echo "ℹ️  Skipping group membership update (no non-root invoking user detected)"
fi

########################################
# Optional driver checks
########################################
echo ""
echo "🔍 Checking for required drivers..."

# Check for libusb-1.0
if ldconfig -p | grep -q libusb-1.0; then
    echo "✅ libusb-1.0 found"
else
    echo "⚠️  libusb-1.0 not found"
    echo "   Install with: sudo apt-get install libusb-1.0-0-dev"
fi

# Check for FTDI driver conflict with BitBabbler
if lsmod | grep -q ftdi_sio; then
  echo "⚠️  FTDI serial driver is loaded - this may conflict with BitBabbler"
  echo "   BitBabbler requires direct USB access, not serial interface"
  echo "   Attempting to unload FTDI serial driver for BitBabbler compatibility..."
  if modprobe -r ftdi_sio; then
    echo "✅ FTDI serial driver unloaded successfully"
    echo "   BitBabbler should now work with direct USB access"
  else
    echo "❌ Failed to unload FTDI serial driver"
    echo "   You may need to manually run: sudo modprobe -r ftdi_sio"
    echo "   Or blacklist the driver: echo 'blacklist ftdi_sio' | sudo tee /etc/modprobe.d/blacklist-bitbabbler.conf"
  fi
else
  echo "✅ FTDI serial driver not loaded - BitBabbler can use direct USB access"
fi


########################################
# Final instructions
########################################
echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Log out/in (or run: exec su - $TARGET_USER) to refresh group membership"
echo "   2. Replug your devices or keep them plugged; udev rules have been triggered"
echo "   3. Run the app: cd $PROJECT_ROOT && streamlit run main_streamlit.py"
echo ""
echo "🔧 Troubleshooting:"
echo "   • If BitBabbler not detected: Check you're in bit-babbler group (groups)"
echo "   • If TrueRNG not detected: Check device permissions (ls -l /dev/ttyUSB*)"
echo "   • If Python errors: Check all dependencies installed (pip3 list)"
echo ""
echo "📖 For more help, see README.md"
