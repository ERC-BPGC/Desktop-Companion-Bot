import serial
import serial.tools.list_ports
import time
import sys
import subprocess
import shutil

# --- CONFIGURATION ---
BAUD_RATE = 115200

# Detect OS once at startup
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')
IS_WINDOWS = sys.platform == 'win32'

# Check available Linux tools
HAS_PLAYERCTL = IS_LINUX and shutil.which('playerctl') is not None
HAS_PACTL = IS_LINUX and shutil.which('pactl') is not None
HAS_AMIXER = IS_LINUX and shutil.which('amixer') is not None

# macOS media key codes (NX_KEYTYPE)
MACOS_MEDIA_KEYS = {
    'play_pause': 16,  # NX_KEYTYPE_PLAY
    'next': 17,        # NX_KEYTYPE_NEXT
    'prev': 18,        # NX_KEYTYPE_PREVIOUS (rewind)
}

def send_macos_media_key(key_type):
    """Send a media key event on macOS using Quartz/CoreGraphics."""
    try:
        import Quartz
        
        # Key down event
        event = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
            Quartz.NSEventTypeSystemDefined,  # 14
            (0, 0),
            0xa00,  # Key down flag
            0,
            0,
            None,
            8,  # NSEventSubtypeScreenChanged / media key subtype
            (key_type << 16) | (0xa << 8),  # data1: key_type in high word, flags in low
            -1
        )
        if event:
            cg_event = event.CGEvent()
            if cg_event:
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, cg_event)
        
        # Key up event
        event_up = Quartz.NSEvent.otherEventWithType_location_modifierFlags_timestamp_windowNumber_context_subtype_data1_data2_(
            Quartz.NSEventTypeSystemDefined,
            (0, 0),
            0xb00,  # Key up flag
            0,
            0,
            None,
            8,
            (key_type << 16) | (0xb << 8),
            -1
        )
        if event_up:
            cg_event_up = event_up.CGEvent()
            if cg_event_up:
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, cg_event_up)
        
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"Error sending media key: {e}")
        return False

def get_serial_port():
    """Auto-detect or return platform-specific default port."""
    # Try to auto-detect USB serial devices
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if 'USB' in port.description or 'Serial' in port.description or 'usbserial' in port.device or 'usbmodem' in port.device:
            print(f"Auto-detected serial port: {port.device}")
            return port.device
    
    # Fallback to platform-specific defaults
    if sys.platform == 'darwin':  # macOS
        return '/dev/tty.usbserial-0001'
    elif sys.platform.startswith('linux'):
        return '/dev/ttyUSB0'
    else:  # Windows
        return 'COM3'

SERIAL_PORT = get_serial_port()

def listen_for_commands():
    ser = None
    print(f"Attempting to connect to {SERIAL_PORT}...")
    
    while True:
        try:
            # 1. Connection Logic
            if ser is None:
                ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
                ser.flush()
                print(f"Successfully connected to {SERIAL_PORT}.")
                print("Listening for gestures. Press Ctrl+C to exit.")

            # 2. Read Data
            if ser.in_waiting > 0:
                # FIX: errors='ignore' prevents crash on startup garbage data
                line = ser.readline().decode('utf-8', errors='ignore').rstrip()
                
                if line:
                    print(f"Received command: {line}")
                    execute_command(line)

        except serial.SerialException:
            # Simple disconnect handler
            print(f"Connection lost with {SERIAL_PORT}. Retrying in 2s...")
            if ser:
                ser.close()
            ser = None
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\nExiting program.")
            if ser:
                ser.close()
            break
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(1)

def run_applescript(script):
    """Run AppleScript command on macOS."""
    subprocess.run(['osascript', '-e', script], check=True)

def run_command(cmd):
    """Run a shell command silently."""
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def media_play_pause():
    if IS_MACOS:
        # Use system media key - works with ANY media player
        if not send_macos_media_key(MACOS_MEDIA_KEYS['play_pause']):
            # Fallback to common players
            run_applescript('''
                if application "Music" is running then
                    tell application "Music" to playpause
                else if application "Spotify" is running then
                    tell application "Spotify" to playpause
                end if
            ''')
    elif IS_LINUX:
        if HAS_PLAYERCTL:
            run_command(['playerctl', 'play-pause'])
        else:
            # Fallback: use dbus directly
            run_command(['dbus-send', '--print-reply', '--dest=org.mpris.MediaPlayer2.spotify',
                        '/org/mpris/MediaPlayer2', 'org.mpris.MediaPlayer2.Player.PlayPause'])
    else:  # Windows
        import pyautogui
        pyautogui.press('playpause')

