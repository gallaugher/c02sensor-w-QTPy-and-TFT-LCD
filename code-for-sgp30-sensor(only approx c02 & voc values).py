# CO2 Sensor in CircuitPython
# Uses: Adafruit SGP 30 STEMMA-QT Sensor,
# Adafruit QT PY ESP32-S3 board, and
# Adafruit 1.44" Color TFT LCD Display with MicroSD Card breakout ST7735R display

# IMPORTS
import board, time, digitalio, json
import adafruit_sgp30
import displayio, terminalio
from adafruit_st7735r import ST7735R
from displayio import FourWire
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

# Display Constants
WIDTH = 128
HEIGHT = 128
HORIZONTAL_START = 8
VERTICAL_MOVE = 8
CO2_VAL_VERTICAL = 37
ICON_VERTICAL = 89
VOC_HORIZONTAL = 67
VOC_STATUS_VERTICAL = 76
VOC_VERTICAL = 100

# Sensor and Timing Constants
CO2_THRESHOLD = 1000
VOC_THRESHOLD = 250
UPDATE_INTERVAL = 4
WARMUP_TIME = 15
CALIBRATION_TIME = 12 * 3600
BASELINE_SAVE_INTERVAL = 3600

# Animation Constants
LOADING_INTERVAL = 0.05
LOADING_PHASE_SLEEP = 0.01
SPINNER_CHARS = ['|', '/', '-', '\\']

# Color Constants
COLOR_BLACK = 0x000000
COLOR_WHITE = 0xFFFFFF
COLOR_GREEN = 0x00FF00
COLOR_RED = 0xFF0000

# GLOBAL VARIABLES
start_time = None
last_baseline_save = 0
animation_frame = 0
last_animation_time = time.monotonic()
prev_values = {
    "co2": None,
    "voc": None,
    "is_high": None
}

# FUNCTION DEFINITIONS
# Baseline management functions
def initialize_baseline_tracking():
    """Start tracking baseline timing"""
    global start_time
    start_time = time.monotonic()

def load_baseline(sensor):
    """Load saved baseline values if available"""
    try:
        with open("sgp30_baseline.json", "r") as f:
            baseline = json.load(f)
            sensor.set_iaq_baseline(
                baseline['eCO2'],
                baseline['TVOC']
            )
            print("Loaded stored baseline values:")
            print(f"eCO2: 0x{baseline['eCO2']:x}, TVOC: 0x{baseline['TVOC']:x}")
            return True
    except (OSError, KeyError):
        print("No stored baseline found - starting fresh calibration")
        return False

def save_baseline(sensor):
    """Save current baseline values"""
    global last_baseline_save

    # Only save if we're past initial calibration
    current_time = time.monotonic()
    if (current_time - start_time) > CALIBRATION_TIME:
        if (current_time - start_time) > CALIBRATION_TIME:
            try:
                baseline = {
                    'eCO2': sensor.baseline_eCO2,
                    'TVOC': sensor.baseline_TVOC
                }
                with open("sgp30_baseline.json", "w") as f:
                    json.dump(baseline, f)
                print("Saved new baseline values")
                last_baseline_save = current_time
            except OSError as e:
                if e.args[0] == 30:  # Read-only filesystem
                    print("Could not save baseline - filesystem is read-only")
                else:
                    print(f"Error saving baseline: {e}")

def check_warmup_status():
    """Check if sensor is warmed up"""
    elapsed = time.monotonic() - start_time
    return {
        'warmed_up': elapsed > WARMUP_TIME,
        'fully_calibrated': elapsed > CALIBRATION_TIME,
        'elapsed_time': elapsed
    }

def update_baseline(sensor):
    """Check if baseline needs saving"""
    current_time = time.monotonic()
    # Save baseline every hour if calibrated
    if (current_time - last_baseline_save) > BASELINE_SAVE_INTERVAL:
        save_baseline(sensor)

# Display functions
def update_spinner_animation(frame):
    """Rotating line animation."""
    co2_label.text = f"Loading {SPINNER_CHARS[frame]}"
    voc_label.text = f"{SPINNER_CHARS[frame]}"

def show_loading_screen():
    """Display loading message while sensor initializes."""
    co2_label.text = "Loading..."
    co2_value.text = ""
    voc_status.text = ""
    voc_label.text = ""
    icon_label.text = ""

