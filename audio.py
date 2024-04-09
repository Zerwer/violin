from constants import *
from util import note_to_freq
import sys
import queue
import sounddevice as sd
import threading
import numpy as np
import math
from librosa import pyin

class AudioInput:
    def __init__(self, device):
        self.device = device

        self.stream = sd.InputStream(
            device=device, channels=1,
            samplerate=SAMPLE_RATE, 
            blocksize=BLOCKSIZE,
            latency='low',
            dtype='float32',
            callback=self._audio_callback)
        
        self.q = queue.Queue()
        self.data_q = queue.Queue()
        self.data = []

    # ========================================================================
    #                            PUBLIC METHODS
    # ========================================================================
        
    def get_stream(self):
        return self.stream
    
    def get_data(self):
        return self.data

    def update(self, current_note):
        # NOTE: If the pitch is intermittently failing to find the fundamental, turn up the device volume
        if(self.q.qsize() > 0):
            arr = []
            while not self.q.empty():
                arr.append(self.q.get())

            if current_note != -1:
                # expected_pitch = note_to_freq(current_note.pitch.midi)
                X = threading.Thread(target=self._process_data, args=(arr[0], current_note,))
                X.start()
        
        if self.data_q.qsize() > 0:
            nums = [self.data_q.get() for _ in range(self.data_q.qsize())]

            self.data.extend(nums)

            errors = [np.abs(self._get_cents(num[0], num[1])) for num in nums]
            errors = [error if error <= 255 else 255 for error in errors]
            avg_error = sum(errors) / len(errors)
            f_errors = [error for error in errors if abs(error - avg_error) < 50]
            if len(f_errors) != 0:
                avg_error = sum(f_errors) / len(f_errors)

                if avg_error <= CENTS_ERROR:
                    # Green to yellow
                    return ((avg_error/CENTS_ERROR)*255, 255, 0)
                else:
                    # Yellow to red
                    return (255, 255 - avg_error + CENTS_ERROR, 0)

        return None

    # ========================================================================
    #                            PRIVATE METHODS
    # ========================================================================

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)

        self.q.put(indata[::DOWNSAMPLE, 0])

    def _get_cents(self, f1, f2):
        if f1 == 0 or f2 == 0:
            return 255
        return 1200 * math.log2(f1/f2)

    def _process_data(self, data, expected_pitch):
        volume = self._get_volume(data)
        f0 = 0

        if volume > SILENCE_THRESHOLD and expected_pitch != 0:
            f0 = self._get_fundamental(data, expected_pitch)
       
        # if f0 == 0:
        #     volume = 0
        
        self.data_q.put((f0, expected_pitch, volume))
        return

    def _get_fundamental(self, data, expected_pitch):
        fmin = expected_pitch/1.5
        fmax = expected_pitch*1.5
        f0, vf, vp = pyin(y=data, sr=SAMPLE_RATE/DOWNSAMPLE, fmin=fmin, fmax=fmax, frame_length=len(data))

        f0 = f0[~np.isnan(f0)]
        if len(f0) == 0:
            f0 = 0
        else:
            closest = np.argmin(np.abs(f0 - expected_pitch))
            f0 = f0[closest]
        
        return f0
    
    def _get_volume(self, data):
        return np.sqrt(np.mean(data**2))
