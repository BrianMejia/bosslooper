import os
import sys
import csv
import time
import pygame
import keyboard
from pydub import AudioSegment

songStructure = []
transitionQueue = []
musicQueue = []
songLoaded = False

# smaller buffer for less latency
pygame.mixer.pre_init(frequency=44100, buffer=512)
pygame.mixer.init()
pygame.init()

# thank you https://stackoverflow.com/a/18869461
class Fader(object):
    def __init__(self, fname):
        super(Fader, self).__init__()
        assert isinstance(fname, str)
        self.name = fname
        self.increment = 0.01 # speed of fade effect
        self.next_vol = 1 # 100% volume on start

    def fade_to(self, new_vol):
        # sets the threshold when updating
        self.next_vol = new_vol

# Fader subclass for main music portions
class MusicFader(Fader):
    def __init__(self, fname):
        super(MusicFader, self).__init__(fname)
        self.music = pygame.mixer.music
        self.music.load(fname)

    def set_volume(self, num):
        self.fade_to(num)
        self.music.set_volume(num)

    def update(self):
        curr_volume = self.music.get_volume()
        if self.next_vol > curr_volume: # fade out
            self.music.set_volume(curr_volume + self.increment)
        elif self.next_vol < curr_volume: # fade in
            self.music.set_volume(curr_volume - self.increment)
        pygame.time.delay(10) # give some time, else effect is instantaneous

# Fader subclass for transition portions
class ChannelFader(Fader):
    def __init__(self, fname):
        super(ChannelFader, self).__init__(fname)
        self.channel = pygame.mixer.Channel(0) # one channel initially, may be expanded later
        self.sound = pygame.mixer.Sound(self.name) # loads sound that will be placed into self.channel

    def set_volume(self, num):
        self.fade_to(num)
        self.channel.set_volume(num)

    def update(self):
        curr_volume = self.channel.get_volume()
        if self.next_vol > curr_volume:
            self.channel.set_volume(curr_volume + self.increment)
        elif self.next_vol < curr_volume:
            self.channel.set_volume(curr_volume - self.increment)
        pygame.time.delay(10)

def clear_screen(): # for updating the screen with new text/menus
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')

def getMilliSec(s): # returns milliseconds when given MM:SS.SSS format
    l = list(map(float, s.split(':')))
    return sum(n * msec for n, msec in zip(l[::-1], (1000, 60000))) # 1s=1000ms, 1m=60000ms

def progbar(curr, total, full_progbar): # [=====     ] [ 50.0%] [5/10] - example progbar(5, 10, 10)
    frac = curr/total
    filled_progbar = round(frac*full_progbar)
    print('[' + '='*filled_progbar + ' '*(full_progbar-filled_progbar) + ']', '[{:>7.2%}]'.format(frac), '[' + str(int(curr)) + '/' + str(int(total)) + ']', end='\r')

def print_line():
    print('=' * 80)

def print_heading(headerText): # dependent on menu
    print_line()
    print(headerText)
    print_line()
    print()

def get_menu_choice(musicLoaded):
    while True: # if given invalid option, redraws this menu
        print("Options:\n")
        print(".: Load Music (ogg/csv) [l]")
        if musicLoaded:
            print(".: Start Music [s]")
        print(".: Quit [q]")
        print()
        choice = input("Enter Option: ").lower().strip()

        if choice == 'l' or choice == 'q' or (musicLoaded and choice == 's'):
            return choice

        clear_screen()
        print_heading("Boss Looper - Main Menu")

def perform_action(action):
    if action == 'l':
        perform_load() # for loading music (.ogg) from a file (.csv)
    elif action == 's':
        perform_start() # for playing music that has been loaded
    elif action == 'q':
        return True # quits program