def update_labels(co2, voc, is_high):
    """Update display labels with new values"""
    # Check VOC status
    voc_is_high = voc >= VOC_THRESHOLD

    # Update only the labels that have changed.
    if prev_values["is_high"] != is_high:
        # Update background color by changing the palette
        color_palette[0] = 0xFFFFFF if is_high else 0x000000
        new_color = 0x000000 if is_high else 0xFFFFFF

        for label_obj in [co2_label, co2_value, voc_status, voc_label]:
            label_obj.color = new_color

        # Update icon
        icon_label.text = "" if not is_high else ""
        icon_label.color = 0xFF0000 if is_high else 0x00FF00
        # icon_label.color = 0x00FF00 if not is_high else 0xFF0000

    # Update text only if values have changed
    if prev_values["co2"] != co2:
        co2_label.text = f"CO2: {"HIGH" if is_high else "good"}"
        co2_value.text = str(co2)

    if prev_values["voc"] != voc:
        voc_status.text = "VOC:"
        voc_status.color = COLOR_GREEN if not voc_is_high else COLOR_RED
        voc_label.text = f"{voc}"

    # Turn on LED if either CO2 or VOC is high
    led.value = False if (not is_high and not voc_is_high) else True
    # led.value = is_high # LED will turn on when CO2 is high

    # Store new values
    prev_values.update({
        "co2": co2,
        "voc": voc,
        "is_high": is_high
    })

def update():
    """Main update function for sensor reading and display"""
    global animation_frame, last_animation_time
    current_time = time.monotonic()

    # Check sensor warmup status
    status = check_warmup_status()

    try:
        if not status['warmed_up']:
            # Show loading animation during warmup
            if current_time - last_animation_time >= LOADING_INTERVAL:
                update_spinner_animation(animation_frame % len(SPINNER_CHARS))
                animation_frame += 1
                last_animation_time = current_time
        else:
            # Sensor is warmed up, read values
            co2 = int(sensor.eCO2)
            voc = int(sensor.TVOC)
            is_high = co2 >= CO2_THRESHOLD

            print(f"CO2: {co2}ppm")
            print(f"VOC: {voc}ppb")

            update_labels(co2, voc, is_high)

            # Check if we should save baseline
            update_baseline(sensor)

    except Exception as e:
        print(f"Error reading sensor: {e}")

# 5. INITIALIZATION CODE
# Setup LED
led = digitalio.DigitalInOut(board.A0)
led.direction = digitalio.Direction.OUTPUT
led.value = False

# Setup CO2 Sensor
i2c = board.STEMMA_I2C()
sensor = adafruit_sgp30.Adafruit_SGP30(i2c)
print("Serial number:", [hex(i) for i in sensor.serial])
sensor.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)

# Initialize baseline tracking
initialize_baseline_tracking()
load_baseline(sensor)

print("Waiting for first measurement....")

# Setup Display
displayio.release_displays()
spi = board.SPI()
tft_cs = board.TX
tft_dc = board.RX

display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.D9)
display = ST7735R(display_bus, width=128, height=128, colstart=2, rowstart=1)

# Load fonts
try:
    font = bitmap_font.load_font("fonts/AvenirNextCondensed-Medium-28.bdf")
    icons = bitmap_font.load_font("fonts/FontAwesomeRegular-28.bdf")
except Exception as e:
    print(f"Error loading fonts. Your CIRCUITPY board probably doesn't have usable fonts with these names in a folder named 'fonts': {e}")

# Create display group and background
main_group = displayio.Group()
color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # Start with black background
bg_tile = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)

# Create all label objects
co2_label = label.Label(
    terminalio.FONT, scale=2, color=0xFFFFFF,
    x=HORIZONTAL_START, y=5+VERTICAL_MOVE)
co2_value = label.Label(
    font, scale=2, color=0xFFFFFF,
    x=HORIZONTAL_START, y=CO2_VAL_VERTICAL+VERTICAL_MOVE)
voc_status = label.Label(
    terminalio.FONT, scale=2, color=0xFFFFFF,
    x=VOC_HORIZONTAL, y=VOC_STATUS_VERTICAL+VERTICAL_MOVE)
voc_label = label.Label(
    terminalio.FONT, scale=3, color=0xFFFFFF,
    x=VOC_HORIZONTAL, y=VOC_VERTICAL+VERTICAL_MOVE)
icon_label = label.Label(
    icons, scale=1, color=0x00FF00,
    x=HORIZONTAL_START, y=ICON_VERTICAL+VERTICAL_MOVE)

# Add all elements to main group
main_group.append(bg_tile)
for label_obj in [co2_label, co2_value, voc_status, voc_label, icon_label]:
    main_group.append(label_obj)

# Show the display group
display.root_group = main_group

# Show initial loading screen
show_loading_screen()

# 6. MAIN LOOP
while True:
    update()
    if prev_values["co2"] is None:
        time.sleep(LOADING_PHASE_SLEEP)  # Fast updates during loading animation
    else:
        time.sleep(UPDATE_INTERVAL)  # Normal delay once sensor is working
