import pandas as pd
import json
import os
from glob import glob
from scipy.stats import norm
import numpy as np

class DataLoader:
    def __init__(self):
        self.collected = '/Users/minhbui/Desktop/Thesis/data/collected'
        self.analysed = '/Users/minhbui/Desktop/Thesis/data/analysed'
        self.participants = [d for d in os.listdir(self.collected) if os.path.isdir(os.path.join(self.collected, d))]

        self.data = None
        self.questionnaire = None
        self.questionnaire_preferences = None

    def load_data(self):
        self.data = self.get_data_all_participants(self.participants)
        self.data = self.remove_invalid_data(self.data)
        self.data = self.remove_outliers(self.data)
        self.data = self.scale_measurements(self.data)

        self.questionnaire, self.questionnaire_preferences = self.get_questionnaire_all_participants(self.participants)
        self.questionnaire = self.reverse_questionnaire_responses(self.questionnaire)
        self.questionnaire = self.add_categorical_variables(self.questionnaire)

        self.questionnaire_preferences = self.questionnaire_preferences.rename(columns={'Question': 'shape', 'Response': 'preferred_camera'})

    def open_json(self, path):
        with open(path, 'r') as f:
            return json.load(f)

    def open_csv(self, path):
        return pd.read_csv(path)
    
    def get_metadata_one_trial(self, participant, filename):
        trial = int(os.path.basename(filename).split('.')[0].split('_')[1])
        data = self.open_json(filename)
        meta_data = {}
        meta_data['participant'] = participant
        meta_data['block'] = 1 if trial <=7 else 2 if trial <= 14 else 3
        meta_data['trial'] = trial
        meta_data.update(data['metadata'])
        return meta_data

    def get_metadata_one_participant(self, participant):
        path = os.path.join(self.collected, participant, '*.json')
        files = glob(path)
        metadata = []
        for file in files:
            meta_data = self.get_metadata_one_trial(participant, file)
            metadata.append(meta_data)
        return metadata
    
    def get_summary_one_participant(self, participant):
        path = os.path.join(self.analysed, participant, 'summary.csv')
        data = self.open_csv(path)
        data['participant'] = participant
        data['trial'] = data['trial'].apply(lambda x: int(x.split('_')[1]))
        data = data.drop(columns=['shape'])
        return data
    
    def get_questionnaire_one_participant(self, participant):
        path = os.path.join(self.collected, participant, 'questionnaire', '*.csv')
        files = glob(path)
        questionnaire = []
        questionnaire_preferences = []
        for file in files:
            if 'preference' in os.path.basename(file):
                data = self.open_csv(file)
                data['participant'] = participant
                questionnaire_preferences.append(data)
                continue
            data = self.open_csv(file)
            data['participant'] = participant
            data['camera'] = os.path.basename(file)[:-18]  # Remove '_questionnaire.csv'
            questionnaire.append(data)
        return pd.concat(questionnaire, ignore_index=True), pd.concat(questionnaire_preferences, ignore_index=True)

    def get_questionnaire_all_participants(self, participants):
        questionnaire = []
        questionnaire_preferences = []
        for participant in participants:
            data, preferences = self.get_questionnaire_one_participant(participant)
            questionnaire.append(data)
            questionnaire_preferences.append(preferences)
        return pd.concat(questionnaire, ignore_index=True), pd.concat(questionnaire_preferences, ignore_index=True)
    
    def reverse_questionnaire_responses(self, df):
        reverse_questions = [
            "I felt sick to my stomach during the experiment.",
            "I felt dizzy during the experiment.",
            "I felt like I was going to vomit during the experiment.",
            "I felt disoriented during the experiment.",
            "I felt fatigued during the experiment.",
            "I felt that I could have performed better with a different camera perspective.",
            "I felt that the shapes were too difficult to follow during the experiment.",
            "I felt that there was a delay between my commands and the robot's response during the experiment.",
            "I felt that the latency affected my performance during the experiment."
        ]

        df.loc[
            df['Question'].isin(reverse_questions), 'Response'
        ] = 6 - df.loc[
            df['Question'].isin(reverse_questions), 'Response'
        ]
        return df
    
    def add_categorical_variables(self, df):
        categories = {
            "Motion Sickness": [
                "I felt sick to my stomach during the experiment.",
                "I felt dizzy during the experiment.",
                "I felt like I was going to vomit during the experiment.",
                "I felt disoriented during the experiment.",
                "I felt fatigued during the experiment."
            ],
            "Camera Usability": [
            "It was easy to use this camera perspective.",
            "It did not take long to get used to this camera perspective.",
            "I felt that the camera perspective provided a good view of the workspace.",
            "I felt that I could have performed better with a different camera perspective.",
            "Overall, I am satisfied with this camera perspective."
            ],
            "Task Accuracy": [
            "I was able to accurately perform the tasks during the experiment.",
            "I felt that the shapes were too difficult to follow during the experiment.",
            "I looked at the whole shape before trying to follow it during the experiment."
            ],
            "Robot Control": [
            "I felt that the robot responded well to my commands during the experiment.",
            "I felt that I had good control over the robot during the experiment."
            ],
            "System Latency": [
            "I felt that there was a delay between my commands and the robot's response during the experiment.",
            "I felt that the latency affected my performance during the experiment."
            ]
        }

        question_to_category = {}
        for cat, questions in categories.items():
            for q in questions:
                question_to_category[q] = cat

        df['category'] = df['Question'].map(question_to_category)
        return df
    
    def get_data_one_participant(self, participant):
        metadata = self.get_metadata_one_participant(participant)
        summary = self.get_summary_one_participant(participant)
        data = pd.merge(pd.DataFrame(metadata), summary, on=['participant', 'trial'])
        return data

    def get_data_all_participants(self, participants):
        metadata = []
        for participant in participants:
            data = self.get_data_one_participant(participant)
            metadata.append(data)
        df_metadata = pd.concat(metadata, ignore_index=True)
        df_sorted = df_metadata.sort_values(by=["participant", "shape", "trial"])
        df_sorted["shape_trial_idx"] = (
            df_sorted
            .groupby(["participant", "shape"])
            .cumcount() + 1
        )
        return df_sorted

    def remove_invalid_data(self, df):
        mask = ~np.isinf(df['chamfer_distance'])
        return df[mask]
    
    def remove_outliers(self, df):
        log_d = np.log1p(df['duration'])
        log_c = np.log1p(df['chamfer_distance'])
        df['log_d'] = log_d
        df['log_c'] = log_c

        iqr_d = log_d.quantile(0.75) - log_d.quantile(0.25)
        iqr_c = log_c.quantile(0.75) - log_c.quantile(0.25)

        df['z_d'] = (log_d - log_d.median()) / iqr_d
        df['z_c'] = (log_c - log_c.median()) / iqr_c

        mask = (df['z_c'] <= 3) & (df['z_d'] <= 3)
        return df[mask]
    
    def scale_measurements(self, df):
        difficulty = 0.2 * df['z_d'] + 0.8 * df['z_c']
        df['performance'] = norm.cdf(-difficulty) * 100
        df['accuracy'] = norm.cdf(-df['z_c']) * 100
        df['efficiency'] = norm.cdf(-df['z_d']) * 100
        return df