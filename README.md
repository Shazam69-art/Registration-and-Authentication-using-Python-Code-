# Medical Authentication System #
Registration and Authentication Python Code

 Face Authentication System: A Python-based face recognition and authentication application with a graphical user interface (GUI) built using Tkinter. The system allows users with different roles (doctor, patient, receptionist, pharmacist) to register their face and authenticate themselves securely using facial recognition.

It uses:

face_recognition for face detection and encoding

OpenCV for webcam handling and image processing

Tkinter for the user interface

JSON and NumPy for data storage and encoding

Logging for tracking authentication events

Features:

           Register a new user with a face image, username, and role
           Authenticate a user by comparing the captured image with the registered encoding
           Supports multiple roles: doctor, patient, receptionist, pharmacist
           Stores images and data locally for each role
           Generates log files of all authentication attempts
           Provides clear and user-friendly GUI
           Handles errors and provides feedback during registration and authentication
           Uses threading to ensure the GUI remains responsive during processing
