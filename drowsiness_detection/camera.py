from playsound import playsound
from math import hypot
import multiprocessing
import cv2
import os
from django.conf import settings
import dlib
import datetime
from .models import drowsiness_history
import pytz


class VideoCamera(object):
    def __init__(self):     # Constructor
        self.p = multiprocessing.Process()

        self.cap = cv2.VideoCapture(0)
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(os.path.join(
            settings.BASE_DIR, "landmarks\shape_predictor_68_face_landmarks.dat"))

        self.eye_close_count = 0
        self.mouth_open_count = 0
        self.font = cv2.FONT_HERSHEY_COMPLEX

        self.yawn_count = 0
        self.yawning = False
        self.drowsy_count = 0
        self.drowsy = False

        self.max_ear = 0
        self.min_ear = 1
        self.per = 35
        self.threshold_ear = 0.25
        self.threshold_mar = 0.35
        self.max_frame_count = 20

    def soundOn(self):      # Play Sound
        if not self.p.is_alive():
            self.p = multiprocessing.Process(target=playsound, args=(
                os.path.join(settings.BASE_DIR, "landmarks\siren.mp3"),))
            self.p.start()

    def soundOff(self):     # Stop Sound
        if self.p.is_alive():
            self.p.terminate()

    def aspect_ratio(self, landmark_list, face_landmark):   # Calculate Aspect Ratio
        n = len(landmark_list)
        left_point = (face_landmark.part(
            landmark_list[0]).x, face_landmark.part(landmark_list[0]).y)
        right_point = (face_landmark.part(
            landmark_list[n//2]).x, face_landmark.part(landmark_list[n//2]).y)
        # Calculate Horizontal Length
        hor_length = hypot(
            (left_point[0] - right_point[0]), (left_point[1] - right_point[1]))

        top = list()    # Co-ordinates of the upper part
        bottom = list()  # Co-ordinates of the lower part

        for i in range(1, n//2):
            top.append((face_landmark.part(
                landmark_list[i]).x, face_landmark.part(landmark_list[i]).y))
            bottom.append((face_landmark.part(
                landmark_list[-1*i]).x, face_landmark.part(landmark_list[-1*i]).y))

        ver_lengths = list()
        for i in range(len(top)):   # Calculate vertical lengths
            ver_lengths.append(
                hypot((top[i][0] - bottom[i][0]), (top[i][1] - bottom[i][1])))

        s = len(ver_lengths)
        ratio = sum(ver_lengths) / (s * hor_length)  # Calculate aspect ratio
        return ratio

    def get_frame(self, request):

        # while True:
        ret, frame = self.cap.read()
        # if not ret:     # If no frame is detected then stop
        #     break

        frame = cv2.flip(frame, 1)
        # Convert the image to gray scale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Detect faces and get the co-ordinates of the rectangle where face is detected
        faces = self.detector(gray)

        if 0 < len(faces):
            face = faces[0]     # Consider only 1st detected face
            face_landmark = self.predictor(gray, face)   # Get facial landmarks

            left_eye_ratio = self.aspect_ratio(
                list(range(36, 42)), face_landmark)
            right_eye_ratio = self.aspect_ratio(
                list(range(42, 48)), face_landmark)
            # Calculate eye aspect ratio
            eye_aspect_ratio = (left_eye_ratio + right_eye_ratio) / 2
            cv2.putText(frame, "Cur EAR: "+str(round(eye_aspect_ratio, 5)),
                        (10, 15), self.font, 0.5, (0, 0, 0))
            cv2.putText(frame, "Thresh EAR: "+str(round(self.threshold_ear, 5)),
                        (10, 30), self.font, 0.5, (0, 0, 0))

            cv2.putText(frame, "Drowsy Count: "+str(self.drowsy_count),
                        (250, 15), self.font, 0.5, (0, 0, 0))

            inner_lip_ratio = self.aspect_ratio(
                list(range(60, 68)), face_landmark)
            outter_lip_ratio = self.aspect_ratio(
                list(range(48, 60)), face_landmark)
            # Calculate mouth aspect ratio
            mouth_aspect_ratio = (inner_lip_ratio + outter_lip_ratio) / 2
            cv2.putText(frame, "Cur MAR: "+str(round(mouth_aspect_ratio, 5)),
                        (475, 15), self.font, 0.5, (0, 0, 0))
            cv2.putText(frame, "Thresh MAR: "+str(round(self.threshold_mar, 5)),
                        (475, 30), self.font, 0.5, (0, 0, 0))
            cv2.putText(frame, "Yawn Count: "+str(self.yawn_count),
                        (475, 45), self.font, 0.5, (0, 0, 0))

            self.max_ear = max(self.max_ear, eye_aspect_ratio)
            self.min_ear = min(self.min_ear, eye_aspect_ratio)
            diff = self.max_ear - self.min_ear
            # Calculate threshold eye aspect ratio
            self.threshold_ear = self.min_ear + diff * self.per / 100

            if eye_aspect_ratio < self.threshold_ear:
                self.eye_close_count += 1
            else:
                self.eye_close_count = 0

            if mouth_aspect_ratio > self.threshold_mar:
                self.mouth_open_count += 1
            else:
                self.mouth_open_count = 0

            # Get co-ordinates of rectangle in which face is detected
            x1, y1 = face.left(), face.top()
            x2, y2 = face.right(), face.bottom()

            if self.eye_close_count >= self.max_frame_count:
                cv2.putText(frame, "Eyes Closed", (10, 55),
                            self.font, 0.75, (0, 0, 255))
            if self.mouth_open_count >= self.max_frame_count:
                cv2.putText(frame, "Yawning", (475, 70),
                            self.font, 0.75, (0, 0, 255))
                if not self.yawning:
                    self.yawn_count += 1
                    self.yawning = True
            else:
                if self.yawning:
                    self.yawning = False

            if self.eye_close_count < self.max_frame_count and self.mouth_open_count < self.max_frame_count:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (31, 163, 21), 2)
                cv2.putText(frame, "Active :)", (250, 50),
                            self.font, 1, (31, 163, 21))
                self.soundOff()
                if self.drowsy:
                    self.drowsy = False
            else:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, "Drowsy!", (250, 50),
                            self.font, 1, (255, 0, 0))
                self.soundOn()
                if not self.drowsy:
                    self.drowsy_count += 1
                    self.drowsy = True
                    time = datetime.datetime.now()
                    t = datetime.datetime(time.year, time.month, time.day, time.hour,
                                          time.minute, time.second, time.microsecond, tzinfo=pytz.UTC)
                    data = drowsiness_history(
                        USERNAME=request.user.username, NAME=request.user.first_name+request.user.last_name, EMAIL=request.user.email, TIME=t)
                    data.save()

            for i in range(0, 68):  # Plot 68 facial landmarks
                (x, y) = (face_landmark.part(i).x, face_landmark.part(i).y)
                cv2.circle(frame, (x, y), 1, (255, 255, 255), -1)

        else:
            self.soundOff()

        # cv2.imshow("Driver Drowsiness Detection System",
        #            frame)  # Display frame

        # key = cv2.waitKey(1)    # Press Esc to exit
        # if key == 27:
        #     break

        # self.soundOff()
        # cap.release()
        # cv2.destroyAllWindows()

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()

    def __del__(self):
        self.soundOff()
        self.cap.release()
        cv2.destroyAllWindows()