def media_next():
    if IS_MACOS:
        # Use system media key - works with ANY media player
        if not send_macos_media_key(MACOS_MEDIA_KEYS['next']):
            # Fallback to common players
            run_applescript('''
                if application "Music" is running then
                    tell application "Music" to next track
                else if application "Spotify" is running then
                    tell application "Spotify" to next track
                end if
            ''')
    elif IS_LINUX:
        if HAS_PLAYERCTL:
            run_command(['playerctl', 'next'])
        else:
            run_command(['dbus-send', '--print-reply', '--dest=org.mpris.MediaPlayer2.spotify',
                        '/org/mpris/MediaPlayer2', 'org.mpris.MediaPlayer2.Player.Next'])
    else:  # Windows
        import pyautogui
        pyautogui.press('nexttrack')

def media_prev():
    if IS_MACOS:
        # Use system media key - works with ANY media player
        if not send_macos_media_key(MACOS_MEDIA_KEYS['prev']):
            # Fallback to common players
            run_applescript('''
                if application "Music" is running then
                    tell application "Music" to previous track
                else if application "Spotify" is running then
                    tell application "Spotify" to previous track
                end if
            ''')
    elif IS_LINUX:
        if HAS_PLAYERCTL:
            run_command(['playerctl', 'previous'])
        else:
            run_command(['dbus-send', '--print-reply', '--dest=org.mpris.MediaPlayer2.spotify',
                        '/org/mpris/MediaPlayer2', 'org.mpris.MediaPlayer2.Player.Previous'])
    else:  # Windows
        import pyautogui
        pyautogui.press('prevtrack')

def volume_up():
    if IS_MACOS:
        run_applescript('set volume output volume ((output volume of (get volume settings)) + 6.25)')
    elif IS_LINUX:
        if HAS_PACTL:
            run_command(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '+5%'])
        elif HAS_AMIXER:
            run_command(['amixer', 'set', 'Master', '5%+'])
    else:  # Windows
        import pyautogui
        pyautogui.press('volumeup')

def volume_down():
    if IS_MACOS:
        run_applescript('set volume output volume ((output volume of (get volume settings)) - 6.25)')
    elif IS_LINUX:
        if HAS_PACTL:
            run_command(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '-5%'])
        elif HAS_AMIXER:
            run_command(['amixer', 'set', 'Master', '5%-'])
    else:  # Windows
        import pyautogui
        pyautogui.press('volumedown')

def execute_command(command):
    # Added a small guard to prevent executing empty or garbage strings
    if not command or len(command) < 2:
        return

    try:
        if command == "PLAY_PAUSE":
            media_play_pause()
        elif command == "NEXT":
            media_next()
        elif command == "PREV":
            media_prev()
        elif command == "VOL_UP":
            volume_up()
        elif command == "VOL_DOWN":
            volume_down()
        else:
            print(f"Ignored unknown command: {command}")
    except Exception as e:
        print(f"Error executing command {command}: {e}")

def print_system_info():
    """Print detected OS and available tools."""
    print("=" * 50)
    print("SYSTEM DETECTION")
    print("=" * 50)
    if IS_MACOS:
        print(f"  OS: macOS (using AppleScript)")
    elif IS_LINUX:
        print(f"  OS: Linux")
        print(f"  Media control: {'playerctl' if HAS_PLAYERCTL else 'dbus (fallback)'}")
        print(f"  Volume control: {'pactl' if HAS_PACTL else ('amixer' if HAS_AMIXER else 'NOT AVAILABLE')}")
        if not HAS_PLAYERCTL:
            print("  TIP: Install playerctl for better media control: sudo apt install playerctl")
        if not HAS_PACTL and not HAS_AMIXER:
            print("  WARNING: No volume control tool found! Install pulseaudio-utils or alsa-utils")
    elif IS_WINDOWS:
        print(f"  OS: Windows (using pyautogui)")
    print("=" * 50)

if __name__ == "__main__":
    print_system_info()
    listen_for_commands()