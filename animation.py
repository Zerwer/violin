from constants import *
from scamp import *
from util import note_to_freq
import pygame
import numpy as np
from music21 import *

# Manage the animation of the music score
class Animation:
    def __init__(self, score, screen):
        self.score = score
        self.screen = screen

        self.music_clips = [pygame.image.fromstring(img.img, img.size, 'RGBA') for img in score.imgs]

        self.key_img = self.music_clips[0]
        self.music_clips = self.music_clips[1:]

        self.marker = pygame.Surface((MARKER_WIDTH,100))
        self.marker.set_alpha(128)
        self.marker.fill(BLACK)

        self.x = self.key_img.get_width() + MARKER_OFFSET + MARKER_WIDTH
        self.y = HEIGHT // 2

        self.img_index = 0
        self.measure_index = 0
        self.note_index = 0
        self.measure_frame = 0

        self.measures = score.get_measures()
        self.speeds = self._measure_speeds()

        self.isTied = False
        self.isSpanning = False
        self._update_transitions()

        # Playback init
        self.ses = Session()
        self.violin = self.ses.new_part("violin")

        self._should_continue = True

    # ========================================================================
    #                            PUBLIC METHODS
    # ========================================================================

    def do_countdown(self):
        count = 3
        font = pygame.font.Font(None, 60)
        for _ in range(3):
            self.screen.fill(WHITE)
            self._draw_music()
            self._draw_marker()
            text = font.render(str(count), True, BLACK)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(text, text_rect)
            pygame.display.flip()
            pygame.time.wait(1000)
            count -= 1

    def do_frame(self):
        self._draw_music()
        self._draw_marker()
        self._increase_measure_frame()
        self._move_x()
        
    def set_marker_colour(self, colour):
         # Do not update during note transitions, except for ties
        if np.abs(self.measure_frame - self._get_note_frames()) <= 4 and not self.isTied:
            return
        self.marker.fill(colour)

    def get_current_note_hz(self):
        if self.get_current_note().isNote:
            if not self.isSpanning and not self.isTied:
                if np.abs(self.measure_frame - self._get_note_frames()) <= 2:
                    return 0
            return note_to_freq(self.get_current_note().pitch.midi)
        return -1 # Rest

    def get_current_note(self):
        return self.measures[self.measure_index].notesAndRests[self.note_index]
    
    def should_continue(self):
        return self._should_continue

    # ========================================================================
    #                            PRIVATE METHODS
    # ========================================================================

    def _update_transitions(self):
        current_note = self.get_current_note()
        spanners = current_note.getSpannerSites()
            
        if current_note.tie:
            self.isTied = not self.isTied
        if spanners:
            self.isSpanning = not self.isSpanning  

    # Create an array where a[i] gives (speed (pixels/frame), # of frames) for measure i
    def _measure_speeds(self):
        speeds = []
        beat_duration = 60 / self.score.bpm
        
        index = 0
        for img in self.score.imgs[1:]:
            width = img.size[0]
            total_layout_width = sum([m.layoutWidth for m in self.measures[index:index + img.count]])
            
            for j in range(img.count):
                m_size = ((self.measures[index + j].layoutWidth / total_layout_width) * width)
                q_len = self.measures[index + j].duration.quarterLength
                m_duration = q_len * beat_duration
                m_frame_count = m_duration * FPS
                speed = m_size / m_frame_count
                speeds.append((speed, int(m_frame_count)))
            index += img.count
                
        return speeds

    def _draw_music(self):
            current_image = self.music_clips[self.img_index]
            w_offset = 0
            for i in range(1, BUFFER_IMAGES):
                if self.img_index + i >= len(self.music_clips):
                    break
                w_offset += self.music_clips[self.img_index + i - 1].get_width()
                next_image = self.music_clips[self.img_index + i]
                self.screen.blit(next_image, (self.x + w_offset, self.y))

            self.screen.blit(current_image, (self.x, self.y))
            self.screen.blit(self.key_img, (0, self.y))
            pygame.draw.rect(self.screen, WHITE, (0, self.y + self.key_img.get_height(), self.key_img.get_width(), 100))
            pygame.draw.rect(self.screen, WHITE, (0, 0, self.key_img.get_width(), HEIGHT - self.key_img.get_height() - 50))

            pygame.draw.line(self.screen, BLACK, (self.key_img.get_width(), HEIGHT - self.key_img.get_height() - 3), (self.key_img.get_width(), HEIGHT - 123), 4)

    def _draw_marker(self):
        if not self.get_current_note().isNote:
            self.set_marker_colour(BLACK)
        self.screen.blit(self.marker, (self.key_img.get_width() + MARKER_OFFSET, HEIGHT - self.key_img.get_height() - 5)) 

    def _do_note(self, instrument, note):
        instrument.end_all_notes()
        instrument.play_note(note.pitch.midi, 1.0, note.duration.quarterLength)

    def _trigger_playback(self):
        if DEBUG_PRINT_NOTE:
            if self.get_current_note().isNote:
                print(self.get_current_note())
                print(note_to_freq(self.get_current_note().pitch.midi))
        if PLAYBACK:
            if self.get_current_note().isNote:
                fork_unsynchronized(self._do_note, (self.violin, self.get_current_note()))
            else:
                self.violin.end_all_notes()

    def _get_note_frames(self):
        return sum([self.measures[self.measure_index].notesAndRests[i].duration.quarterLength * (60 / self.score.bpm) * FPS 
                    for i in range(self.note_index + 1)])

    def _get_speed(self):
        return self.speeds[self.measure_index][0]

    def _get_measure_frame_size(self):
        return self.speeds[self.measure_index][1]

    def _increase_measure_frame(self):
        self.measure_frame += 1

        if self.measure_frame >= self._get_measure_frame_size():
            self.measure_index += 1
            self.measure_frame = 0
            self.note_index = 0

            if self.measure_index >= len(self.measures):
                self._should_continue = False
                if PLAYBACK:
                    self.violin.end_all_notes()
            else:
                self._update_transitions()
                self._trigger_playback()
        elif self.measure_frame > self._get_note_frames():
            self.note_index += 1
            self._update_transitions()
            self._trigger_playback()
            
    def _move_x(self):
        if not self._should_continue:
            return

        self.x -= self._get_speed()

        # If image has moved off the left side, reset position and move to the next image
        if self.x < -self.music_clips[self.img_index].get_width() + self.key_img.get_width():
            self.x +=self.music_clips[self.img_index].get_width()
            self.img_index += 1
        