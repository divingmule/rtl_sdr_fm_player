from tkinter import *
import subprocess
import time
import threading
import keyboard
import configparser
from functools import partial
import socket
import json


Stop = True
Muted = False
Server = False
Tuning = 'stopped'
CPU = 0

config = configparser.ConfigParser()
config.read('settings.ini')

host = config['Server']['ip address']
port = config['Server']['server port']
api_port = config['Server']['server api port']

stations = dict({i: config['Stations'][i] for i in config['Stations']})
frequencies = list(stations.keys())
frequencies.sort()
FREQ = frequencies[0]

background_color = config['GUI']['background color']
font_color = config['GUI']['text color']
button_color = config['GUI']['button color']
if button_color == 'black':
    icon_path = 'icons/black_icons/'
else:
    icon_path = 'icons/white_icons/'

play_string = ('rtl_fm -f %sM -M fm -s 170k -A std -l 0 -E deemp -r 44.1k | '
               'ffplay -nodisp -f s16le -ac 1 -i pipe:0')

if config['Server']['rtl_fm_streamer'] == 'true':
    Server = True
    play_string = ('ffplay -nodisp http://%s:%s/freq/%s' %
                   (host, port, config['Server']['stereo']))
    if config['Server']['start server'] == 'true':
        subprocess.Popen(['rtl_fm_streamer', '-P', port])


def make_request(payload):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, int(api_port)))
        s.sendall(json.dumps(payload).encode('utf-8'))
        data = s.recv(1024)
        print('Received', str(json.loads(data)))


def set_frequency(frequency):
    freq = int(float(frequency) * 1000000)
    print('setting frequency to %s' % freq)
    payload = {"method": "SetFrequency", "params": [freq]}
    make_request(payload)


def get_power_level():
    payload = {"method": "GetPowerLevel"}
    make_request(payload)


# credit https://rosettacode.org/wiki/Linux_CPU_utilization
def get_cpu_utilisation():
    global CPU
    last_idle = last_total = 0
    while True:
        with open('/proc/stat') as f:
            fields = [float(column) for column in f.readline().strip().split()[1:]]
        idle, total = fields[3], sum(fields)
        idle_delta, total_delta = idle - last_idle, total - last_total
        last_idle, last_total = idle, total
        utilisation = 100.0 * (1.0 - idle_delta / total_delta)
        print('%5.1f%%' % utilisation, end='\r')
        CPU = ('%5.1f%%' % utilisation)
        time.sleep(2)


def get_cpu_info():
    get_temp = subprocess.check_output(["vcgencmd", "measure_temp"])
    temp = get_temp.decode('utf-8').lstrip('temp=')
    cpu_text.config(text='CPU %s %s' % (temp, CPU))
    cpu_text.after(2000, get_cpu_info)


