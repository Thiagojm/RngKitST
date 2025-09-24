# Standard library imports
import os
import platform
import secrets
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# External imports
import streamlit as st
import plotly.graph_objects as go
import serial
from serial.tools import list_ports

# Internal imports

# Make 'src' importable for the service layer
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from rngkit.services import filenames as fn_service  # type: ignore
from rngkit.services import storage as storage_service  # type: ignore
from rngkit.services import utils as svc_utils  # type: ignore
from rngkit.devices import bitbabbler as dev_bitb  # type: ignore
from rngkit.devices import truerng as dev_trng  # type: ignore
from rngkit.devices import pseudo as dev_pseudo  # type: ignore

# Page configuration
st.set_page_config(
    page_title="RngKit 1.0 - Streamlit Version",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state with defaults
def init_session_state():
    """Initialize all session state variables with default values"""
    defaults = {
        'collecting': False,
        'live_plotting': False,
        'zscore_data': [],
        'index_data': [],
        'current_values': {},
        'collected_data': [],
        'file_name': "",
        'last_update_time': datetime.now(),
        'sample_size': 2048,
        'sample_interval': 1.0,
        'csv_ones': [],
        'csv_sum': 0,
        'csv_count': 0,
        # Cached device detection invalidation counter
        'device_refresh_counter': 0,
        # Performance profiling
        'perf_enabled': True,
        'perf_samples': {},
        # Scheduled sampling times
        'next_sample_time': None,
        'next_live_sample_time': None,
        # Device detection snapshot
        'bb_detected': None,
        'bb_error': "",
        'trng_detected': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize session state
init_session_state()

# No seedd process management needed with bbpy

# Ensure data directory exists
DATA_DIR = svc_utils.ensure_data_dir()

# Helper functions
LIVE_MAX_POINTS = 200  # cap points rendered on live chart
COLLECT_MAX_HISTORY = 200  # cap collection status history kept in memory
PERF_MAX_SAMPLES = 200  # cap stored perf samples per span
JITTER_TOLERANCE_SEC = 0.25  # scheduling tolerance to avoid missed samples

def record_perf_sample(span_name: str, duration_seconds: float) -> None:
    """Record a performance sample for a named span.

    Parameters
    ----------
    span_name: str
        Logical name of the measured span.
    duration_seconds: float
        Elapsed time in seconds.
    """
    if not st.session_state.get('perf_enabled', True):
        return
    samples: Dict[str, List[float]] = st.session_state.get('perf_samples', {})
    arr = samples.get(span_name, [])
    arr.append(duration_seconds)
    if len(arr) > PERF_MAX_SAMPLES:
        arr = arr[-PERF_MAX_SAMPLES:]
    samples[span_name] = arr
    st.session_state['perf_samples'] = samples


@contextmanager
def perf_timer(span_name: str):
    """Context manager to measure and record wall time for a code block.

    Parameters
    ----------
    span_name: str
        Logical name of the measured span.
    """
    if not st.session_state.get('perf_enabled', True):
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        record_perf_sample(span_name, end - start)


def render_perf_panel(max_rows: int = 6) -> None:
    """Render a small performance panel in the sidebar with recent timings.

    Parameters
    ----------
    max_rows: int
        Maximum number of spans to show, sorted by worst-case time.
    """
    samples: Dict[str, List[float]] = st.session_state.get('perf_samples', {})
    if not samples:
        return
    with st.sidebar.expander("🕒 Performance (recent)", expanded=False):
        # Build simple rows sorted by max duration desc
        rows = []
        for name, arr in samples.items():
            if not arr:
                continue
            count = len(arr)
            total = sum(arr)
            avg = total / count
            worst = max(arr)
            arr_sorted = sorted(arr)
            p95 = arr_sorted[int(0.95 * (count - 1))] if count > 1 else worst
            rows.append((name, avg, p95, worst, count))
        rows.sort(key=lambda r: r[3], reverse=True)
        if not rows:
            st.write("No perf samples yet.")
            return
        rows = rows[:max_rows]
        for name, avg, p95, worst, count in rows:
            st.write(f"{name}: avg {avg*1000:.1f} ms | p95 {p95*1000:.1f} ms | max {worst*1000:.1f} ms (n={count})")


def count_ones_in_bytes(data: bytes) -> int:
    """Count the number of 1-bits in a bytes object efficiently.

    Parameters
    ----------
    data: bytes
        Bytes buffer whose bits will be counted.

    Returns
    -------
    int
        Number of 1-bits across all bytes.
    """
    return sum(b.bit_count() for b in data)

@st.cache_data
def detect_bitbabbler_cached(refresh_counter: int) -> Tuple[bool, str]:
    """Return BitBabbler detection status using cache.

    Parameters
    ----------
    refresh_counter: int
        Counter value used to invalidate the cache when changed.

    Returns
    -------
    Tuple[bool, str]
        A tuple with (detected, error_message).
    """
    try:
        # Try a few times to allow USB stack to settle after plug/unplug
        attempts = 3
        last_error = ""
        for i in range(attempts):
            detected = dev_bitb.probe()
            if detected:
                return True, ""
            # reset and retry after short wait
            try:
                dev_bitb.reset()
            except Exception:
                pass
            last_error = dev_bitb.get_detection_error()
            time.sleep(0.2)
        return False, last_error
    except Exception as exc:  # pragma: no cover - defensive
        return False, str(exc)


@st.cache_data
def detect_trng_cached(refresh_counter: int) -> bool:
    """Return TrueRNG/TrueRNG3 detection status using cache.

    Parameters
    ----------
    refresh_counter: int
        Counter value used to invalidate the cache when changed.

    Returns
    -------
    bool
        True if the device is detected, False otherwise.
    """
    try:
        # Try a few times to allow USB/serial enumeration to settle
        for _ in range(3):
            if dev_trng.detect():
                return True
            time.sleep(0.2)
        return False
    except Exception:  # pragma: no cover - defensive
        return False


def refresh_device_status() -> None:
    """Increment refresh counter to invalidate cached device detection."""
    # Also reset device-level cache so unplug/plug is seen immediately
    try:
        dev_bitb.reset()
    except Exception:
        pass
    st.session_state['device_refresh_counter'] = (
        st.session_state.get('device_refresh_counter', 0) + 1
    )
    # Perform one-time detection and store snapshot results
    try:
        bb_ok, bb_err = detect_bitbabbler_cached(st.session_state['device_refresh_counter'])
    except Exception as _:
        bb_ok, bb_err = False, "Unexpected detection error"
    try:
        trng_ok = detect_trng_cached(st.session_state['device_refresh_counter'])
    except Exception:
        trng_ok = False
    st.session_state['bb_detected'] = bb_ok
    st.session_state['bb_error'] = bb_err
    st.session_state['trng_detected'] = trng_ok
def create_values_dict(rng_type: str, xor_mode: int, sample_size: int, sample_interval: float, prefix: str = "") -> dict:
    """Create a values dictionary for device operations"""
    return {
        f"{prefix}bit_ac": rng_type == "BitBabbler",
        f"{prefix}true3_ac": rng_type in ["TrueRNG", "TrueRNG3"],
        f"{prefix}pseudo_rng_ac": rng_type == "PseudoRNG",
        f"{prefix}combo": xor_mode,
        f"{prefix}bit_count": sample_size,
        f"{prefix}time_count": sample_interval,
        # Also include the original keys for backward compatibility
        "bit_ac": rng_type == "BitBabbler",
        "true3_ac": rng_type in ["TrueRNG", "TrueRNG3"],
        "pseudo_rng_ac": rng_type == "PseudoRNG"
    }

def is_device_not_found_error(error: Exception) -> bool:
    """Check if an error indicates device not found, cross-platform"""
    if isinstance(error, OSError):
        # Linux/Unix: errno 19 = ENODEV (No such device)
        # Windows: errno 2 = ENOENT (No such file or directory)
        # Windows: errno 3 = ESRCH (No such process)
        if hasattr(error, 'errno'):
            if platform.system().lower() == "windows":
                return error.errno in [2, 3]  # ENOENT, ESRCH on Windows
            else:
                return error.errno == 19  # ENODEV on Linux/Unix
    
    # Check error message content for common device not found patterns
    error_msg = str(error).lower()
    device_not_found_patterns = [
        "no such device",
        "device not found",
        "no such file or directory",
        "permission denied",
        "access denied",
        "device or resource busy"
    ]
    return any(pattern in error_msg for pattern in device_not_found_patterns)


def get_platform_specific_troubleshooting(device_type: str) -> list:
    """Get platform-specific troubleshooting steps for device errors"""
    system = platform.system().lower()
    
    if device_type == "BitBabbler":
        if system == "windows":
            return [
                "1. Ensure BitBabbler is connected to USB",
                "2. Install Visual C++ Redistributable (vcredist_x64.exe)",
                "3. Install BitBabbler driver using Zadig (zadig-2.8.exe)",
                "4. Try running `python test_bitbabbler.py` to diagnose"
            ]
        elif system == "linux":
            return [
                "1. Ensure BitBabbler is connected to USB",
                "2. Install libusb-1.0 development package: `sudo apt-get install libusb-1.0-0-dev`",
                "3. Add user to bit-babbler group: `sudo usermod -aG bit-babbler $USER`",
                "4. Run setup script: `sudo ./tools/installers/setup_rng_devices_linux_python.sh`",
                "5. Log out and back in for group changes to take effect"
            ]
        else:  # macOS or other
            return [
                "1. Ensure BitBabbler is connected to USB",
                "2. Install libusb-1.0: `brew install libusb`",
                "3. Check device permissions and USB access"
            ]
    elif device_type == "TrueRNG":
        if system == "windows":
            return [
                "1. Ensure TrueRNG is connected to USB",
                "2. Install TrueRNG driver from tools/installers/TrueRng/",
                "3. Check Windows Device Manager for the device"
            ]
        elif system == "linux":
            return [
                "1. Ensure TrueRNG is connected to USB",
                "2. Add user to dialout group: `sudo usermod -aG dialout $USER`",
                "3. Check device permissions: `ls -l /dev/ttyUSB*` or `/dev/ttyACM*`",
                "4. Run setup script: `sudo ./tools/installers/setup_rng_devices_linux_python.sh`"
            ]
        else:  # macOS or other
            return [
                "1. Ensure TrueRNG is connected to USB",
                "2. Check device permissions and serial port access"
            ]
    
    return ["1. Ensure device is properly connected to USB"]


def validate_device_detection(values: dict, rng_type: str, force_refresh: bool = False) -> bool:
    """Validate device detection and show appropriate error messages.

    Parameters
    ----------
    values: dict
        Current selection flags for devices.
    rng_type: str
        Selected RNG type friendly name.
    force_refresh: bool
        When True, bypass cache and perform a fresh device detection.

    Returns
    -------
    bool
        True when the required device is detected, False otherwise.
    """
    refresh_counter = st.session_state.get('device_refresh_counter', 0)

    if values.get("bit_ac", False):
        if force_refresh:
            # bypass cache at both app and device layer
            try:
                dev_bitb.reset()
            except Exception:
                pass
            detected = dev_bitb.detect()
            error_msg = "" if detected else dev_bitb.get_detection_error()
        else:
            detected, error_msg = detect_bitbabbler_cached(refresh_counter)

        if not detected:
            st.error(f"❌ **BitBabbler Device Error:** {error_msg}")
            st.error("**Troubleshooting steps:**")
            for step in get_platform_specific_troubleshooting("BitBabbler"):
                st.error(step)
            return False

    elif values.get("true3_ac", False):
        if force_refresh:
            detected = dev_trng.detect()
        else:
            detected = detect_trng_cached(refresh_counter)

        if not detected:
            st.error("❌ **TrueRNG3 Device Error:** Device not detected")
            st.error("**Troubleshooting steps:**")
            for step in get_platform_specific_troubleshooting("TrueRNG"):
                st.error(step)
            return False
    # Removed true3_bit_ac logic as combined option is no longer supported
    return True

def show_device_error(rng_type: str):
    """Show device-specific error messages"""
    if rng_type == "BitBabbler":
        st.error("❌ BitBabbler device check failed!")
        st.error("**Troubleshooting steps:**")
        st.error("1. Ensure BitBabbler is connected to USB")
        st.error("2. Install Visual C++ Redistributable (vcredist_x64.exe)")
        st.error("3. Install BitBabbler driver using Zadig (zadig-2.8.exe)")
        st.error("4. Try running `python test_bitbabbler.py` to diagnose")
    else:
        st.error("❌ Device check failed. Please ensure your device is connected.")

@st.cache_data
def calculate_zscore(ones_list: list, sample_size: int) -> float:
    """Calculate Z-score from ones count list"""
    if not ones_list:
        return 0.0
    index_number = len(ones_list)
    sums_csv = sum(ones_list)
    avrg_csv = sums_csv / index_number
    return (avrg_csv - (sample_size / 2)) / (((sample_size / 4) ** 0.5) / (index_number ** 0.5))


def calculate_zscore_streaming(total_ones: int, num_samples: int, sample_size: int) -> float:
    """Calculate Z-score using streaming totals.

    Parameters
    ----------
    total_ones: int
        Sum of ones across all samples.
    num_samples: int
        Number of samples accumulated.
    sample_size: int
        Number of bits per sample.

    Returns
    -------
    float
        Z-score computed from streaming aggregates.
    """
    if num_samples <= 0:
        return 0.0
    avrg_csv = total_ones / num_samples
    return (avrg_csv - (sample_size / 2)) / (((sample_size / 4) ** 0.5) / (num_samples ** 0.5))

@st.cache_data
def read_file_content(file_path: str) -> str:
    """Cache file reading for better performance"""
    try:
        with open(file_path, "r", encoding="utf8") as f:
            return f.read()
    except FileNotFoundError:
        return "File not found."

@st.cache_data
def process_uploaded_file(uploaded_file, data_dir: str) -> str:
    """Cache uploaded file processing"""
    file_path = os.path.join(data_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def main():
    # Header
    st.title("🎲 RngKit 1.0 - Streamlit Version")
    st.markdown("**by Thiago Jung** - thiagojm1984@hotmail.com")
    st.markdown("---")
    # Perf panel
    render_perf_panel()
    # On first load, take a detection snapshot (only once per session)
    if st.session_state.get('bb_detected') is None or st.session_state.get('trng_detected') is None:
        refresh_device_status()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Data Collection & Analysis", "📈 Live Plot", "📖 Instructions"])
    
    with tab1:
        render_data_collection_tab()
    
    with tab2:
        render_live_plot_tab()
    
    with tab3:
        render_instructions_tab()

def render_data_collection_tab():
    st.header("📊 Data Collection & Analysis")
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🔧 Acquiring Data")
        
        # RNG Device Selection
        rng_type = st.radio(
            "Choose RNG Device:",
            ["BitBabbler", "TrueRNG", "PseudoRNG"],
            index=0
        )
        
        # Device Status Indicator (cached) and manual refresh
        cols_status = st.columns([3, 1])
        with cols_status[0]:
            if rng_type == "BitBabbler":
                if st.session_state.get('bb_detected'):
                    st.success("✅ BitBabbler device detected and ready")
                else:
                    st.error(f"❌ BitBabbler device not available: {st.session_state.get('bb_error','')}" )
            elif rng_type in ["TrueRNG", "TrueRNG3"]:
                if st.session_state.get('trng_detected'):
                    st.success("✅ TrueRNG3 device detected and ready")
                else:
                    st.error("❌ TrueRNG3 device not detected")
            elif rng_type == "PseudoRNG":
                st.info("ℹ️ PseudoRNG (software-based) - always available")
        with cols_status[1]:
            if st.button("🔄 Refresh", use_container_width=True):
                refresh_device_status()
                st.rerun()
        
        # Device-specific options
        if rng_type == "BitBabbler":
            xor_mode = st.selectbox(
                "RAW(0)/XOR (1,2,3,4):",
                options=[0, 1, 2, 3, 4],
                index=0,
                help="0 = RAW mode, 1-4 = XOR with different fold counts"
            )
        else:
            xor_mode = 0
        
        # Sample parameters
        sample_size = st.number_input(
            "Sample Size (bits):",
            min_value=8,
            value=2048,
            step=8,
            help="Must be divisible by 8"
        )
        
        sample_interval = st.number_input(
            "Sample Interval (seconds):",
            min_value=1,
            value=1,
            step=1
        )
        
        # Collection controls
        col_start, col_status = st.columns([1, 1])
        
        with col_start:
            if not st.session_state.collecting:
                if st.button("▶️ Start Collection", type="primary", use_container_width=True):
                    start_data_collection(rng_type, xor_mode, sample_size, sample_interval)
            else:
                if st.button("⏹️ Stop Collection", type="secondary", use_container_width=True):
                    stop_data_collection()
        
        with col_status:
            # Auto-updating collection status
            # Only run fragment when collecting
            run_every = 1 if st.session_state.collecting else None
            
            @st.fragment(run_every=run_every)
            def update_collection_status():
                if st.session_state.collecting:
                    # Generate new data
                    with perf_timer("collect_data_sample"):
                        collect_data_sample()
                    
                    st.success("🟢 Collecting")
                    # Show collection statistics
                    if st.session_state.collected_data:
                        data_count = len(st.session_state.collected_data)
                        latest_data = st.session_state.collected_data[-1]
                        st.metric("Samples", data_count)
                        st.metric("Latest Ones", latest_data['ones'])
                else:
                    st.info("🟡 Idle")
            
            update_collection_status()
    with col2:
        st.subheader("📈 Data Analysis")
        
        # File selection for analysis
        st.info("💡 **Tip**: Navigate to the data folder to find your generated files")
        uploaded_file = st.file_uploader(
            "Select file for analysis:",
            type=['csv', 'bin'],
            help="Select a previously generated .csv or .bin file from the data folder"
        )
        
        if uploaded_file:
            st.info(f"Selected: {uploaded_file.name}")
            
            # Analysis parameters (auto-detected from filename)
            analysis_col1, analysis_col2 = st.columns(2)
            
            # Try to detect defaults from filename convention
            detected_sample = 2048
            detected_interval = 1
            try:
                detected_sample = fn_service.parse_bits(uploaded_file.name)
                detected_interval = fn_service.parse_interval(uploaded_file.name)
            except Exception:
                pass

            # Update session defaults when file changes
            if st.session_state.get('_last_uploaded_for_analysis') != uploaded_file.name:
                st.session_state['an_sample_size'] = detected_sample
                st.session_state['an_sample_interval'] = detected_interval
                st.session_state['_last_uploaded_for_analysis'] = uploaded_file.name
            
            with analysis_col1:
                an_sample_size = st.number_input(
                    "Sample Size (bits):",
                    min_value=8,
                    step=8,
                    key="an_sample_size"
                )
            
            with analysis_col2:
                an_sample_interval = st.number_input(
                    "Sample Interval (seconds):",
                    min_value=1,
                    step=1,
                    key="an_sample_interval"
                )
            
            # Analysis buttons
            analysis_btn_col1, analysis_btn_col2 = st.columns(2)
            
            with analysis_btn_col1:
                if st.button("📊 Generate Analysis", use_container_width=True):
                    if svc_utils.is_valid_params(an_sample_size, an_sample_interval):
                        # Save uploaded file to data folder using cached function
                        file_path = process_uploaded_file(uploaded_file, DATA_DIR)
                        
                        try:
                            # Build dataframe depending on extension
                            if file_path.endswith('.bin'):
                                df = storage_service.read_bin_counts(file_path, an_sample_size)
                            else:
                                df = storage_service.read_csv_counts(file_path)
                            df = storage_service.add_zscore(df, an_sample_size)
                            storage_service.write_excel_with_chart(df, file_path, an_sample_size, an_sample_interval)
                            st.success("✅ Analysis completed! Check the output folder.")
                        except Exception as e:
                            st.error(f"❌ Analysis failed: {str(e)}")
                    else:
                        st.error("❌ Invalid parameters. Sample size must be divisible by 8.")
            
            with analysis_btn_col2:
                if st.button("📁 Open Output Folder", use_container_width=True):
                    if os.name == 'nt':  # Windows
                        os.startfile(DATA_DIR)
                    else:  # Linux/macOS
                        import subprocess
                        subprocess.run(['xdg-open', DATA_DIR])
        
        # File concatenation section
        st.subheader("🔗 Concatenate Multiple CSV Files")
        st.info("💡 **Tip**: Navigate to the data folder to find your CSV files")
        
        concat_files = st.file_uploader(
            "Select multiple CSV files to concatenate:",
            type=['csv'],
            accept_multiple_files=True,
            help="Select multiple CSV files with the same sample size and interval from the data folder"
        )
        
        if concat_files:
            concat_col1, concat_col2 = st.columns(2)
            
            with concat_col1:
                concat_sample_size = st.number_input(
                    "Sample Size (bits):",
                    min_value=8,
                    value=2048,
                    step=8,
                    key="concat_sample_size"
                )
            
            with concat_col2:
                concat_sample_interval = st.number_input(
                    "Sample Interval (seconds):",
                    min_value=1,
                    value=1,
                    step=1,
                    key="concat_sample_interval"
                )
            
            if st.button("🔗 Concatenate Files", use_container_width=True):
                if len(concat_files) > 1:
                    # Save uploaded files to data folder using cached function
                    file_paths = []
                    for file in concat_files:
                        file_path = process_uploaded_file(file, DATA_DIR)
                        file_paths.append(file_path)
                    
                    try:
                        # Create output stem with timestamp and parameters
                        out_stem = time.strftime(f"%Y%m%dT%H%M%S_concat_s{concat_sample_size}_i{concat_sample_interval}")
                        out_path = storage_service.concat_csv_files([*file_paths], out_stem)
                        st.success(f"✅ Files concatenated successfully! Saved: {out_path}")
                    except Exception as e:
                        st.error(f"❌ Concatenation failed: {str(e)}")
                else:
                    st.warning("⚠️ Please select at least 2 files to concatenate.")

def render_live_plot_tab():
    st.header("📈 Live Plot")
    
    # Create two columns
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ Options")
        
        # RNG Device Selection for live plot
        live_rng_type = st.radio(
            "Choose RNG Device:",
            ["BitBabbler", "TrueRNG3", "PseudoRNG"],
            index=0,
            key="live_rng"
        )
        
        # Device Status Indicator for Live Plot (cached) and manual refresh
        cols_status_live = st.columns([3, 1])
        with cols_status_live[0]:
            if live_rng_type == "BitBabbler":
                if st.session_state.get('bb_detected'):
                    st.success("✅ BitBabbler device detected and ready")
                else:
                    st.error(f"❌ BitBabbler device not available: {st.session_state.get('bb_error','')}")
            elif live_rng_type == "TrueRNG3":
                if st.session_state.get('trng_detected'):
                    st.success("✅ TrueRNG3 device detected and ready")
                else:
                    st.error("❌ TrueRNG3 device not detected")
            elif live_rng_type == "PseudoRNG":
                st.info("ℹ️ PseudoRNG (software-based) - always available")
        with cols_status_live[1]:
            if st.button("🔄 Refresh", key="live_refresh", use_container_width=True):
                refresh_device_status()
                st.rerun()
        
        # Device-specific options
        if live_rng_type == "BitBabbler":
            live_xor_mode = st.selectbox(
                "RAW(0)/XOR (1,2,3,4):",
                options=[0, 1, 2, 3, 4],
                index=0,
                key="live_xor"
            )
        else:
            live_xor_mode = 0
        
        # Live plot parameters
        live_sample_size = st.number_input(
            "Sample Size (bits):",
            min_value=8,
            value=2048,
            step=8,
            key="live_sample_size"
        )
        
        live_sample_interval = st.number_input(
            "Sample Interval (seconds):",
            min_value=1,
            value=1,
            step=1,
            key="live_sample_interval"
        )
        
        # Live plot controls
        if not st.session_state.live_plotting:
            if st.button("▶️ Start Live Plot", type="primary", use_container_width=True):
                start_live_plotting(live_rng_type, live_xor_mode, live_sample_size, live_sample_interval)
        else:
            if st.button("⏹️ Stop Live Plot", type="secondary", use_container_width=True):
                stop_live_plotting()
        
        # Status
        if st.session_state.live_plotting:
            st.success("🟢 Live Plotting Active")
        else:
            st.info("🟡 Live Plot Idle")
    
    with col2:
        st.subheader("📊 Live Z-Score Chart")
        

        
        # Auto-updating live chart
        # Only run fragment when live plotting
        run_every = 1 if st.session_state.live_plotting else None
        
        @st.fragment(run_every=run_every)
        def update_live_chart():
            if st.session_state.live_plotting:
                # Generate new data
                with perf_timer("collect_live_plot_sample"):
                    collect_live_plot_sample()
            
            if st.session_state.zscore_data and st.session_state.index_data:
                with perf_timer("plot_prepare"):
                    fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=st.session_state.index_data,
                    y=st.session_state.zscore_data,
                    mode='lines',
                    name='Z-Score',
                    line=dict(color='orange', width=2)
                ))
                
                with perf_timer("plot_layout"):
                    fig.update_layout(
                        title="Live Z-Score Plot",
                        xaxis_title=f"Number of samples (one sample every {live_sample_interval} second(s))",
                        yaxis_title=f"Z-Score - Sample Size = {live_sample_size} bits",
                        height=400,
                        showlegend=False,
                        uirevision=True,
                        transition_duration=0
                    )
                
                with perf_timer("plot_render"):
                    st.plotly_chart(fig, use_container_width=True)
                
                # Show current statistics
                if st.session_state.zscore_data:
                    current_zscore = st.session_state.zscore_data[-1]
                    current_samples = st.session_state.index_data[-1]
                    
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    with col_stat1:
                        st.metric("Current Z-Score", f"{current_zscore:.3f}")
                    with col_stat2:
                        st.metric("Samples Collected", current_samples)
                    with col_stat3:
                        if current_zscore > 2:
                            st.metric("Status", "🔴 High", delta="Above +2σ")
                        elif current_zscore < -2:
                            st.metric("Status", "🔴 Low", delta="Below -2σ")
                        else:
                            st.metric("Status", "🟢 Normal", delta="Within ±2σ")
            else:
                st.info("📊 Chart will appear here when live plotting starts")
        
        update_live_chart()

def render_instructions_tab():
    st.header("📖 Instructions")
    
    # Read and display README content using cached function
    instruction_text = read_file_content("README.md")
    if instruction_text == "File not found.":
        st.error("README.md file not found. Please ensure it exists in the project directory.")
    else:
        # Convert markdown to display properly
        st.markdown(instruction_text)

def collect_data_sample():
    """Collect a single data sample based on current settings"""
    if not st.session_state.collecting or not st.session_state.current_values:
        return
    
    now = datetime.now()
    if st.session_state.get('next_sample_time') is None:
        st.session_state['next_sample_time'] = now
    
    values = st.session_state.current_values
    file_name = st.session_state.file_name
    
    # Catch up loop to avoid missing samples due to jitter
    loops = 0
    while (now + timedelta(seconds=JITTER_TOLERANCE_SEC)) >= st.session_state['next_sample_time'] and loops < 3:
        try:
            if values["bit_ac"]:
                collect_bitbabbler_sample(values, file_name)
            elif values['true3_ac']:
                collect_trng3_sample(values, file_name)
            elif values['pseudo_rng_ac']:
                collect_pseudo_sample(values, file_name)
            
            st.session_state.last_update_time = now
            st.session_state['next_sample_time'] = st.session_state['next_sample_time'] + timedelta(seconds=st.session_state.sample_interval)
            loops += 1
        except Exception as e:
            print(f"Data collection error: {e}")
            st.session_state.collecting = False
            break

def collect_bitbabbler_sample(values, file_name):
    """Collect a single BitBabbler sample"""
    sample_value = int(values["ac_bit_count"])
    sample_bytes = int(sample_value / 8)
    folds = int(values.get("ac_combo", 0))
    
    try:
        with open(file_name + '.bin', "ab+") as bin_file:
            with perf_timer("bitb.read_bytes"):
                chunk = dev_bitb.read_bytes(sample_bytes, folds)
            if chunk:
                with perf_timer("file.write_bin"):
                    bin_file.write(chunk)
            else:
                st.error("❌ **No data received from BitBabbler**")
                st.error("Device may be disconnected or not responding properly.")
                st.session_state.collecting = False
                st.rerun()
                return
        
        # Count ones quickly without BitArray
        num_ones_array = count_ones_in_bytes(chunk)
        with perf_timer("csv.write_count"):
            storage_service.write_csv_count(num_ones_array, file_name)
        
        # Update session state (capped)
        st.session_state.collected_data.append({
            'timestamp': time.time(),
            'ones': num_ones_array,
            'sample_size': sample_value
        })
        if len(st.session_state.collected_data) > COLLECT_MAX_HISTORY:
            st.session_state.collected_data = st.session_state.collected_data[-COLLECT_MAX_HISTORY:]
        
    except RuntimeError as e:
        if "not found" in str(e).lower():
            st.error("❌ **BitBabbler device not found!**")
            st.error("Please check that your BitBabbler is properly connected to USB.")
            st.error("**Troubleshooting:** Try reconnecting the device or check driver installation.")
        elif "initialize" in str(e).lower():
            st.error("❌ **BitBabbler initialization failed!**")
            st.error("Device found but failed to initialize. Try reconnecting the device.")
        else:
            st.error(f"❌ **BitBabbler error:** {str(e)}")
        st.session_state.collecting = False
        st.rerun()
    except OSError as e:
        if is_device_not_found_error(e):
            st.error("❌ **BitBabbler device disconnected!**")
            st.error("Please check that your BitBabbler is properly connected to USB and try again.")
            st.error("**Troubleshooting steps:**")
            for step in get_platform_specific_troubleshooting("BitBabbler"):
                st.error(step)
        else:
            st.error(f"❌ **BitBabbler device error:** {str(e)}")
        st.session_state.collecting = False
        st.rerun()
    except Exception as e:
        st.error(f"❌ **BitBabbler collection error:** {str(e)}")
        st.error("This may indicate a device connection or driver issue.")
        st.session_state.collecting = False
        st.rerun()

def collect_trng3_sample(values, file_name):
    """Collect a single TrueRNG3 sample"""
    sample_value = int(values["ac_bit_count"])
    blocksize = int(sample_value / 8)
    
    ports_available = list(list_ports.comports())
    rng_com_port = None
    for temp in ports_available:
        if temp[1].startswith("TrueRNG"):
            if rng_com_port is None:
                rng_com_port = str(temp[0])
    
    if rng_com_port is None:
        st.error("❌ **TrueRNG3 device not found!**")
        st.error("Please check that your TrueRNG3 is properly connected to USB and try again.")
        st.session_state.collecting = False
        st.rerun()
        return
    
    try:
        with open(file_name + '.bin', "ab") as bin_file:
            with perf_timer("serial.open"):
                ser = serial.Serial(port=rng_com_port, timeout=10)
            if not ser.isOpen():
                with perf_timer("serial.ensure_open"):
                    ser.open()
            with perf_timer("serial.dtr_flush"):
                ser.setDTR(True)
                ser.flushInput()
            
            with perf_timer("serial.read"):
                x = ser.read(blocksize)
            with perf_timer("file.write_bin"):
                bin_file.write(x)
            with perf_timer("serial.close"):
                ser.close()
        
        # Count ones quickly without BitArray
        num_ones_array = count_ones_in_bytes(x)
        with perf_timer("csv.write_count"):
            storage_service.write_csv_count(num_ones_array, file_name)
        
        # Update session state (capped)
        st.session_state.collected_data.append({
            'timestamp': time.time(),
            'ones': num_ones_array,
            'sample_size': sample_value
        })
        if len(st.session_state.collected_data) > COLLECT_MAX_HISTORY:
            st.session_state.collected_data = st.session_state.collected_data[-COLLECT_MAX_HISTORY:]
        
    except serial.SerialException as e:
        st.error("❌ **TrueRNG3 device disconnected!**")
        st.error("Please check that your TrueRNG3 is properly connected to USB and try again.")
        st.session_state.collecting = False
        st.rerun()
    except Exception as e:
        st.error(f"❌ **TrueRNG3 collection error:** {str(e)}")
        st.session_state.collecting = False
        st.rerun()

def collect_pseudo_sample(values, file_name):
    """Collect a single Pseudo RNG sample"""
    sample_value = int(values["ac_bit_count"])
    blocksize = int(sample_value / 8)
    
    try:
        with open(file_name + '.bin', "ab") as bin_file:
            with perf_timer("pseudo.read_bytes"):
                x = dev_pseudo.read_bytes(blocksize)
            with perf_timer("file.write_bin"):
                bin_file.write(x)
        
        # Count ones quickly without BitArray
        num_ones_array = count_ones_in_bytes(x)
        with perf_timer("csv.write_count"):
            storage_service.write_csv_count(num_ones_array, file_name)
        
        # Update session state (capped)
        st.session_state.collected_data.append({
            'timestamp': time.time(),
            'ones': num_ones_array,
            'sample_size': sample_value
        })
        if len(st.session_state.collected_data) > COLLECT_MAX_HISTORY:
            st.session_state.collected_data = st.session_state.collected_data[-COLLECT_MAX_HISTORY:]
        
    except Exception as e:
        print(f"Pseudo RNG collection error: {e}")
        st.session_state.collecting = False

def start_data_collection(rng_type, xor_mode, sample_size, sample_interval):
    """Start data collection process"""
    # Validate parameters
    if not svc_utils.is_valid_params(sample_size, sample_interval):
        st.error("❌ Invalid parameters. Sample size must be divisible by 8.")
        return
    
    # Create values dict for compatibility with existing functions
    values = create_values_dict(rng_type, xor_mode, sample_size, sample_interval, "ac_")
    
    # Device detection via adapters
    # Force a fresh detection when starting collection
    # Take a fresh detection snapshot on start
    refresh_device_status()
    if not validate_device_detection(values, rng_type, force_refresh=True):
        show_device_error(rng_type)
        return
    
    # Generate filename using service
    device_suffix = "bitb" if values["bit_ac"] else "trng" if values["true3_ac"] else "pseudo"
    file_name = fn_service.format_capture_name(device_suffix, sample_size, sample_interval, xor_mode if device_suffix == "bitb" else None)
    file_name = os.path.join(DATA_DIR, file_name)
    
    # Start collection
    st.session_state.collecting = True
    st.session_state.current_values = values
    st.session_state.file_name = file_name
    st.session_state.collected_data = []
    st.session_state.sample_size = sample_size
    st.session_state.sample_interval = sample_interval
    st.session_state.last_update_time = datetime.now()
    st.session_state.next_live_sample_time = st.session_state.last_update_time
    st.session_state.next_sample_time = st.session_state.last_update_time
    
    # No seedd needed when using bbpy
    
    st.success("✅ Data collection started!")
    st.rerun()

def stop_data_collection():
    """Stop data collection process"""
    st.session_state.collecting = False
    # Nothing to kill for bbpy
    st.success("⏹️ Data collection stopped!")
    # Force rerun to update fragments
    st.rerun()

def collect_live_plot_sample():
    """Collect a single live plot sample based on current settings"""
    if not st.session_state.live_plotting or not st.session_state.current_values:
        return
    
    now = datetime.now()
    if st.session_state.get('next_live_sample_time') is None:
        st.session_state['next_live_sample_time'] = now
    
    values = st.session_state.current_values
    file_name = st.session_state.file_name
    
    # For live chart, collect at most one sample per update tick to avoid bursts
    if (now + timedelta(seconds=JITTER_TOLERANCE_SEC)) >= st.session_state['next_live_sample_time']:
        try:
            if values['live_bit_ac']:
                collect_live_bitbabbler_sample(values, file_name)
            elif values['live_true3_ac']:
                collect_live_trng3_sample(values, file_name)
            elif values['live_pseudo_rng_ac']:
                collect_live_pseudo_sample(values, file_name)
            
            st.session_state.last_update_time = now
            st.session_state['next_live_sample_time'] = st.session_state['next_live_sample_time'] + timedelta(seconds=st.session_state.sample_interval)
        except Exception as e:
            print(f"Live plotting error: {e}")
            st.session_state.live_plotting = False

def collect_live_bitbabbler_sample(values, file_name):
    """Collect a single live BitBabbler sample"""
    sample_value = int(values["live_bit_count"])
    sample_bytes = int(sample_value / 8)
    folds = int(values.get("live_combo", 0))
    
    try:
        with open(file_name + '.bin', "ab+") as bin_file:
            with perf_timer("bitb.read_bytes"):
                chunk = dev_bitb.read_bytes(sample_bytes, folds)
            if chunk:
                with perf_timer("file.write_bin"):
                    bin_file.write(chunk)
            else:
                st.error("❌ **No data received from BitBabbler**")
                st.error("Device may be disconnected or not responding properly.")
                st.session_state.live_plotting = False
                st.rerun()
                return
        
        # Count ones quickly without BitArray
        num_ones_array = count_ones_in_bytes(chunk)
        st.session_state.csv_sum += num_ones_array
        st.session_state.csv_count += 1
        with perf_timer("csv.write_count"):
            storage_service.write_csv_count(num_ones_array, file_name)
        
        # Calculate Z-score (streaming)
        zscore_csv = calculate_zscore_streaming(st.session_state.csv_sum, st.session_state.csv_count, sample_value)
        
        # Update session state
        st.session_state.zscore_data.append(zscore_csv)
        st.session_state.index_data.append(st.session_state.csv_count)
        
    except RuntimeError as e:
        if "not found" in str(e).lower():
            st.error("❌ **BitBabbler device not found!**")
            st.error("Please check that your BitBabbler is properly connected to USB.")
            st.error("**Troubleshooting:** Try reconnecting the device or check driver installation.")
        elif "initialize" in str(e).lower():
            st.error("❌ **BitBabbler initialization failed!**")
            st.error("Device found but failed to initialize. Try reconnecting the device.")
        else:
            st.error(f"❌ **BitBabbler error:** {str(e)}")
        st.session_state.live_plotting = False
        st.rerun()
    except OSError as e:
        if is_device_not_found_error(e):
            st.error("❌ **BitBabbler device disconnected!**")
            st.error("Please check that your BitBabbler is properly connected to USB and try again.")
            st.error("**Troubleshooting steps:**")
            for step in get_platform_specific_troubleshooting("BitBabbler"):
                st.error(step)
        else:
            st.error(f"❌ **BitBabbler device error:** {str(e)}")
        st.session_state.live_plotting = False
        st.rerun()
    except Exception as e:
        st.error(f"❌ **Live BitBabbler error:** {str(e)}")
        st.error("This may indicate a device connection or driver issue.")
        st.session_state.live_plotting = False
        st.rerun()

def collect_live_trng3_sample(values, file_name):
    """Collect a single live TrueRNG3 sample"""
    sample_value = int(values["live_bit_count"])
    blocksize = int(sample_value / 8)
    
    try:
        with open(file_name + '.bin', "ab+") as bin_file:
            with perf_timer("trng.read_bytes"):
                chunk = dev_trng.read_bytes(blocksize)
            with perf_timer("file.write_bin"):
                bin_file.write(chunk)
        
        # Count ones quickly without BitArray
        num_ones_array = count_ones_in_bytes(chunk)
        st.session_state.csv_sum += num_ones_array
        st.session_state.csv_count += 1
        with perf_timer("csv.write_count"):
            storage_service.write_csv_count(num_ones_array, file_name)
        
        # Calculate Z-score (streaming)
        zscore_csv = calculate_zscore_streaming(st.session_state.csv_sum, st.session_state.csv_count, sample_value)
        
        # Update session state
        st.session_state.zscore_data.append(zscore_csv)
        st.session_state.index_data.append(st.session_state.csv_count)
        
    except OSError as e:
        if is_device_not_found_error(e):
            st.error("❌ **TrueRNG3 device disconnected!**")
            st.error("Please check that your TrueRNG3 is properly connected to USB and try again.")
            st.error("**Troubleshooting steps:**")
            for step in get_platform_specific_troubleshooting("TrueRNG"):
                st.error(step)
            st.session_state.live_plotting = False
            st.rerun()
        else:
            st.error(f"❌ **TrueRNG3 device error:** {str(e)}")
            st.session_state.live_plotting = False
            st.rerun()
    except Exception as e:
        st.error(f"❌ **Live TrueRNG3 error:** {str(e)}")
        st.session_state.live_plotting = False
        st.rerun()

def collect_live_pseudo_sample(values, file_name):
    """Collect a single live Pseudo RNG sample"""
    sample_value = int(values["live_bit_count"])
    blocksize = int(sample_value / 8)
    
    try:
        with open(file_name + '.bin', "ab+") as bin_file:
            with perf_timer("pseudo.token_bytes"):
                chunk = secrets.token_bytes(blocksize)
            with perf_timer("file.write_bin"):
                bin_file.write(chunk)
        
        # Count ones quickly without BitArray
        num_ones_array = count_ones_in_bytes(chunk)
        st.session_state.csv_sum += num_ones_array
        st.session_state.csv_count += 1
        with perf_timer("csv.write_count"):
            storage_service.write_csv_count(num_ones_array, file_name)
        
        # Calculate Z-score (streaming)
        zscore_csv = calculate_zscore_streaming(st.session_state.csv_sum, st.session_state.csv_count, sample_value)
        
        # Update session state with capped history
        st.session_state.zscore_data.append(zscore_csv)
        st.session_state.index_data.append(st.session_state.csv_count)
        if len(st.session_state.zscore_data) > LIVE_MAX_POINTS:
            st.session_state.zscore_data = st.session_state.zscore_data[-LIVE_MAX_POINTS:]
            st.session_state.index_data = st.session_state.index_data[-LIVE_MAX_POINTS:]
        
    except Exception as e:
        print(f"Live Pseudo RNG error: {e}")
        st.session_state.live_plotting = False

def start_live_plotting(rng_type, xor_mode, sample_size, sample_interval):
    """Start live plotting process"""
    # Validate parameters
    if not svc_utils.is_valid_params(sample_size, sample_interval):
        st.error("❌ Invalid parameters. Sample size must be divisible by 8.")
        return
    
    # Create values dict for compatibility
    values = create_values_dict(rng_type, xor_mode, sample_size, sample_interval, "live_")
    
    # Device detection via adapters
    # Force a fresh detection when starting live plotting
    # Take a fresh detection snapshot on start
    refresh_device_status()
    if not validate_device_detection(values, rng_type, force_refresh=True):
        show_device_error(rng_type)
        return
    
    # Generate filename using service
    device_suffix = "bitb" if values["live_bit_ac"] else "trng" if values["live_true3_ac"] else "pseudo"
    file_name = fn_service.format_capture_name(device_suffix, sample_size, sample_interval, xor_mode if device_suffix == "bitb" else None)
    file_name = os.path.join(DATA_DIR, file_name)
    
    # Start live plotting
    st.session_state.live_plotting = True
    st.session_state.current_values = values
    st.session_state.file_name = file_name
    st.session_state.zscore_data = []
    st.session_state.index_data = []
    st.session_state.csv_ones = []
    st.session_state.csv_sum = 0
    st.session_state.csv_count = 0
    st.session_state.sample_size = sample_size
    st.session_state.sample_interval = sample_interval
    st.session_state.last_update_time = datetime.now()
    
    # No seedd needed when using bbpy
    
    st.success("✅ Live plotting started!")
    st.rerun()

def stop_live_plotting():
    """Stop live plotting process"""
    st.session_state.live_plotting = False
    # Nothing to kill for bbpy
    st.success("⏹️ Live plotting stopped!")
    # Force rerun to update fragments
    st.rerun()

if __name__ == "__main__":
    main()
