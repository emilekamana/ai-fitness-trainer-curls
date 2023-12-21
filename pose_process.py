import cv2
import mediapipe as mp
from utils import calculate_angle
import numpy as np

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

class PoseProcess:
    def __init__(self) -> None:
        self.left_counter = 0
        self.right_counter = 0
        self.left_stage = None
        self.right_stage = None

    def process_frame(self, frame, pose):

        frame_height, frame_width, _ = frame.shape
        
        # Recolor image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # Make detection
        results = pose.process(image)

        # Recolor back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Extract landmarks
        try:
            landmarks = results.pose_landmarks.landmark

            # Get left coordinates
            left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            left_wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            # Get right coordinates
            right_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            right_elbow = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            right_wrist = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            
            # Calculate angle
            left_angle = calculate_angle(left_shoulder, left_elbow, left_wrist)
            right_angle = calculate_angle(right_shoulder, right_elbow, right_wrist)

            # left_elbow_text_coord_x = left_elbow[0]+10
            # right_elbow_text_coord_x = right_elbow[0]-10


            # Visualize left elbow angle
            cv2.putText(image, str(int(left_angle)),
                        tuple(np.multiply(left_elbow, [frame_width, frame_height]).astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX, (0.5*frame_height/480), (0, 255, 0), 2, cv2.LINE_AA
                                )

            # Visualize right elbow angle
            cv2.putText(image, str(int(right_angle)),
                        tuple(np.multiply(right_elbow, [frame_width, frame_height]).astype(int)),
                        cv2.FONT_HERSHEY_SIMPLEX, (0.5*frame_height/480), (0, 255, 0), 2, cv2.LINE_AA
                                )

            # print()
            # Curl left side counter logic
            if left_angle > 160:
                self.left_stage = "down"
            if left_angle < 30 and self.left_stage =='down':
                self.left_stage="up"
                self.left_counter +=1
                print("left: ",self.left_counter)

            # Curl right side counter logic
            if right_angle > 160:
                self.right_stage = "down"
            if right_angle < 30 and self.right_stage =='down':
                self.right_stage="up"
                self.right_counter +=1
                print(self.right_counter)

        except:
            pass

        # Render curl self.counter
        # Setup status box
        cv2.rectangle(image, (0,0), (int(frame_width*0.40),int(80*frame_height/480)), (245,117,16), -1)

        # Rep data
        cv2.putText(image, 'LEFT ' + str(self.left_counter) +' reps ' + str(self.left_stage), 
                    (15,int(30*frame_height/480)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7*frame_height/480, (255,255,255), 2, cv2.LINE_AA)
        cv2.putText(image, 'RIGHT ' + str(self.right_counter) +' reps ' + str(self.right_stage),
                    (15,int(60*frame_height/480)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7*frame_height/480, (255,255,255), 2, cv2.LINE_AA)

        # self.stage data
        # cv2.putText(image, 'self.stage', (65,12),
        #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
        # cv2.putText(image, self.stage,
        #             (60,60),
        #             cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)


        # Render detections
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                                mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                                )

        return image

    def process_video(self, vr, out, pose):
        
        for frame in vr[:]:

            processed_frame = self.process_frame(frame, pose)
            
            out.write(processed_frame)

        out.release()