from tkinter import *
import subprocess
import time
import threading
import keyboard
import configparser

Stop = True
Muted = False
Server = False

config = configparser.ConfigParser()
config.read('settings.ini')

stations = dict({i: config['Stations'][i] for i in config['Stations']})
frequencies = list(stations.keys())
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
                   (config['Server']['ip address'], config['Server']['port'],
                    config['Server']['stereo']))
    if config['Server']['start server'] == 'true':
        subprocess.Popen(['rtl_fm_streamer', '-P', config['Server']['server port']])


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
    stop()
    global FREQ
    current_frequency = frequencies.index(FREQ)
    if frequencies[current_frequency] == frequencies[-1]:
        FREQ = frequencies[0]
    else:
        FREQ = frequencies[current_frequency + 1]
    time.sleep(1)
    start(FREQ)


def previous_station():
    stop()
    global FREQ
    current_frequency = frequencies.index(FREQ)
    if frequencies[current_frequency] == frequencies[0]:
        FREQ = frequencies[-1]
    else:
        FREQ = frequencies[current_frequency - 1]
    time.sleep(1)
    start(FREQ)


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


def update_station():
    station_text.config(text='%s %s' % (FREQ, stations[FREQ]))
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
station_text.place(x=220, y=140)
clock = Label(master, font=('Quicksand Medium', 32, 'bold'), bg=background_color, fg=font_color)
clock.place(x=540, y=30)

# play button
play_image = PhotoImage(file='%splay.png' % icon_path)
stop_image = PhotoImage(file='%sstop-circle.png' % icon_path)
play_button = Button(master, command=lambda: start(FREQ),
                     bg=background_color, activebackground=background_color)
play_button.place(relx=0.45, rely=0.7)

# power button
power_image = PhotoImage(file='%spower.png' % icon_path)
power_button = Button(master, image=power_image, command=power_off,
                      bg=background_color, activebackground=background_color)
power_button.place(relx=0.82, rely=0.7)

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
vol_button.place(relx=0.05, rely=0.45)

# vol down button
vol_down_image = PhotoImage(file='%schevron-down.png' % icon_path)
vol_down = Button(master, image=vol_down_image, command=vol_down,
                  bg=background_color, activebackground=background_color)
vol_down.place(relx=0.05, rely=0.7)

# previous button
previous_image = PhotoImage(file='%schevron-left.png' % icon_path)
previous_button = Button(master, image=previous_image, command=previous_station,
                         bg=background_color, activebackground=background_color)
previous_button.place(relx=0.3, rely=0.7)

# next button
next_image = PhotoImage(file='%schevron-right.png' % icon_path)
next_button = Button(master, image=next_image, command=next_station,
                     bg=background_color, activebackground=background_color)
next_button.place(relx=0.6, rely=0.7)

tick()
update_station()
update_play_button()
update_vol_button()
mainloop()
