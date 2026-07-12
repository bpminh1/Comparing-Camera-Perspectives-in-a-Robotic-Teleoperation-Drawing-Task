# Comparing Camera Perspectives in a Robotic Teleoperation Drawing Task

This repository contains the implementation for a Bachelor thesis at TU Darmstadt.

The thesis studies how camera perspective affects performance and user experience in a teleoperation drawing task with a simulated Franka Emika Panda robot.

## Project Overview

Participants control a simulated robot arm through hand-tracking input and complete drawing tasks under different camera perspectives. The system records interaction data, computes objective task metrics, and evaluates subjective feedback from questionnaires and camera preference choices.

## What This Project Does

- Runs a MuJoCo-based robot teleoperation experiment.
- Uses MediaPipe hand tracking for user input.
- Manages a structured multi-block study flow with tutorials, trials, and questionnaires.
- Stores participant-level trial data and calibration data.
- Processes collected drawing outputs for analysis.

## Main Components

- Experiment runtime and control logic: src/experiments and src/core
- Experiment configuration: config/experiment_config.yaml
- Analysis scripts: src/analysis
- Franka IK extension (C++/pybind11): ext and third_party

## Research Focus

The project investigates camera perspective effects on:

- Drawing accuracy and time efficiency in teleoperated drawing.
- Learning behavior across repeated trials.
- Subjective usability, comfort, and camera preference.

## Thesis Context

This codebase serves as:

- The experimental software stack used to run participant studies.
