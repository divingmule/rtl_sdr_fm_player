import configparser
import os


config = configparser.ConfigParser()

if os.path.exists('settings.ini'):
    config.read('settings.ini')
# settings.ini will be created from example-settings.ini
else:
    config.read('example-settings.ini')

Server = config.getboolean('rtl_fm_streamer', 'rtl_fm_streamer')
start_server = config.getboolean('rtl_fm_streamer', 'start server')
if Server:
    host = config.get('rtl_fm_streamer', 'ip address')
    port = config.get('rtl_fm_streamer', 'server port')
    api_port = config.get('rtl_fm_streamer', 'server api port')
    play_string = ('%s http://%s:%s/freq/%s' %
                   (config.get('rtl_fm_streamer', 'player command'),
                    host, port, config.get('rtl_fm_streamer', 'stereo')))
else:
    play_string = (' %s | %s' % (config.get('rtl_fm', 'rtl_fm command'),
                                 config.get('rtl_fm', 'player command')))


stations = dict({i: config['Stations'][i] for i in config['Stations']})
frequencies = list(stations.keys())

background_color = config.get('GUI', 'background color')
font_color = config.get('GUI', 'text color')
border_color = config.get('GUI', 'button border')
button_color = config.get('GUI', 'button color')
if button_color == 'black':
    icon_path = 'icons/black_icons/'
else:
    icon_path = 'icons/white_icons/'


def add_station(freq):
    config['Stations'][freq] = ''
    write_config()


def remove_station(freq):
    config.remove_option('Stations', freq)
    write_config()


def write_config():
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)


# I'm going somewhere with this, I think*
def set_preset(button, freq):
    pass
