import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.analysis.metrics import analyse_participant
from src.analysis.process_image import save_one_participant

def main():
    '''Main function to process the images and analyze the results for a specific participant.'''
    participant_name = 'P30'
    save_one_participant(participant_name, os.path.join('data', 'collected'), os.path.join('data', 'analysed'))
    analyse_participant(os.path.join('data', 'analysed', participant_name))

if __name__ == "__main__":
    main()