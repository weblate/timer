import subprocess
import json
# Czech
if subprocess.getoutput("locale") == 'LANG=cs_CZ.UTF-8\nLC_CTYPE="cs_CZ.UTF-8"\nLC_NUMERIC="cs_CZ.UTF-8"\nLC_TIME="cs_CZ.UTF-8"\nLC_COLLATE="cs_CZ.UTF-8"\nLC_MONETARY="cs_CZ.UTF-8"\nLC_MESSAGES="cs_CZ.UTF-8"\nLC_PAPER="cs_CZ.UTF-8"\nLC_NAME="cs_CZ.UTF-8"\nLC_ADDRESS="cs_CZ.UTF-8"\nLC_TELEPHONE="cs_CZ.UTF-8"\nLC_MEASUREMENT="cs_CZ.UTF-8"\nLC_IDENTIFICATION="cs_CZ.UTF-8"\nLC_ALL=':
    with open('translations/cs.json') as t:
        jT = json.load(t)
# Italian
elif subprocess.getoutput("locale") == 'LANG=it_IT.UTF-8\nLC_CTYPE="it_IT.UTF-8"\nLC_NUMERIC="it_IT.UTF-8"\nLC_TIME="it_IT.UTF-8"\nLC_COLLATE="it_IT.UTF-8"\nLC_MONETARY="it_IT.UTF-8"\nLC_MESSAGES="it_IT.UTF-8"\nLC_PAPER="it_IT.UTF-8"\nLC_NAME="it_IT.UTF-8"\nLC_ADDRESS="it_IT.UTF-8"\nLC_TELEPHONE="it_IT.UTF-8"\nLC_MEASUREMENT="it_IT.UTF-8"\nLC_IDENTIFICATION="it_IT.UTF-8"\nLC_ALL=':
    with open('translations/it.json') as t:
        jT = json.load(t)
# Deutsch
elif subprocess.getoutput("locale") == 'LANG=de_DE.UTF-8\nLC_CTYPE="de_DE.UTF-8"\nLC_NUMERIC="de_DE.UTF-8"\nLC_TIME="de_DE.UTF-8"\nLC_COLLATE="de_DE.UTF-8"\nLC_MONETARY="de_DE.UTF-8"\nLC_MESSAGES="de_DE.UTF-8"\nLC_PAPER="de_DE.UTF-8"\nLC_NAME="de_DE.UTF-8"\nLC_ADDRESS="de_DE.UTF-8"\nLC_TELEPHONE="de_DE.UTF-8"\nLC_MEASUREMENT="de_DE.UTF-8"\nLC_IDENTIFICATION="de_DE.UTF-8"\nLC_ALL=':
    with open('translations/de.json') as t:
        jT = json.load(t)
# Russian
elif subprocess.getoutput("locale") == 'LANG=ru_RU.UTF-8\nLC_CTYPE="ru_RU.UTF-8"\nLC_NUMERIC="ru_RU.UTF-8"\nLC_TIME="ru_RU.UTF-8"\nLC_COLLATE="ru_RU.UTF-8"\nLC_MONETARY="ru_RU.UTF-8"\nLC_MESSAGES="ru_RU.UTF-8"\nLC_PAPER="ru_RU.UTF-8"\nLC_NAME="ru_RU.UTF-8"\nLC_ADDRESS="ru_RU.UTF-8"\nLC_TELEPHONE="ru_RU.UTF-8"\nLC_MEASUREMENT="ru_RU.UTF-8"\nLC_IDENTIFICATION="ru_RU.UTF-8"\nLC_ALL=':
    with open('translations/ru.json') as t:
        jT = json.load(t)
# Finnish
elif subprocess.getoutput("locale") == 'LANG=fi_FI.UTF-8\nLC_CTYPE="fi_FI.UTF-8"\nLC_NUMERIC="fi_FI.UTF-8"\nLC_TIME="fi_FI.UTF-8"\nLC_COLLATE="fi_FI.UTF-8"\nLC_MONETARY="fi_FI.UTF-8"\nLC_MESSAGES="fi_FI.UTF-8"\nLC_PAPER="fi_FI.UTF-8"\nLC_NAME="fi_FI.UTF-8"\nLC_ADDRESS="fi_FI.UTF-8"\nLC_TELEPHONE="fi_FI.UTF-8"\nLC_MEASUREMENT="fi_FI.UTF-8"\nLC_IDENTIFICATION="fi_FI.UTF-8"\nLC_ALL=':
    with open('translations/fi.json') as t:
        jT = json.load(t)

# French
elif subprocess.getoutput("locale") == 'LANG=fr_FR.UTF-8\nLC_CTYPE="fr_FR.UTF-8"\nLC_NUMERIC="fr_FR.UTF-8"\nLC_TIME="fr_FR.UTF-8"\nLC_COLLATE="fr_FR.UTF-8"\nLC_MONETARY="fr_FR.UTF-8"\nLC_MESSAGES="fr_FR.UTF-8"\nLC_PAPER="fr_FR.UTF-8"\nLC_NAME="fr_FR.UTF-8"\nLC_ADDRESS="fr_FR.UTF-8"\nLC_TELEPHONE="fr_FR.UTF-8"\nLC_MEASUREMENT="fr_FR.UTF-8"\nLC_IDENTIFICATION="fr_FR.UTF-8"\nLC_ALL=':
    with open('translations/fr.json') as t:
        jT = json.load(t)

# Norway
elif subprocess.getoutput("locale") == 'LANG=nb_NO.UTF-8\nLC_CTYPE="nb_NO.UTF-8"\nLC_NUMERIC="nb_NO.UTF-8"\nLC_TIME="nb_NO.UTF-8"\nLC_COLLATE="nb_NO.UTF-8"\nLC_MONETARY="nb_NO.UTF-8"\nLC_MESSAGES="nb_NO.UTF-8"\nLC_PAPER="nb_NO.UTF-8"\nLC_NAME="nb_NO.UTF-8"\nLC_ADDRESS="nb_NO.UTF-8"\nLC_TELEPHONE="nb_NO.UTF-8"\nLC_MEASUREMENT="nb_NO.UTF-8"\nLC_IDENTIFICATION="nb_NO.UTF-8"\nLC_ALL=':
    with open('translations/nb_NO.json') as t:
        jT = json.load(t)

# English
else:
    with open('translations/en.json') as t:
        jT = json.load(t)

# Variables
timer_title = jT["timer_title"]
timer_running = jT["timer_running"]
run_timer = jT["run_timer"]
stop_timer = jT["stop_timer"]
timing_finished = jT["timing_finished"]
timing_ended = jT["timing_ended"]
timer_quit = jT["timer_quit"]
about_app = jT["about_app"]
simple_timer = jT["simple_timer"]
preferences = jT["preferences"]
close = jT["close"]
spinner = jT["spinner"]
spinner_size_desc = jT["spinner_size_desc"]
select = jT["select"]
resizable_of_window = jT["resizable_of_window"]
default = jT["default"]
preferences_saved = jT["preferences_saved"]
theme_desc = jT["theme_desc"]
dark_theme = jT["dark_theme"]
contributors = jT["contributors"]
hours = jT["hours"]
mins = jT["mins"]
secs = jT["secs"]
shut_down = jT["shut_down"]
reboot = jT["reboot"]
action_after_timing = jT["action_after_timing"]
blank_value = jT["blank_value"]
blank_values_desc = jT["blank_values_desc"]
custom_notification = jT["custom_notification"]
mute_volume = jT["mute_volume"]
play_beep = jT["play_beep"]
suspend = jT["suspend"]
translator_credits = jT["translator_credits"]
import src.main
