import cv2
import time
import RPi.GPIO as GPIO
from gsmmodem import GsmModem
from gpsd import gpscommon

# Initialize GSM modem
gsm_modem = GsmModem(port="/dev/ttyUSB0")  # Update with your actual port
gsm_modem.connect(baudrate=9600)

# Initialize GPS
gpsd = gpscommon.connect()

GPIO.setmode(GPIO.BCM)
button_pin1 = 13
button_pin2 = 16
button_pin3 = 19
button_pin4 = 26
button_pin5 = 20
button_pin6 = 21

button_pins = [button_pin1, button_pin2, button_pin3, button_pin4, button_pin5, button_pin6]
GPIO.setup(button_pins, GPIO.OUT)

# Load class names from a file (coco.names)
classNames = []
classFile = "coco.names"
with open(classFile, "rt") as f:
    classNames = f.read().rstrip("\n").split("\n")

# Load pre-trained model configuration and weights
configPath = "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "frozen_inference_graph.pb"

# Create a detection model using OpenCV's dnn module
net = cv2.dnn_DetectionModel(weightsPath, configPath)
net.setInputSize(320, 320)
net.setInputScale(1.0 / 127.5)
net.setInputMean((127.5, 127.5, 127.5))
net.setInputSwapRB(True)

# Function to send SMS using GSM modem
def send_sms(message):
    gsm_modem.sendSms("+123456789", message)  # Update with the recipient's phone number

# Function to get GPS coordinates
def get_gps_coordinates():
    report = gpsd.next()
    if report['class'] == 'TPV':
        return report.lat, report.lon
    return None

# Function to perform object detection and draw rectangles around detected objects
def find_position_cutdown_y(box, frame_width, frame_height):
    x, y, w, h = box

    # Calculate object position in terms of left, right, center
    x_position = "Left" if x < frame_width // 3 else "Center" if x < 2 * frame_width // 3 else "Right"
    y_position = "Top" if y < frame_height // 3 else "Center" if y < 2 * frame_height // 3 else "Bottom"

    return x_position, y_position

def getObjects(img, net, thres, nms, min_area_threshold, max_area_threshold, draw=True, objects=[]):
    classIds, confs, bbox = net.detect(img, confThreshold=thres, nmsThreshold=nms)
    
    if len(objects) == 0:
        objects = classNames
    
    objectInfo = []
    
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            className = classNames[classId - 1]
            
            # Calculate the area of the bounding box
            box_area = box[2] * box[3]
            
            # Check if the area is within the specified thresholds
            if min_area_threshold <= box_area <= max_area_threshold:
                objectInfo.append([box, className, box_area])
                
                if draw:
                    # Draw the bounding box on the image
                    cv2.rectangle(img, box, color=(0, 255, 0), thickness=2)
                    
                    frame_height, frame_width, _ = img.shape
                    x_position, y_position = find_position_cutdown_y(box, frame_width, frame_height)

                    # Display the position information
                    position_text = f"X: {x_position}, Y: {y_position}"
                    cv2.putText(img, position_text, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                   
                    try:
                        if x_position == "Right":
                            GPIO.output(button_pin1, GPIO.HIGH)
                            time.sleep(2)
                        elif x_position == "Center":
                            GPIO.output(button_pin2, GPIO.HIGH)
                            GPIO.output(button_pin5, GPIO.HIGH)
                            time.sleep(2)
                        elif x_position == "Left":
                            GPIO.output(button_pin6, GPIO.HIGH)
                            time.sleep(2)
                        elif y_position == "Bottom":
                            GPIO.output(button_pin4, GPIO.HIGH)
                            time.sleep(2)
                        
                        # Example: Send SMS when a specific object is detected
                        if className == "person":
                            send_sms("Person detected!")

                        # Example: Get GPS coordinates when a specific object is detected
                        if className == "Person":
                            coordinates = get_gps_coordinates()
                            if coordinates:
                                print(f"Person detected! GPS Coordinates: {coordinates}")
                    
                    finally:
                        GPIO.output(button_pins, GPIO.LOW)  # Turn off all the pins
                        time.sleep(2)  # Keep the pins low for an additional 2 seconds

    return img, objectInfo

# Main program
if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    while True:
        success, img = cap.read()
        result, objectInfo = getObjects(img, net, 0.45, 0.2, min_area_threshold=50000, max_area_threshold=200000)
        
        for info in objectInfo:
            box, className, area = info
            # print(f"Class: {className}, Area: {area}")

        cv2.imshow("Output", img)
        cv2.waitKey(1)