def play(p_string):
    print('Play String  %s' % p_string)
    global Stop
    p = subprocess.Popen(p_string, shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    while not Stop:
        time.sleep(.2)
    else:
        print('STOP: %s' % Stop)
        p.terminate()
        if Server:
            subprocess.run(['killall', 'ffplay'])
        else:
            subprocess.run(['killall', '-s', 'SEGV', 'rtl_fm'])


def start(freq):
    global Stop
    if Stop:
        print('starting play_thread')
        if Server:
            freq = int(float(freq) * 1000000)
            p_string = play_string.replace('/freq/', '/%s/' % freq)
        else:
            p_string = play_string % freq
        play_thread = threading.Thread(target=play, args=([p_string]))
        play_thread.start()
        print(p_string)
        Stop = False
    else:
        print('stopping play_thread')
        Stop = True


def stop():
    global Stop
    Stop = True


def mute():
    global Muted
    if Muted:
        Muted = False
    else:
        Muted = True
    keyboard.send('f13')


def vol_up():
    keyboard.send('help')


def vol_down():
    keyboard.send('f14')


def next_station():
    if not Server:
        stop()
    global FREQ
    if FREQ in frequencies:
        current_frequency = frequencies.index(FREQ)
        if frequencies[current_frequency] == frequencies[-1]:
            FREQ = frequencies[0]
        else:
            FREQ = frequencies[current_frequency + 1]
    else:
        freq_list = [i for i in frequencies if i > FREQ]
        if freq_list:
            FREQ = freq_list[0]
        else:
            FREQ = frequencies[0]
    if Server:
        set_frequency(FREQ)
    else:
        time.sleep(1)
        start(FREQ)


def previous_station():
    if not Server:
        stop()
    global FREQ
    if FREQ in frequencies:
        current_frequency = frequencies.index(FREQ)
        if frequencies[current_frequency] == frequencies[0]:
            FREQ = frequencies[-1]
        else:
            FREQ = frequencies[current_frequency - 1]
    else:
        freq_list = [i for i in frequencies if i < FREQ]
        if freq_list:
            FREQ = freq_list[0]
        else:
            FREQ = frequencies[-1]
    if Server:
        set_frequency(FREQ)
    else:
        time.sleep(1)
        start(FREQ)


def preset_station(freq):
    if freq == 'Preset':
        return
    if not Server:
        stop()
    global FREQ
    FREQ = freq
    if Server:
        set_frequency(FREQ)
    else:
        time.sleep(1)
        start(FREQ)


def tune_up():
    global FREQ
    global Tuning
    if not Server:
        if not Stop:
            stop()
    if Tuning != 'started':
        Tuning = 'started'
    FREQ = str(round((float(FREQ) + 0.1), 1))
    print('Tune up %s' % FREQ)


def tune_down():
    global FREQ
    global Tuning
    if not Server:
        if not Stop:
            stop()
    if Tuning != 'started':
        Tuning = 'started'
    FREQ = str(round((float(FREQ) - 0.1), 1))
    print('Tune down %s' % FREQ)


def tuning_stop(event):
    global Tuning
    Tuning = 'finished'


def tune():
    global Tuning
    if Tuning == 'finished':
        if Server:
            set_frequency(FREQ)
        else:
            start(FREQ)
        Tuning = 'stopped'
        print('Tuning to %s' % FREQ)
    master.after(200, tune)


def power_off():
    stop()
    time.sleep(1)
    if Server:
        subprocess.run(['killall', 'rtl_fm_streamer'])
    master.destroy()


def tick():
    time_string = ''
    time_now = time.strftime('%I:%M %p')
    if time_now != time_string:
        clock.config(text=time_now.lstrip('0'))
    clock.after(200, tick)


def update_freq_label():
    freq_text.config(text=FREQ)
    freq_text.after(100, update_freq_label)


def update_station():
    if FREQ in stations:
        station_text.config(text='%s' % stations[FREQ])
    else:
        station_text.config(text='%s' % FREQ)
    station_text.after(200, update_station)


def update_play_button():
    if Stop:
        button_img = play_image
    else:
        button_img = stop_image
    play_button.config(image=button_img)
    play_button.after(200, update_play_button)


def update_vol_button():
    if Muted:
        button_image = vol_mute_image
    else:
        button_image = vol_image
    vol_button.config(image=button_image)
    vol_button.after(200, update_vol_button)


# Start of GUI
master = Tk()

width = master.winfo_screenwidth()
height = master.winfo_screenheight()

if width > 800 or height > 480:
    master.geometry("800x480")
else:
    # assuming Rpi 7in touch screen @ 800x480
    # makes full screen window
    master.overrideredirect(1)
    master.geometry("%dx%d+0+0" % (width, height))

canvas = Canvas(master, width=800, height=480)
canvas.config(background=background_color)
canvas.pack()
background_image = PhotoImage(file='background.png')
canvas_back = canvas.create_image(400, 240, image=background_image)
title_text = canvas.create_text(150, 40, font=('Quicksand Medium', 16, 'bold', 'italic'),
                                fill=font_color, text='RTL-SDR FM Player')
station_text = Label(master, font=("Quicksand Medium", 38, 'bold'), fg=font_color, bg=background_color)
station_text.config(justify='left', wraplength=560, fg=font_color)
station_text.place(x=220, y=190)
freq_text = Label(master, font=("Quicksand Medium", 38, 'bold'), fg=font_color, bg=background_color)
freq_text.config(justify='left', fg=font_color, width=5, borderwidth=2, relief='sunken')
freq_text.place(x=300, y=100)
clock = Label(master, font=('Quicksand Medium', 32, 'bold'), bg=background_color, fg=font_color)
clock.place(x=480, y=20)
cpu_text = Label(master, font=('Quicksand Medium', 16, 'bold', 'italic'),
                 bg=background_color, fg=font_color)
cpu_text.place(relx=0.6, rely=0.65)

preset_x = 0.27
preset_y = 0.81
preset_list = frequencies[:5]
if frequencies.index(FREQ) > frequencies.index(frequencies[-2]):
    preset_list = frequencies[(frequencies.index(frequencies[-1]) - 4):]
    print(str(preset_list))
elif frequencies.index(FREQ) < frequencies.index(frequencies[1]):
    preset_list = frequencies[:(frequencies.index(frequencies[0]) + 5)]
    print(str(preset_list))
if len(preset_list) < 5:
    while len(preset_list) < 5:
        preset_list.append('Preset')
for i in preset_list:
    com = partial(preset_station, i)
    b_name = Button(master, command=com, text=i,
                    bg=background_color, activebackground=background_color, width=5)
    b_name.config(font=('Quicksand Medium', 16, 'bold', 'italic'), pady=12)
    b_name.place(relx=preset_x, rely=preset_y)
    preset_x += 0.12

# play button
play_image = PhotoImage(file='%splay.png' % icon_path)
stop_image = PhotoImage(file='%sstop-circle.png' % icon_path)
play_button = Button(master, command=lambda: start(FREQ),
                     bg=background_color, activebackground=background_color)
play_button.place(relx=0.05, rely=0.8)

# power button
power_image = PhotoImage(file='%spower.png' % icon_path)
power_button = Button(master, image=power_image, command=power_off,
                      bg=background_color, activebackground=background_color)
power_button.place(relx=0.87, rely=0.07)

# vol up button
vol_up_image = PhotoImage(file='%schevron-up.png' % icon_path)
vol_up = Button(master, image=vol_up_image, command=vol_up,
                bg=background_color, activebackground=background_color)
vol_up.place(relx=0.05, rely=0.2)

# vol mute button
vol_image = PhotoImage(file='%svolume-2.png' % icon_path)
vol_mute_image = PhotoImage(file='%svolume-x.png' % icon_path)
vol_button = Button(master, command=mute, bg=background_color,
                    activebackground=background_color)
vol_button.place(relx=0.05, rely=0.4)

# vol down button
vol_down_image = PhotoImage(file='%schevron-down.png' % icon_path)
vol_down = Button(master, image=vol_down_image, command=vol_down,
                  bg=background_color, activebackground=background_color)
vol_down.place(relx=0.05, rely=0.60)

# previous button
previous_image = PhotoImage(file='%schevron-left.png' % icon_path)
previous_button = Button(master, image=previous_image, command=previous_station,
                         bg=background_color, activebackground=background_color)
previous_button.place(relx=0.16, rely=0.8)

# next button
next_image = PhotoImage(file='%schevron-right.png' % icon_path)
next_button = Button(master, image=next_image, command=next_station,
                     bg=background_color, activebackground=background_color)
next_button.place(relx=0.87, rely=0.8)

# tune down button
tune_down_image = PhotoImage(file='%schevron-left.png' % icon_path)
tune_down_button = Button(master, image=tune_down_image, command=tune_down,
                          bg=background_color, activebackground=background_color)
tune_down_button.config(repeatdelay=100, repeatinterval=200)
tune_down_button.bind('<ButtonRelease>', tuning_stop)
tune_down_button.place(relx=0.25, rely=0.2)

# tune up button
tune_up_image = PhotoImage(file='%schevron-right.png' % icon_path)
tune_up_button = Button(master, image=tune_up_image, command=tune_up,
                        bg=background_color, activebackground=background_color)
tune_up_button.config(repeatdelay=100, repeatinterval=200)
tune_up_button.bind('<ButtonRelease>', tuning_stop)
tune_up_button.place(relx=0.61, rely=0.2)

cpu_thread = threading.Thread(target=get_cpu_utilisation)
cpu_thread.start()

tick()
tune()
update_freq_label()
update_station()
update_play_button()
update_vol_button()
get_cpu_info()
mainloop()
