import os
import cv2
import pytz
import datetime
import time as tm
import multiprocessing
import mediapipe as mp
from playsound import playsound
from math import hypot
from django.conf import settings
from .models import drowsiness_history


class VideoCamera(object):
    def __init__(self):     # Constructor
        self.p = multiprocessing.Process()

        self.cap = cv2.VideoCapture(0)
        self.pTime = 0

        self.mpFaceMesh = mp.solutions.face_mesh
        self.faceMesh = self.mpFaceMesh.FaceMesh()

        self.eye_close_count = 0
        self.mouth_open_count = 0
        self.font = cv2.FONT_HERSHEY_COMPLEX

        self.yawn_count = 0
        self.yawning = False
        self.drowsy_count = 0
        self.drowsy = False

        self.max_ear = 0
        self.min_ear = 1
        self.per = 40
        self.threshold_ear = 0.25
        self.threshold_mar = 0.35
        self.max_frame_count = 20

        self.le = [33, 246, 161, 160, 159, 158, 157, 173,
                   133, 155, 154, 153, 145, 144, 163, 7]
        self.re = [362, 398, 384, 385, 386, 387, 388, 466,
                   263, 249, 390, 373, 374, 380, 381, 382]

        self.il = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415,
                   308, 324, 318, 402, 317, 14, 87, 178, 88, 95]
        self.ol = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409,
                   291, 375, 321, 405, 314, 17, 84, 181, 91, 146]

    def soundOn(self):      # Play Sound
        if not self.p.is_alive():
            self.p = multiprocessing.Process(target=playsound, args=(
                os.path.join(settings.BASE_DIR, "landmarks\siren.mp3"),))
            self.p.start()

    def soundOff(self):     # Stop Sound
        if self.p.is_alive():
            self.p.terminate()

    def aspect_ratio(self, landmark_list, face_landmarks):   # Calculate Aspect Ratio
        n = len(landmark_list)

        # Calculate horizontal length
        left_point = face_landmarks[landmark_list[0]]  # (x, y)
        right_point = face_landmarks[landmark_list[n//2]]
        hor_length = hypot(
            (left_point[0] - right_point[0]), (left_point[1] - right_point[1]))

        top = list()    # Co-ordinates of the upper part
        bottom = list()  # Co-ordinates of the lower part

        for i in range(1, n//2):
            top.append(face_landmarks[landmark_list[i]])
            bottom.append(face_landmarks[landmark_list[-1*i]])

        ver_lengths = list()
        for i in range(len(top)):   # Calculate vertical lengths
            d = hypot((top[i][0] - bottom[i][0]), (top[i][1] - bottom[i][1]))
            ver_lengths.append(d)

        s = len(ver_lengths)
        ratio = sum(ver_lengths) / (s * hor_length)  # Calculate aspect ratio
        return ratio

    def landmarkCoordinates(self, facelandmarks, image):
        coord = list()
        ih, iw, ic = image.shape  # image height, image width, image channels
        for lm in facelandmarks:
            x, y = int(lm.x*iw), int(lm.y*ih)
            coord.append((x, y))
        return coord

    def get_frame(self, request):

        # while True:
        success, frame = self.cap.read()
        # if not success:     # If no frame is detected then stop
        #     break

        frame = cv2.flip(frame, 1)
        # Detect faces and get the co-ordinates of the rectangle where face is detected
        results = self.faceMesh.process(frame)  # Detect faces

        self.cTime = tm.time()
        fps = 1/(self.cTime - self.pTime)
        self.pTime = self.cTime
        cv2.putText(frame, f"FPS: {int(fps)}",
                    (10, 15), self.font, 0.5, (0, 0, 0))

        if results.multi_face_landmarks:
            # Consider only 1st detected face
            face = results.multi_face_landmarks[0]
            face_landmarks = self.landmarkCoordinates(
                face.landmark, frame)   # Get facial landmarks

            left_eye_ratio = self.aspect_ratio(
                self.le, face_landmarks)  # 7vertical 1horizontal
            right_eye_ratio = self.aspect_ratio(
                self.re, face_landmarks)  # 7v 1h
            # Calculate eye aspect ratio
            eye_aspect_ratio = (left_eye_ratio + right_eye_ratio) / 2
            cv2.putText(frame, "Cur EAR: "+str(round(eye_aspect_ratio, 5)),
                        (10, 30), self.font, 0.5, (0, 0, 0))
            cv2.putText(frame, "Thresh EAR: "+str(round(self.threshold_ear, 5)),
                        (10, 45), self.font, 0.5, (0, 0, 0))

            cv2.putText(frame, "Drowsy Count: "+str(self.drowsy_count),
                        (250, 15), self.font, 0.5, (0, 0, 0))

            inner_lip_ratio = self.aspect_ratio(
                self.il, face_landmarks)  # 9v  1h
            outter_lip_ratio = self.aspect_ratio(
                self.ol, face_landmarks)  # 9v 1h
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
            self.threshold_ear = self.min_ear + diff * self.per / \
                100      # Calculate threshold eye aspect ratio

            if eye_aspect_ratio < self.threshold_ear:
                self.eye_close_count += 1
            else:
                self.eye_close_count = 0

            if mouth_aspect_ratio > self.threshold_mar:
                self.mouth_open_count += 1
            else:
                self.mouth_open_count = 0

            if self.eye_close_count >= self.max_frame_count:
                cv2.putText(frame, "Eyes Closed", (10, 70),
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

            # Get co-ordinates of rectangle in which face is detected
            x1, y1 = face_landmarks[234][0], face_landmarks[10][1]
            x2, y2 = face_landmarks[454][0], face_landmarks[152][1]

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

            for i in self.le + self.re + self.il + self.ol:  # Plot facial landmarks
                x, y = face_landmarks[i][0], face_landmarks[i][1]
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
