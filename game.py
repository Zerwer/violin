from music21 import *
import pickle
from pygame.locals import *
import pygame
import pygame.midi
from constants import *
from animation import Animation
from audio import AudioInput
from score import plt_data

def main(score, audio_in):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    clock = pygame.time.Clock()

    animation = Animation(score, screen)
    animation.do_countdown()

    while animation.should_continue():
        screen.fill(WHITE)

        marker_colour = audio_in.update(animation.get_current_note_hz())
        
        if marker_colour:
            animation.set_marker_colour(marker_colour)

        animation.do_frame()

        pygame.display.flip()
        clock.tick(FPS)

        # Check for quit events
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit(0)
    # end pygame
    pygame.quit()

    data = audio_in.get_data()
    plt_data(data)

if __name__ == "__main__":
    save = 'Storm.pkl'
    with open(save, 'rb') as f:
        score = pickle.load(f)
    
    # HACK: WTF?? Seems to drop spanners after pickle
    my_score = converter.parse('storms.mxl')
    score.score = my_score
    
    audio_in = AudioInput(device=0)
    
    with audio_in.get_stream():
        main(score, audio_in)
