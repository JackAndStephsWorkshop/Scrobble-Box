buffer = "0"*2048
import gc
print("starting program. Free memory:", gc.mem_free())
import board
print("Free memory after board:", gc.mem_free())
import digitalio
print("Free memory after digitalio:", gc.mem_free())
import time
print("Free memory after time:", gc.mem_free())
import adafruit_requests as requests
print("Free memory after adafruit_requests:", gc.mem_free())
import socketpool
print("Free memory after socketpool:", gc.mem_free())
import ssl
print("Free memory after ssl:", gc.mem_free())
import wifi
print("Free memory after wifi:", gc.mem_free())
import microcontroller
import rtc
print("Free memory after rtc:", gc.mem_free())
import adafruit_requests as requests

def setup_wifi():
    # Set up WiFi
    wifi.radio.connect("YOUR WIRELESS NETWORK NAME HERE", "YOUR WIRELESS NETWORK PASSWORD HERE")
    gc.collect()  # Run garbage collection

# Initialize the Spinitron switch
switch = digitalio.DigitalInOut(board.GP2)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

# Initialize the Gush switch
switch2 = digitalio.DigitalInOut(board.GP1)
switch2.direction = digitalio.Direction.INPUT
switch2.pull = digitalio.Pull.UP

# Setup the keyboard switch
kbswitch = digitalio.DigitalInOut(board.GP16) 
kbswitch.direction = digitalio.Direction.INPUT
kbswitch.pull = digitalio.Pull.UP

def get_current_time():
    # Get the current time from an NTP server
    pool = socketpool.SocketPool(wifi.radio)
    req = requests.Session(pool, ssl.create_default_context())
    response = req.get("http://worldtimeapi.org/api/ip")
    data = response.json()
    timestamp = data['unixtime']
    response.close()  # Close the response

    # Set the RTC to the current time
    real_time_clock = rtc.RTC()
    real_time_clock.datetime = time.localtime(timestamp)

    # Now time.time() will return the current time
    print(time.time())
    gc.collect()  # Run garbage collection

def scrobble_track(artist, track, timestamp):
    pool = socketpool.SocketPool(wifi.radio)
    req = requests.Session(pool, ssl.create_default_context())
    print("starting scrobbling function. Free memory:", gc.mem_free())

    # API endpoint
    url = "https://ws.audioscrobbler.com/2.0/"

    # If artist and track are not provided, get the current song
    if artist is None or track is None:
        artist, track = get_current_song(req)

    # Parameters for the scrobble request
    params = {
        "method": "track.scrobble",
        "artist": artist,
        "track": track,
        "timestamp": str(timestamp),
        "api_key": API_KEY,
        "sk": SESSION_KEY,
    }

    import adafruit_hashlib as hashlib
    print("Free memory after adafruit_hashlib:", gc.mem_free())


    # Generate the API signature
    signature_string = "".join(key + params[key] for key in sorted(params.keys()))
    signature_string += API_SECRET
    m = hashlib.md5()
    m.update(signature_string.encode('utf-8'))
    signature = m.hexdigest()
    del hashlib
    gc.collect()
    # Add the signature to the parameters
    params["api_sig"] = signature
    params["format"] = "json"

    # Make the POST request
    for _ in range(3):  # Try up to three times
        print(f"trying request, attempt {_+1}. Free memory:", gc.mem_free())

        try:
            response = req.post(url, data=params)
            break  # If the request was successful, break out of the loop
        except MemoryError:
            print("MemoryError encountered. Waiting before retrying...")
            gc.collect()
            time.sleep(10)  # Wait for 10 seconds before retrying
    else:
        print("Failed to scrobble track after three attempts.")
        return

    # Check the response
    if response.status_code == 200:
        print("Scrobbled successfully!", response.text)
    else:
        print("Error scrobbling:", response.text)

    response.close()  # Close the response
    
    del response, req, pool, m, signature, params, signature_string

    
    
    gc.collect()  # Run garbage collection
    print("Finished scrobbling track. Free memory:", gc.mem_free())

