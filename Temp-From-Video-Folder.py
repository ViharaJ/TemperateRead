"""
Retreives temperatures from video and returns results in an excel file. 
A 'Results' folder is created inside the folder with the videos to be processed. 
The excel files will be placed there. Currently, UNDERTEMP = 0 and frames with 
ineligible values are not recorded.


The script is processing every 2nd frame to maintain a reasonable run time. The
variable 'pos' tracks what frame we're on, you can use this variable to change which frames
will be processed.

How to use:
PART 1:
If you don't already have the tesseract executable file, follow the
instructions here: 
    https://stackoverflow.com/questions/50951955/pytesseract-tesseractnotfound-error-tesseract-is-not-installed-or-its-not-i

PART 2:    
How to use: 
    1. Change inputDir
    2. Run
    3. Draw the ROI of where the script should search for text. Press SPACE 
    or ENTER when you're done.    
"""

import pytesseract
import cv2
import matplotlib.pyplot as plt
import re
import keyboard 
import time 
import pandas as pd
import os

# set path to tesseract executeable file
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\v.jayaweera\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

#======================================FUNCTIONS===============================

def analyzeVideo(path):
    '''
    path: file path to video to be processed 
    returns: 2 arrays: temperatures and the corresponding time stamps
    '''
    global use_same_ROI, crop_coord
    
    start_time = time.time()
    cap = cv2.VideoCapture(path)

    ret, frame = cap.read()
    
    # Select ROI 
    if not use_same_ROI:
        crop_coord = cv2.selectROI("select the area", frame) 
        cv2.destroyAllWindows()
        usR = input('Use same ROI for all videos? (Y):')
        
        # update use_same_ROI
        use_same_ROI = True if usR.lower() == 'y' else False

    # variables
    temperatures = []
    time_stamps = []
    pos = 1

    while cap.isOpened():
        # get frame
        ret, frame = cap.read()
        
        # increment
        pos = pos + 1
        
        # only analyze every other frame
        if pos % 2 == 0:   
            
            # if frame is read correctly ret is True
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            else:
                cropped_frame = frame[int(crop_coord[1]):int(crop_coord[1]+crop_coord[3]),  
                                  int(crop_coord[0]):int(crop_coord[0]+crop_coord[2])]
                
                # extract text from frame using regex to find temperature
                text = pytesseract.image_to_string(cropped_frame).replace(" ", "")
                temp = re.findall(r'\d+\.\d+', text)
                
                # if there is a temp, process it
                if len(temp) > 0:
                    temp = temp[0]
                    temp = float(temp)
                    
                    # filter for misreads
                    if temp < 4000 and temp >= 1000:
                        temperatures.append(temp)
                        seconds = cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                        
                        #TODO:FIGURE OUT WHAT IS CAUSING TIMESTEP TO GO TO 0s BEFORE THE END
                        if seconds ==  0.0:
                            print(time_stamps[-1])
                            seconds = time_stamps[-1] + 1/cap.get(cv2.CAP_PROP_FPS)
                            
                        time_stamps.append(seconds)
                        
                        print("Got a frame and temp ", temp, " at time ", time_stamps[-1])
                else:
                    #process text 
                    if text == "UNTERTEMP\n":
                        temperatures.append(0)
                        seconds = cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                        time_stamps.append(seconds)
                    
            
        
        #check for keyboard presses to quit
        if keyboard.is_pressed('q'):
            break

    #add 0 to end to indcate that the experiment did end 
    temperatures.append(0)
    seconds = time_stamps[-1] + 1/cap.get(cv2.CAP_PROP_FPS)
    time_stamps.append(seconds)

    # release video
    cap.release()

    print("--- %s seconds ---" % (time.time() - start_time))
          
    return temperatures, time_stamps


def createDir(root, folderName):
    '''
    creates new folder if it doesn't exist
    returns: new folder's path
    '''
    if not os.path.exists((root + "/" + folderName)):
        os.makedirs(root + "/" + folderName)
        
    return root + "/" + folderName
         


#===============================MAIN=========================================

#Place path of folder
inputDir = "" 
outputDir = createDir(inputDir, "Results")

use_same_ROI = False
crop_coord = []

for file in os.listdir(inputDir):
    if file.split(".")[-1].lower() == "mp4":
        
        temps, timestamps = analyzeVideo(inputDir + "/" + file)

        #plot figure 
        plt.rcParams['figure.figsize'] = [12, 5] 
        plt.title("Temperature vs Time(s)")
        plt.plot(timestamps, temps, "b.-")
        plt.ylabel("Temperature")
        plt.xlabel("Time (s)")
        plt.show()
        
        
        # save data
        df = pd.DataFrame(data=temps, columns=['Temp'], index=timestamps)
        df.to_excel(outputDir + "/" + "Data_" + file + ".xlsx")


