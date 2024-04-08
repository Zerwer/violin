from music21 import *
import pickle

def save_as_png(score, file_path):
    score.write('musicxml.png', fp=file_path)

def extract_part(score, instrument):
    for part in score.parts:
        if instrument in part.partName:
            return part
    return None

# Convert MIDI to frequency
def note_to_freq(note):
    a = 440
    return (a / 32) * (2 ** ((note - 9) / 12))

class MeasureClip:
    def __init__(self, img, size, count):
        self.img = img
        self.size = size
        self.count = count

class ScoreSave:
    def __init__(self, name, bpm, score, imgs):
        self.name = name
        self.score = score
        self.bpm = bpm
        self.imgs = imgs

    def save(self):
        with open(f'{self.name}.pkl', 'wb') as f:
            pickle.dump(self, f)

    def get_measures(self):
        violin_part = extract_part(self.score, 'Violin')
        return violin_part.getElementsByClass(stream.Measure)