def perform_load(): # loads music segments from user's .csv file
    global musicQueue
    global transitionQueue
    global songStructure
    global songLoaded # for opening up option in main menu

    musicQueue = []
    transitionQueue = []
    songStructure = []

    clear_screen()
    print_heading("Boss Looper - Load Menu")

    inputSong = str(input("Input file name of song: "))
    try:
        song = AudioSegment.from_ogg(inputSong)
        songName = inputSong.strip().split('.')[0] # for creating folder
        if not os.path.exists(songName):
            os.makedirs(songName)
    except FileNotFoundError:
        raise FileNotFoundError("Cannot open '" + inputSong + "'.")

    inputParts = str(input("Input file name of loop portions: "))
    try:
        inputFile = open(inputParts, 'r')
        numLines = sum(1 for line in open(inputParts))
    except IOError:
        raise IOError("Cannot open '" + inputParts + "'.")

    print("\nFile Search successful. Importing...")
    lineNum = 1
    for line in inputFile:
        progbar(lineNum, numLines, 30)

        line = line.strip().split(',')
        if len(line) != 4:
            raise ValueError("Invalid number of fields for loops. Expected 4, received %d on line %d." %(len(line), lineNum))

        partFile = songName + "/p" + str(lineNum) + ".ogg"
        milliStart = getMilliSec(line[0])
        milliEnd = getMilliSec(line[1])
        tempSong = song[milliStart:milliEnd] # thanks to Pydub, simple song splitting

        tempSong.export(partFile, format="ogg") # places in own song directory
        if (int(line[2])): # from .csv file, 1 - Music portion, 0 - Transition portion
            musicQueue.append(partFile)
        else:
            transitionQueue.append(partFile)
        songStructure.append(line[3])

        lineNum += 1

    inputFile.close()
    songLoaded = True
    print("\nLoad Complete.")

def perform_start():
    def reset_screen(isLoop):
        clear_screen()
        print_heading("Boss Looper - Music Menu")
        if isLoop:
            print(".: Switch to Next Transition Phase [Alt+Shift+S]")
        print(".: Quit [Alt+Shift+Q]\n")
        print("Phase:" + songStructure[songPhase])

    # globals for reloading music
    global musicQueue
    global transitionQueue
    global songStructure

    musicPhase = 0
    transitionPhase = 0
    songPhase = 0

    transitionMix = ChannelFader(transitionQueue[transitionPhase])
    musicMix = MusicFader(musicQueue[musicPhase])
    phaseText = songStructure[songPhase]

    # clock for keeping track of how long a transition goes on for
    elapsed = time.time()
    length = transitionMix.sound.get_length()

    transitionMix.channel.play(transitionMix.sound)

    # not looping, need transition times
    reset_screen(False)

    while True:
        while transitionMix.channel.get_busy(): # transition is playing
            progbar(time.time() - elapsed, length, 50) # display remaining time on transition

            if keyboard.is_pressed('alt+shift+q'): # quit to menu
                musicMix.music.stop()
                transitionMix.channel.stop()
                transitionMix.sound.stop()
                return

        # transition has ended, check to see if it is last phase
        if songPhase == len(songStructure) - 1:
            musicMix.music.stop()
            transitionMix.sound.stop()
            transitionMix.channel.stop()
            return

        # begin playing next music phase
        musicMix.music.play(-1)
        transitionMix.fade_to(0)

        # advance transition and song phases, make sure phases don't go past alloted size
        transitionPhase = min(transitionPhase + 1, len(transitionQueue) - 1)
        songPhase = min(songPhase + 1, len(songStructure) - 1)
        transitionMix.sound = pygame.mixer.Sound(transitionQueue[transitionPhase])
        length = transitionMix.sound.get_length()

        # looping, need additional option
        reset_screen(True)

        while musicMix.music.get_busy(): # music is playing
            transitionMix.update() # if transition has not faded out, do so

            if keyboard.is_pressed('alt+shift+s'): # move to next transition phase
                musicMix.fade_to(0) # start to fade out music
                transitionMix.channel.play(transitionMix.sound) # play transition simultaneously
                transitionMix.fade_to(1)

                elapsed = time.time() # for progbar while fading
                musicPhase = min(musicPhase + 1, len(musicQueue) - 1)
                songPhase = min(songPhase + 1, len(songStructure) - 1)
                reset_screen(False)

                while transitionMix.channel.get_volume() < 1:
                    progbar(time.time() - elapsed, length, 50)
                    musicMix.update()
                    transitionMix.update()

                musicMix.music.stop()
                musicMix.music.load(musicQueue[musicPhase]) # load next phase while transition is playing
                musicMix.set_volume(1) # set back to full volume for when transition ends

            if keyboard.is_pressed('alt+shift+q'): # quit to menu
                musicMix.music.stop()
                transitionMix.channel.stop()
                transitionMix.sound.stop()
                return

def main(): # the main menu
    try:
        global songLoaded
        while True:
            clear_screen()
            print_heading("Boss Looper - Main Menu")

            choice = get_menu_choice(songLoaded)

            if perform_action(choice): # quit program
                pygame.quit()
                sys.stdout.flush()
                break
    except KeyboardInterrupt:
        print("\nBoss Looper has been shut down forcibly.")

if __name__ == '__main__':
    main()
