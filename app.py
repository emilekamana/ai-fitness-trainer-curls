import os
import sys
import streamlit as st
import mediapipe as mp
import cv2
import tempfile
import numpy as np
from videoreader import VideoReader

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a,b,c):
    a = np.array(a) # First
    b = np.array(b) # Mid
    c = np.array(c) # End

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)

    if angle >180.0:
        angle = 360-angle

    return angle

def process_video(vr, out):
    # Curl counter variables
    counter = 0
    stage = None

    ## Setup mediapipe instance
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        for frame in vr[:]:

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

                # Get coordinates
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                # Calculate angle
                angle = calculate_angle(shoulder, elbow, wrist)

                # Visualize angle
                cv2.putText(image, str(angle),
                            tuple(np.multiply(elbow, [640, 480]).astype(int)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                                    )

                # Curl counter logic
                if angle > 160:
                    stage = "down"
                if angle < 30 and stage =='down':
                    stage="up"
                    counter +=1
                    print(counter)

            except:
                pass

            # Render curl counter
            # Setup status box
            cv2.rectangle(image, (0,0), (225,73), (245,117,16), -1)

            # Rep data
            cv2.putText(image, 'REPS', (15,12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter),
                        (10,60),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)

            # Stage data
            cv2.putText(image, 'STAGE', (65,12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
            cv2.putText(image, stage,
                        (60,60),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 2, cv2.LINE_AA)


            # Render detections
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                    mp_drawing.DrawingSpec(color=(245,117,66), thickness=2, circle_radius=2),
                                    mp_drawing.DrawingSpec(color=(245,66,230), thickness=2, circle_radius=2)
                                    )

            out.write(image)

        out.release()


# Main Streamlit app
def main():
    download = None

    if 'download' not in st.session_state:
        st.session_state['download'] = False

    st.title("AI Fitness Trainer: Bicep Curl Counter")

    output_video_file = f'output_recorded.mp4'

    if os.path.exists(output_video_file):
        os.remove(output_video_file)

    # Upload video through Streamlit
    with st.form('Upload', clear_on_submit=True):
        uploaded_file = st.file_uploader("Upload a video of type mp4, mov, avi", type=['mp4','mov', 'avi'])
        uploaded = st.form_submit_button("Upload")

    stframe = st.empty()

    ip_vid_str = '<p style="font-family:Helvetica; font-weight: bold; font-size: 16px;">Input Video</p>'

    download_button = st.empty()

    if uploaded_file and uploaded:
        download_button.empty()
        tfile = tempfile.NamedTemporaryFile(delete=False)
        try:
            tfile.write(uploaded_file.read())

            cap = cv2.VideoCapture(tfile.name)

            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            frame_size = (width, height)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v') #codec
            out = cv2.VideoWriter(output_video_file, fourcc, fps, frame_size)
            
            vr = VideoReader(tfile.name)

            process_video(vr, out)

            out.release()
            stframe.empty()
            ip_video.empty()
            txt.empty()
            tfile.close()

            txt = st.sidebar.markdown(ip_vid_str, unsafe_allow_html=True)   
            ip_video = st.sidebar.video(tfile.name) 

        except:
            # If the file is not an image, show an error message
            st.error("Something went wrong. Please try uploading another image file.")
    else:
        # If no file is uploaded, show a warning message
        st.warning("Please upload a video file")

    if os.path.exists(output_video_file):
        with open(output_video_file, 'rb') as op_vid:
            download = download_button.download_button('Download Video', data = op_vid, file_name='output_recorded.mp4')
    
    if download:
        st.session_state['download'] = True



    if os.path.exists(output_video_file) and st.session_state['download']:
        os.remove(output_video_file)
        st.session_state['download'] = False
        download_button.empty()


if __name__ == '__main__':
    main()
