# C02 Sensor in CircuitPython
# Uses an Adafruit SCD40 C02 Sensor & an
# Adafruit Adafruit ESP32-S2 Reverse TFT Feather with 8MB flash

import board, time, digitalio
import adafruit_scd4x
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
TEMP_HORIZONTAL = 67
TEMP_VERTICAL = 76
HUMID_VERTICAL = 105

# Sensor Constants
CO2_THRESHOLD = 1000
UPDATE_INTERVAL = 4

# Color Constants
COLOR_BLACK = 0x000000
COLOR_WHITE = 0xFFFFFF
COLOR_GREEN = 0x00FF00
COLOR_RED = 0xFF0000

# Add these constants near the top with your other constants
LOADING_INTERVAL = 0.05  # How fast the animation updates (in seconds)
LOADING_PHASE_SLEEP = 0.01 # How long to wait between loading animation updates
SPINNER_CHARS = ['|', '/', '-', '\\']  # For spinning animation

# Setup C02 Sensor
i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
scd4x = adafruit_scd4x.SCD4X(i2c)
print("Serial number:", [hex(i) for i in scd4x.serial_number])
scd4x.start_periodic_measurement()
print("Waiting for first measurement....")

# Setup Display
# Release any resources currently in use for the displays
displayio.release_displays()

spi = board.SPI()
# tft_cs = board.D5
# tft_dc = board.D6
tft_cs = board.TX
tft_dc = board.RX

display_bus = FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.D9)
display = ST7735R(display_bus, width=128, height=128, colstart=2, rowstart=1)

# Setup LED
# led = digitalio.DigitalInOut(board.D13)
# led.direction = digitalio.Direction.OUTPUT
# led.value = False

# Dictionary that holds previous values. Values accessed ex: last_value["co2"]
prev_values = {
    "co2": None,
    "temp": None,
    "humidity": None,
    "is_high": None
}

# Load fonts once
try:
    font = bitmap_font.load_font("fonts/AvenirNextCondensed-Medium-28.bdf")
    icons = bitmap_font.load_font("fonts/FontAwesomeRegular-28.bdf")
except Exception as e:
    print(f"Error loading fonts. Your CIRCUITPY board probably don't have usable fonts with these names in a folder named 'fonts': {e}")

# Create base display group
main_group = displayio.Group()

# Create single background with palette
color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000  # Start with black background
bg_tile = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)

# Create all label objects once
co2_label = label.Label(
    terminalio.FONT, scale=2, color=0xFFFFFF,
    x=HORIZONTAL_START, y=5+VERTICAL_MOVE)
co2_value = label.Label(
    font, scale=2, color=0xFFFFFF,
    x=HORIZONTAL_START, y=CO2_VAL_VERTICAL+VERTICAL_MOVE)
temp_label = label.Label(
    terminalio.FONT, scale=3, color=0xFFFFFF,
    x=TEMP_HORIZONTAL, y=TEMP_VERTICAL+VERTICAL_MOVE)
humid_label = label.Label(
    terminalio.FONT, scale=3, color=0xFFFFFF,
    x=TEMP_HORIZONTAL, y=HUMID_VERTICAL+VERTICAL_MOVE)
icon_label = label.Label(
    icons, scale=1, color=0x00FF00,
    x=HORIZONTAL_START, y=ICON_VERTICAL+VERTICAL_MOVE)

# Add all elements to main group
main_group.append(bg_tile)
for label_obj in [co2_label, co2_value,
                  temp_label, humid_label,
                  icon_label]:
    main_group.append(label_obj)

# Show the display group
display.root_group = main_group

# Different animation styles you can choose from:
def update_spinner_animation(frame):
    """Rotating line animation."""
    co2_label.text = f"Loading {SPINNER_CHARS[frame]}"
    temp_label.text = f"{SPINNER_CHARS[frame]}"
    humid_label.text = f"{SPINNER_CHARS[frame]}"

def show_loading_screen():
    """Display loading message while sensor initializes."""
    co2_label.text = "Loading..."
    co2_value.text = ""
    temp_label.text = "..."
    humid_label.text = "..."
    icon_label.text = ""

# Show loading screen
show_loading_screen()

def update_labels(co2, temp, humidity, is_high):
    # Update only the labels that have changed.
    if prev_values["is_high"] != is_high:

        # Update background color by changing the palette
        color_palette[0] = 0xFFFFFF if is_high else 0x000000
        new_color = 0x000000 if is_high else 0xFFFFFF

        for label_obj in [co2_label, co2_value,
                          temp_label, humid_label]:
            label_obj.color = new_color

        # Update icon
        icon_label.text = "" if not is_high else ""
        icon_label.color = 0x00FF00 if not is_high else 0xFF0000
        # icon_label.x = 44 if not is_high else 61  # Move 15 pixels right when high
        # led.value = is_high # LED will turn on when CO2 is high

        # Update text only if values have changed
    if prev_values["co2"] != co2:
        co2_label.text = f"CO2: {"HIGH" if is_high else "good"}"
        co2_value.text = str(co2)

    if prev_values["temp"] != temp:
        temp_label.text = f"{temp}°F"

    if prev_values["humidity"] != humidity:
        humid_label.text = f"{humidity}%"

    # Store new values
    prev_values.update({
        "co2": co2,
        "temp": temp,
        "humidity": humidity,
        "is_high": is_high
    })

# Used with animation while loading
animation_frame = 0
last_animation_time = time.monotonic()

def update():
    # Read sensor and update display if data is ready
    global animation_frame, last_animation_time

    current_time = time.monotonic()

    try:
        if scd4x.data_ready:
            co2 = int(scd4x.CO2)
            temp = int((scd4x.temperature * (9 / 5)) + 32)
            humidity = int(scd4x.relative_humidity)
            is_high = co2 >= CO2_THRESHOLD # True if c02 level is high

            print(f"CO2: {co2}ppm")
            print(f"Temperature: {temp}°F")
            print(f"Humidity: {humidity}%\n")

            update_labels(co2, temp, humidity, is_high)
        else:
            # Only animate if we've never received data
            if prev_values["co2"] is None:
                if current_time - last_animation_time >= LOADING_INTERVAL:
                    update_spinner_animation(animation_frame % len(SPINNER_CHARS))
                    animation_frame += 1
                    last_animation_time = current_time
    except Exception as e:
        print(f"Error reading sensor: {e}")

while True:
    update()
    # Use shorter delay while loading, normal delay once sensor is ready
    if prev_values["co2"] is None:
        time.sleep(LOADING_PHASE_SLEEP)  # Fast updates during loading animation
    else:
        time.sleep(UPDATE_INTERVAL)  # Normal delay once sensor is working