def love_track():
    pool = socketpool.SocketPool(wifi.radio)
    req = requests.Session(pool, ssl.create_default_context())
    print("starting love track function. Free memory:", gc.mem_free())

    # Setup the parameters
    params = {
        "method": "track.love",
        "track": last_song,
        "artist": last_artist,
        "api_key": API_KEY,
        "sk": SESSION_KEY,
    }

    import adafruit_hashlib as hashlib

    # Sort the parameters and compute the signature
    sorted_params = sorted(params.items())
    param_string = "".join(f"{k}{v}" for k, v in sorted_params)
    param_string += API_SECRET
    api_sig = hashlib.md5(param_string.encode()).hexdigest()

    # Add the signature to the parameters
    params["api_sig"] = api_sig
    del hashlib
    # Make the POST request
    url = "http://ws.audioscrobbler.com/2.0/"
  
   # Make the POST request
    for _ in range(3):  # Try up to three times
        print(f"trying love request, attempt {_+1}. Free memory:", gc.mem_free())

        try:
            response = req.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=params)
            break  # If the request was successful, break out of the loop
        except MemoryError:
            print("MemoryError encountered. Waiting before retrying...")
            gc.collect()
            time.sleep(10)  # Wait for 10 seconds before retrying
    else:
        print("Failed to love track after three attempts.")
        return

    # Check the response
    if response.status_code == 200:
        print("Loved track successfully!", response.text)
    else:
        print("Error loving track:", response.text)

    response.close()  # Close the response
    
    del response, req, pool, params

    
    gc.collect()  # Run garbage collection
    print("Finished loving track. Free memory:", gc.mem_free())
    update_display(f"{last_song} \nby \n{last_artist}\nLoved ")
    time.sleep(3)


def get_current_kxlu_song(buffer=buffer): #checks for KXLU player
    # global buffer
    pool = socketpool.SocketPool(wifi.radio)
    req = requests.Session(pool, ssl.create_default_context())
    url = "https://spinitron.com/KXLU/"

    # Make the GET request
    response = req.get(url)

    # Process the response in chunks  
    
    for chunk in response.iter_content(chunk_size=256):  # Reduced chunk size
        chunk = chunk.decode('utf-8')
        buffer+=chunk
        if '<div class="spin-icons">' in buffer:
            break
        # Keep the buffer size manageable
        buffer = buffer[-2048:]  # Keep the buffer size in line with the chunk size
        gc.collect()
        print("Chunking. Free memory:", gc.mem_free())

    response.close()  # Close the response

    # Extract the artist and song title
    start_artist = buffer.find('<td class="spin-text"><div class="spin"><span class="artist">') + len('<td class="spin-text"><div class="spin"><span class="artist">')
    end_artist = buffer.find('</span>', start_artist)
    artist = buffer[start_artist:end_artist]
    buffer = buffer[end_artist:]
    start_song = buffer.find('<span class="song">') + len('<span class="song">')
    end_song = buffer.find('</span>', start_song)
    song = buffer[start_song:end_song]
    
    del response, req, pool

    gc.collect()  # Run garbage collection
    return artist, song

def get_current_gush_song(): #checks for Gush plays
    pool = socketpool.SocketPool(wifi.radio)
    req = requests.Session(pool, ssl.create_default_context())
    response = req.get("http://XX.X.X.XX:8000") # Enter your local IP address
    data = response.json()
    artist = data.get("artist")
    song = data.get("song")
    response.close()
    return artist, song

def update_display(theText):
    print('updating display')
    import displayio
    import adafruit_ssd1680
    import busio
    import terminalio
    from adafruit_display_text import label


    displayio.release_displays()

    spi = busio.SPI(clock=board.GP14, MOSI=board.GP11, MISO=board.GP12)
    epd_cs = board.GP9
    epd_dc = board.GP10
    epd_reset = None
    epd_busy = None

    display_bus = displayio.FourWire(
        spi, command=epd_dc, chip_select=epd_cs, reset=epd_reset, baudrate=1000000
    )
    time.sleep(1)

    display = adafruit_ssd1680.SSD1680(
        bus=display_bus,
        width=250,
        height=122,
        rotation=270,
        colstart=10,
    )

    g = displayio.Group()

    # Set the background color of the group
    background_color = displayio.Bitmap(display.width, display.height, 1)
    bg_palette = displayio.Palette(1)
    bg_palette[0] = 0xFFFFFF  # White
    bg_sprite = displayio.TileGrid(background_color, pixel_shader=bg_palette, x=0, y=0)
    g.append(bg_sprite)

    # Create a text label with inverted color
    text_area = label.Label(terminalio.FONT, text=theText, color=0x0000, scale=2)  # Inverted color
    text_area.x = 0
    text_area.y = 16

    g.append(text_area)

    display.show(g)
    display.refresh()
    spi.deinit()
    del epd_cs    
    del epd_dc
    print("Update Display has run")
    time.sleep(3)

#update_display("Scrobble Box initialized\nPreparing to scrobble")

# Last.fm API credentials
API_KEY = 'YOUR API KEY HERE'
API_SECRET = 'YOUR API SECRET HERE'
SESSION_KEY = 'YOUR SESSION KEY HERE'

