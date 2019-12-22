import serial
import time
from datetime import datetime
import pymysql
from pyfingerprint.pyfingerprint import PyFingerprint
import hashlib
import cv2
import os
import numpy as np
from PIL import Image

db = pymysql.connect(host="localhost", user="root", passwd="1309", db="duy")
curs= db.cursor()
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('/home/pi/Downloads/project/doan/finger/trainer/trainer.yml')
cascadePath = "/home/pi/Downloads/project/doan/finger/haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)
font = cv2.FONT_HERSHEY_SIMPLEX

# Initialize and start realtime video capture
cam = cv2.VideoCapture(0)
cam.set(3, 640) # set video widht
cam.set(4, 480) # set video height
# Define min window size to be recognized as a face
minW = 0.1*cam.get(3)
minH = 0.1*cam.get(4)
def fingersearch():
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

        if ( f.verifyPassword() == False ):
            raise ValueError('The given fingerprint sensor password is wrong!')

    except Exception as e:
        print('cam bien chua duoc cai dat kiem tra lai!')
        print('Exception message: ' + str(e))
        exit(1)

    ## Gets some sensor information
    print('so ID da su dung: ' + str(f.getTemplateCount()) +'/'+ str(f.getStorageCapacity()))

    ## Tries to search the finger and calculate hash
    try:
        print('Dang cho van tay...')

        ## Wait that finger is read
        while ( f.readImage() == False ):
            pass

        ## Converts read image to characteristics and stores it in charbuffer 1
        f.convertImage(0x01)

        ## Searchs template
        result = f.searchTemplate()

        positionNumber = result[0]
        accuracyScore = result[1]

        if ( positionNumber == -1 ):
            print('khong tim thay van tay!')
            return -1
        else:
            print('tim thay van tay ID = #' + str(positionNumber))
            #print('The accuracy score is: ' + str(accuracyScore))

        ## OPTIONAL stuff
        ##

        ## Loads the found template to charbuffer 1
        f.loadTemplate(positionNumber, 0x01)

        ## Downloads the characteristics of template loaded in charbuffer 1
        characterics = str(f.downloadCharacteristics(0x01)).encode('utf-8')

        ## Hashes characteristics of template
        #print('SHA-2 hash of template: ' + hashlib.sha256(characterics).hexdigest())
        return positionNumber
    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        exit(1)
def facesearch():
    while True:
        ret, img =cam.read()
        #img = cv2.flip(img, -1) # Flip vertically
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale( 
            gray,
            scaleFactor = 1.2,
            minNeighbors = 5,
            minSize = (int(minW), int(minH)),
           )

        for(x,y,w,h) in faces:

            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
            id, confidence = recognizer.predict(gray[y:y+h,x:x+w])
            curs.execute("SELECT name from data where id=%s" %(id))
            data1=curs.fetchone()
            name=data1[0]
            # Check if confidence is less them 100 ==> "0" is perfect match 
            if (confidence < 100):
                ids =name
                confidence = "  {0}%".format(round(100 - confidence))
                cv2.putText(img, str(ids), (x+5,y-5), font, 1, (255,255,255), 2)
                cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)
                times=time.strftime('%Y-%m-%d %H:%M:%S')
                curs.execute("INSERT into %s(time)values('%s')" %(name,times))
                db.commit()
                cam.release()
                cv2.destroyAllWindows()
                return name,id
            else:
                ids = "unknown"
                confidence = "  {0}%".format(round(100 - confidence))
                cv2.putText(img, str(ids), (x+5,y-5), font, 1, (255,255,255), 2)
                cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1) 
        
        cv2.imshow('camera',img) 

        k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
        if (k == 27):
            cam.release()
            cv2.destroyAllWindows()
def main():
    while(True):
        chosse=input("vui long chon cach cham cong:\n1.van tay\n2.khuon mat\n")
        if(chosse=='1'):
            ids=fingersearch()
            while(ids==-1):
                print("vui long thu lai")
                ids=fingersearch()
            if(ids!=-1):
                curs.execute("SELECT name from data where id=%s" %(ids))
                data=curs.fetchone()
                name=data[0]
                print("XIN CHAO "+str(name))
                print("diem danh thanh cong")
                times=time.strftime('%Y-%m-%d %H:%M:%S')
                curs.execute("INSERT into %s(time)VALUES('%s')" %(str(name),str(times)))
                db.commit()
        elif(chosse=='2'):
            name,ids=facesearch()
            print("tim thay khuon mat ID= #"+str(ids))
            print("XIN CHAO "+str(name))
            print("diem danh thanh cong")
        else:
            print("lua chon khong dung")
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print ("Goodbye!")