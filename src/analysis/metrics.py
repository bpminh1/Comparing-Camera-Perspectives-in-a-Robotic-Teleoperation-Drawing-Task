import cv2
import numpy as np
import os
import pandas as pd

def compute_Hu_Moments(img):
    '''Computes the Hu Moments for a given image. 
    The image is expected to be a binary image where the shape is represented by white pixels on a black background.
    '''
    moments = cv2.moments(img)
    hu_moments = cv2.HuMoments(moments)
    return hu_moments.flatten()

def compute_hu_similarity(hu1, hu2):
    '''Computes the similarity between two sets of Hu Moments using a logarithmic transformation.'''
    mi1 = np.array([-np.sign(h)*np.log10(abs(h)+1e-30) for h in hu1])
    mi2 = np.array([-np.sign(h)*np.log10(abs(h)+1e-30) for h in hu2])
    distance = np.sum(np.abs(mi1 - mi2))
    return distance

def compute_contour_similarity(img1, img2):
    '''Computes the similarity between the contours of two images.'''
    contours1, _ = cv2.findContours(img1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours2, _ = cv2.findContours(img2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours1) > 0 and len(contours2) > 0:
        match = cv2.matchShapes(contours1[0], contours2[0], cv2.CONTOURS_MATCH_I1, 0)
        return match
    return float('inf')

def compute_chamfer_distance(img1, img2):
    '''Computes the Chamfer distance between two binary images.'''
    dist1 = cv2.distanceTransform(255 - img1, cv2.DIST_L2, 5)
    dist2 = cv2.distanceTransform(255 - img2, cv2.DIST_L2, 5)

    pts1 = np.argwhere(img1 > 0)
    pts2 = np.argwhere(img2 > 0)

    if len(pts1) == 0 or len(pts2) == 0:
        return float('inf')

    d12 = np.mean([dist2[y, x] for y, x in pts1])
    d21 = np.mean([dist1[y, x] for y, x in pts2])
    return float((d12 + d21) / 2)

def analyse_trial(trial_path):
    '''Analyzes a single trial by computing the Hu Moments similarity, contour similarity, and Chamfer distance between the drawn image and the target image.'''
    target_image = cv2.imread(os.path.join(trial_path, 'target.png'), cv2.IMREAD_GRAYSCALE)
    drawn_image = cv2.imread(os.path.join(trial_path, 'drawn.png'), cv2.IMREAD_GRAYSCALE)

    hu_drawn = compute_Hu_Moments(drawn_image)
    hu_target = compute_Hu_Moments(target_image)

    hu_score = compute_hu_similarity(hu_drawn, hu_target)
    contour_score = compute_contour_similarity(drawn_image, target_image)
    chamfer_score = compute_chamfer_distance(drawn_image, target_image)

    return {
        'trial': os.path.basename(trial_path),
        'hu_similarity': hu_score,
        'contour_similarity': contour_score,
        'chamfer_distance': chamfer_score
    }

def analyse_participant(participant_path):
    '''Analyzes all trials for a given participant and saves the results to a summary CSV file.'''
    trial_results = []
    for trial in os.listdir(participant_path):
        trial_path = os.path.join(participant_path, trial)
        if os.path.isdir(trial_path):
            result = analyse_trial(trial_path)
            trial_results.append(result)

    summary_path = os.path.join(participant_path, 'summary.csv')
    df_metrics = pd.DataFrame(trial_results)
    trials_info = pd.read_csv(summary_path)
    df = pd.merge(trials_info, df_metrics, on='trial', how='left')
    df.to_csv(summary_path, index=False)

def analyse_all_participants(results_path):
    '''Analyzes all participants in the given results path.'''
    for participant in os.listdir(results_path):
        participant_path = os.path.join(results_path, participant)
        if os.path.isdir(participant_path):
            analyse_participant(participant_path)