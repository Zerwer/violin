import matplotlib.pyplot as plt
from constants import *

def plt_data(data):
    # each data point is: (actual_hz, expected_hz, volume)
    # graph two lines: actual and expected

    # Set to 0 if volume is too low
    actual = [x[0] if x[2] > SILENCE_THRESHOLD else 0 for x in data]
    # shift expected to the right by 1
    expected = [x[1] for x in data]
    expected = [0] + expected[:-1]
    volume = [x[2] *1000 for x in data]
    


    # actual
    plt.plot(actual, label='Actual Hz')
    # expected
    plt.plot(expected, label='Expected Hz')
    # volume
    plt.plot(volume, label='Volume')

    errors = [abs(x[0] - x[1]) for x in data]
    errors_less_than_50 = [error for error in errors if error <= 50]
    print("Rythmn accuracy: {:.2f}%".format(len(errors_less_than_50) / len(errors) * 100))

    # Slur accuracy
    # find index in expected where x[i] != 0 and x[i] != x[i+1]
    slur_indices = [i for i in range(len(expected) - 1) if expected[i] != 0 and expected[i] != expected[i + 1] and expected[i + 1] != 0]
    bow_change_indices = [i for i in range(len(expected) - 1) if expected[i] != 0 and expected[i + 1] == 0]
    
    total_slurs = len(slur_indices)
    correct_slurs = len(slur_indices)
    for slur in slur_indices:
        lower = max(0, slur - 2)
        upper = min(len(actual) - 1, slur + 2)
        # check for atleast 2 zero values in the range
        if len([actual[i] for i in range(lower, upper + 1) if actual[i] == 0]) > 0:
            correct_slurs -= 1
    
    if total_slurs != 0:
        print("Got {} out of {} slurs correct ({:.2f}%)".format(correct_slurs, total_slurs, correct_slurs / total_slurs * 100))

    total_bow_changes = len(bow_change_indices)
    correct_bow_changes = len(bow_change_indices)
    for bow_change in bow_change_indices:
        lower = max(0, bow_change - 2)
        upper = min(len(actual) - 1, bow_change + 2)
        # check for zero values in the range
        # Check for at least 2 non-zero values in the range
        if len([actual[i] for i in range(lower, upper + 1) if actual[i] == 0]) > 0:
            pass
        else:
            correct_bow_changes -= 1
        # if 0 not in [data[i][0] for i in range(lower, upper + 1)]:
        #     correct_bow_changes -= 1
    
    if total_bow_changes != 0:
        print("Got {} out of {} bow changes correct ({:.2f}%)".format(correct_bow_changes, total_bow_changes, correct_bow_changes / total_bow_changes * 100))

    # draw vertical lines at indices
    # for index in slur_indices:
    #     plt.axvline(x=index, color='r', linestyle='--')

    # for index in bow_change_indices:
    #     plt.axvline(x=index, color='g', linestyle='--')
    # print(indices)

    plt.legend()
    plt.show()
