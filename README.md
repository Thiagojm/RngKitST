# 🎲 RngKit 1.0 - Streamlit Version

**A powerful tool for True Random Number Generator data collection and statistical analysis**

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*by [Thiago Jung](https://github.com/Thiagojm) • [thiagojm1984@hotmail.com](mailto:thiagojm1984@hotmail.com)*

[GitHub Repository](https://github.com/Thiagojm/RngKitST) • [Original RngKitPSG](https://github.com/Thiagojm/RngKitPSG)

---

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [🔧 Supported Hardware](#-supported-hardware)
- [⚡ Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [🚀 Usage Guide](#-usage-guide)
- [📁 File Naming Convention](#-file-naming-convention)
- [⚠️ Known Issues](#️-known-issues)
- [📄 License](#-license)

---

## 🎯 Overview

**RngKit 1.0** is a modernized version of the original RngKitPSG 3.0, rebuilt with **Streamlit** for better cross-platform compatibility and user experience. This application provides comprehensive tools for collecting and analyzing data from True Random Number Generators (TRNGs) and Pseudo Random Number Generators (PRNGs).

### ✨ Key Features

- 🔌 **Multi-Device Support**: TrueRNG, BitBabbler, and Pseudo RNG
- 📊 **Real-time Analysis**: Live plotting with Z-score visualization
- 📈 **Statistical Analysis**: Automated Excel report generation with charts
- 🔄 **Data Concatenation**: Combine multiple CSV files for extended analysis
- 🖥️ **Cross-Platform**: Windows, Linux, and macOS support
- 🎨 **Modern UI**: Clean, intuitive Streamlit interface

### 🔄 What's New in 1.x

- ✅ **Direct BitBabbler Support**: No more `seedd.exe` daemon required
- ✅ **Auto-Detection**: Sample size and interval detection from filenames
- ✅ **Enhanced Error Handling**: User-friendly device disconnection alerts
- ✅ **Performance Optimizations**: Cached operations for better responsiveness

---

## 🔧 Supported Hardware

| Device | Model | Status | Notes |
|--------|-------|--------|-------|
| **TrueRNG** | TrueRNG3, TrueRNGPro | ✅ Supported | [ubld.it](https://ubld.it/) |
| **BitBabbler** | Black, White | ✅ Supported | [bitbabbler.org](http://www.bitbabbler.org/what.html) |
| **Pseudo RNG** | Python `secrets` | ✅ Supported | Not truly random, for testing only |

---

## ⚡ Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements_streamlit.txt
   ```

2. **Run the application**:
   ```bash
   streamlit run main_streamlit.py
   ```

3. **Open your browser** to `http://localhost:8501`

4. **Start collecting data** with your preferred RNG device!

---

## 📦 Installation

### 🪟 Windows Installation

#### Hardware Setup

1. **TrueRNG/TrueRNGPro**:
   - Navigate to `tools/installers/TrueRng/` folder
   - Right-click `TrueRNG.inf` or `TrueRNGpro.inf`
   - Select "Install" and follow the prompts

2. **BitBabbler**:
   - Run `vcredist_x64.exe` from `tools/installers/BitBabbler/`
   - Insert BitBabbler device into USB port
   - Run `zadig-2.8.exe` and install driver for your device

### 🐧 Linux Installation

#### Automated Setup (Recommended)
```bash
sudo ./tools/installers/setup_rng_devices_linux_python.sh
```

This script will:
- ✅ Set up udev rules for device access
- ✅ Create required user groups
- ✅ Configure device permissions

#### Manual Setup
```bash
# Install Python dependencies
pip3 install -r requirements_streamlit.txt

# Install system dependencies
sudo apt-get install libusb-1.0-0-dev

# Add user to bit-babbler group
sudo usermod -aG bit-babbler $USER

# Log out and back in for group changes to take effect
```

### 🍎 macOS Installation

```bash
# Install Python dependencies
pip install -r requirements_streamlit.txt

# Install system dependencies
brew install libusb
```

---

## 🚀 Usage Guide

### 📊 Tab 1: Data Collection & Analysis

#### 🔄 Collecting Data

1. **Select your device**:
   - **BitBabbler**: Choose fold level (0-4)
     - `0` = RAW mode
     - `1-4` = XOR folding levels
   - **TrueRNG**: No fold options
   - **Pseudo RNG**: Uses Python `secrets` module

2. **Configure parameters**:
   - **Sample Size**: Number of bits per sample (must be divisible by 8)
   - **Sample Interval**: Time between samples in seconds

3. **Start/Stop collection**:
   - Click **"▶️ Start Collection"** to begin
   - Click **"⏹️ Stop Collection"** to end
   - Files are automatically saved to `data/raw/`

#### 📈 Analyzing Data

1. **Upload a file**:
   - Select a previously generated `.bin` or `.csv` file
   - Sample size and interval are auto-detected from filename

2. **Generate analysis**:
   - Click **"📊 Generate Analysis"**
   - Excel file with Z-score chart is created
   - Use **"📁 Open Output Folder"** to access results

#### 🔗 Concatenating Files

1. **Select multiple CSV files** with the same parameters
2. **Set correct sample size and interval**
3. **Click "🔗 Concatenate Files"** to merge data

### 📈 Tab 2: Live Plot

1. **Configure device and parameters** (same as data collection)
2. **Click "▶️ Start Live Plot"** to begin real-time visualization
3. **Monitor Z-score chart** updating in real-time
4. **Click "⏹️ Stop Live Plot"** when finished

### 📖 Tab 3: Instructions

View this README content directly in the application.

---

## 📁 File Naming Convention

Files follow a structured naming pattern that encodes important metadata:

```
YYYYMMDDTHHMMSS_{device}_s{bits}_i{interval}[_f{folds}]
```

### 📝 Format Breakdown

| Component | Description | Example |
|-----------|-------------|---------|
| `YYYYMMDDTHHMMSS` | Timestamp | `20201011T142208` |
| `{device}` | Device type | `trng`, `bitb`, `pseudo` |
| `s{bits}` | Sample size in bits | `s2048` |
| `i{interval}` | Interval in seconds | `i1` |
| `_f{folds}` | BitBabbler fold level | `f0` (RAW), `f1-f4` (XOR) |

### 💡 Example

```
20201011T142208_bitb_s2048_i1_f0
```

- **Date**: October 11, 2020
- **Time**: 14:22:08
- **Device**: BitBabbler
- **Sample Size**: 2048 bits
- **Interval**: 1 second
- **Mode**: RAW (f0)

---

## ⚠️ Known Issues

### 🐧 Linux Compatibility

| Issue | Status | Workaround |
|-------|--------|------------|
| **TrueRNG + BitBabbler combination** | ❌ Not supported | Use individual devices instead |

### 🔧 Troubleshooting

#### BitBabbler Issues
- **Device not detected**: Ensure proper USB connection and driver installation
- **Permission denied**: Add user to `bit-babbler` group and restart session
- **Driver issues**: Reinstall using Zadig (Windows) or udev rules (Linux)

#### TrueRNG Issues
- **Port not found**: Check USB connection and driver installation
- **Permission denied**: Ensure user has access to serial ports

---

## 📄 License

**MIT License**

Copyright (c) 2025 Thiago Jung Mendaçolli

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

**Made with ❤️ by [Thiago Jung](https://github.com/Thiagojm)**

[⭐ Star this repo](https://github.com/Thiagojm/RngKitST) • [🐛 Report Issues](https://github.com/Thiagojm/RngKitST/issues) • [💬 Discussions](https://github.com/Thiagojm/RngKitST/discussions)