setup_wifi()
print("Finished setting up WiFi. Free memory:", gc.mem_free())
gc.collect()
print("Ran garbage collection after setting up WiFi.", gc.mem_free())

get_current_time()
print("Finished getting current time. Free memory:", gc.mem_free())
gc.collect()
print("Ran garbage collection after getting current time. Free memory:", gc.mem_free())
try:
   # Read the first 4 bytes from NVM to get the length of the stored data
    length_str = microcontroller.nvm[0:4].decode('utf-8')
    data_length = int(length_str)

    # Read the stored data from NVM using the length
    read_bytes = microcontroller.nvm[4:4+data_length]

    # Convert read bytes back to string
    read_string = read_bytes.decode('utf-8')

    # Split the string into artist and song using newline as a delimiter
    lines = read_string.split('\n')

    # Assuming the first line is artist and the second line is song
    last_artist = lines[0]
    last_song = lines[1]

    print(f"Last Artist: {last_artist}")
    print(f"Last Song: {last_song}")
except:
    last_artist = None
    last_song = None
wasOff=False
scrobbled=False
while True:
    #if wasOff:
       # microcontroller.reset()
    # KXLU switch reads False when flipped "On", True when flipped "Off"
    if not switch.value or not switch2.value:  # Check if either switch is on
        print("if not switch value")
        if microcontroller.cpu.reset_reason != microcontroller.ResetReason.RESET_PIN:
            print("Starting a new iteration of the main loop. Free memory:", gc.mem_free())
           # The current song is obtained based on the switch that is active. 
            # If both are active, it defaults to the KXLU switch.
            if not switch.value:
                artist, song = get_current_kxlu_song()
            else:
                artist, song = get_current_gush_song()
            
            gc.collect()
            print("Finished getting current song. Free memory:", gc.mem_free())

            # If the artist or song has changed, print the new track information and scrobble it
            if artist != last_artist or song != last_song:
                print('Artist:', artist)
                print('Song:', song)
                scrobble_track(artist, song, int(time.time()))
                scrobbled=True
                print("Finished scrobbling track. Free memory:", gc.mem_free())
                gc.collect()
                print("Ran garbage collection after scrobbling track.")
           
            # Update last artist and song to the current ones for the next iteration
            last_artist = artist
            last_song = song
       
       
            gc.collect()
            print("Finished an iteration of the main loop.", gc.mem_free())
            break
            # Wait for 60 seconds
           # time.sleep(60)
            #microcontroller.reset()
        else: # Reset pin triggered a reset
            print('Loving last track bercause of restart reason:', microcontroller.cpu.reset_reason)
            love_track()
            microcontroller.reset()
    else: # Both switches are off
        # Your code for when the switch is off
        wasOff = True
        update_display("Not scrobbling")
        print("Not scrobbling")
        import alarm
        switch.deinit()
        switch2.deinit()
        pinAlarm = alarm.pin.PinAlarm(pin=board.GP2, value=False, pull=True)
        alarm.exit_and_deep_sleep_until_alarms(pinAlarm)
time.sleep(1)
print("reset reason:", microcontroller.cpu.reset_reason)
import alarm

print('alarm reason:', alarm.wake_alarm)
if isinstance(alarm.wake_alarm, alarm.time.TimeAlarm):
    print('detected time alarm!')
if not isinstance(alarm.wake_alarm,  alarm.time.TimeAlarm) and not scrobbled:
    update_display(f"{last_song} \nby \n{last_artist}\nScrobbled & Loved")
else:
    update_display(f"{song} \nby \n{artist}\nScrobbled")

    # String to store in NVM
    previousTrack = f"{artist}\n{song}\n"

    # Convert string to bytes
    previousTrackBytes = previousTrack.encode('utf-8')

    # Check if data + 4 bytes for the length is larger than 4KB
    if len(previousTrackBytes) + 4 > 4096:
        print("Data exceeds 4KB, it will be truncated.")
        previousTrackBytes = previousTrackBytes[:4092]  # Leave 4 bytes for the length

    # Write length of data to the first 4 bytes of NVM
    length_str = "{:04}".format(len(previousTrackBytes))  # Pad with zeros to ensure 4 bytes
    microcontroller.nvm[0:4] = bytes(length_str, 'utf-8')

    # Write bytes to NVM starting from the 5th byte
    microcontroller.nvm[4:4+len(previousTrackBytes)] = previousTrackBytes



import alarm
timeAlarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic()+60)
alarm.exit_and_deep_sleep_until_alarms(timeAlarm)
