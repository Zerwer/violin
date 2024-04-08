from music21 import *
from music21.note import Rest, Note
import os
from PIL import Image
from util import ScoreSave, MeasureClip, save_as_png, extract_part

MINIMUM_MEASURE_SPAN = 1

def parse_first_measure(first_measure):
    new_measure = stream.Measure()
    k = None
    for obj in first_measure:
        if isinstance(obj, (clef.TrebleClef, key.KeySignature, meter.TimeSignature, note.Rest, note.Note)):
            new_measure.append(obj)
            if isinstance(obj, key.KeySignature):
                k = obj
    
    # new_measure.showNumber = False TODO

    return new_measure, k

if __name__ == "__main__":
    name = 'Storm'
    bpm = 120
    # start_width = 250
    start_width = 150
    imgs = []
    my_score = converter.parse('storms.mxl')

    violin_part = extract_part(my_score, 'Violin')

    measures = violin_part.getElementsByClass(stream.Measure)

    new_measure, k = parse_first_measure(measures[0])
                
    i = 0
    save_as_png(new_measure, f'clip.png')
    img = Image.open('clip-1.png')
    left_half = img.crop((0, 0, start_width, img.height))
    right_half = img.crop((start_width, 0, img.width, img.height))
    
    img1_bytes = left_half.tobytes("raw", 'RGBA')
    img2_bytes = right_half.tobytes("raw", 'RGBA')
    imgs.append(MeasureClip(img1_bytes, left_half.size, 1))
    imgs.append(MeasureClip(img2_bytes, right_half.size, 1))

    img.close()
    os.remove('clip-1.png')
    i += 1
    
    span = []
    isSpanning = False
    isTied = False
    for measure in measures[1:]:
        filtered = stream.Measure()

        m_spanners = measure.getSpannerSites()
        filtered.append(m_spanners)

        for obj in measure:
            if isinstance(obj, (Note, Rest)):
                filtered.append(obj)

        for note in measure.flatten().notesAndRests:
            spanners = note.getSpannerSites()
            
            if note.tie:
                isTied = not isTied
            if spanners:
                if not isSpanning:
                    filtered.append(spanners)
                isSpanning = not isSpanning

        span.append(filtered)
        
        if not isSpanning and not isTied and len(span) >= MINIMUM_MEASURE_SPAN:
            s = stream.Stream()
            s.insert(0, k)
            s.append(span)
            save_as_png(s, f'clip.png')
            img = Image.open('clip-1.png')
            img = img.crop((start_width - 50, 0, img.width, img.height))
            
            img_bytes = img.tobytes("raw", 'RGBA')
            imgs.append(MeasureClip(img_bytes, img.size, len(span)))
            # img.save(f'clip{i}.png')

            img.close()
            os.remove('clip-1.png')

            span = []
            i += 1

    score = ScoreSave(name, bpm, my_score, imgs)
    score.save()
