import serial
import time
import datetime
import pymysql
from pyfingerprint.pyfingerprint import PyFingerprint
import cv2
import os
import numpy as np
from PIL import Image

db = pymysql.connect(host="localhost", user="root", passwd="1309", db="duy")
curs= db.cursor()
#ser=serial.Serial('/dev/ttyACM1', 9600)
cam = cv2.VideoCapture(0)
cam.set(3, 640) # set video width
cam.set(4, 480) # set video height
face_detector = cv2.CascadeClassifier('/home/pi/Downloads/project/doan/finger/haarcascade_frontalface_default.xml')
path = 'dataset'
recognizer = cv2.face.LBPHFaceRecognizer_create()
def face(ids,name):
    count = 0
    face_id = ids
    os.mkdir("/home/pi/Downloads/project/doan/finger/dataset/"+str(name))
    print("\n Dang thiet lap camera.Cho camera hien thi va chup 30 anh khuon mat ...")
    while True:
    #while cam.isOpened():
        ret, img = cam.read()
        #img = cv2.flip(img, -1) # flip video image vertically
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #faces = face_detector.detectMultiScale(gray, 1.3, 5)
        faces = face_detector.detectMultiScale(gray,scaleFactor=1.2,minNeighbors=5,minSize=(20, 20))
        for (x,y,w,h) in faces:

            cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)     
            count += 1

            # Save the captured image into the datasets folder
            cv2.imwrite("/home/pi/Downloads/project/doan/finger/dataset/"+str(name)+"/" + str(face_id) + '.' + str(count) + ".jpg", gray[y:y+h,x:x+w])

            #cv2.imshow('image', img)
        cv2.imshow('image', img)
        k = cv2.waitKey(100) & 0xff # Press 'ESC' for exiting video
        if k == 27:
            break
        elif count >= 30: # Take 30 face sample and stop video
             break
def getImagesAndLabels(path):

    imagePaths = [os.path.join(path,f) for f in os.listdir(path)]     
    faceSamples=[]
    ids = []

    for imagePath in imagePaths:

        PIL_img = Image.open(imagePath).convert('L') # convert it to grayscale
        img_numpy = np.array(PIL_img,'uint8')

        id = int(os.path.split(imagePath)[-1].split(".")[0])
        faces = face_detector.detectMultiScale(img_numpy)

        for (x,y,w,h) in faces:
            faceSamples.append(img_numpy[y:y+h,x:x+w])
            ids.append(id)

    return faceSamples,ids

def fingerscan ():
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

        if ( f.verifyPassword() == False ):
            raise ValueError('The given fingerprint sensor password is wrong!')

    except Exception as e:
        print('cam bien van tay chua duoc lap dat vui long kiem tra lai!')
        print('Exception message: ' + str(e))
        exit(1)

    ## Tries to enroll new finger
    try:
        print('Dat van tay cua ban vao...')

        ## Wait that finger is read
        while ( f.readImage() == False ):
            pass

        ## Converts read image to characteristics and stores it in charbuffer 1
        f.convertImage(0x01)

    ## Checks if finger is already enrolled
        result = f.searchTemplate()
        positionNumber = result[0]

        if ( positionNumber >= 0 ):
            print('van tay da duoc luu voi id #' + str(positionNumber))
            return -1,0

        print('xin cho...')
        time.sleep(2)

        print('xac nhan lai van tay...')

        ## Wait that finger is read again
        while ( f.readImage() == False ):
            pass

        ## Converts read image to characteristics and stores it in charbuffer 2
        f.convertImage(0x02)

        ## Compares the charbuffers
        if ( f.compareCharacteristics() == 0 ):
            print('van tay khong trung')
            return -1,0
        ## Creates a template
        f.createTemplate()

        ## Saves template at new position number
        positionNumber = f.storeTemplate()
    
        print('dang ki van tay thanh cong!')
        
    
        f.loadTemplate(positionNumber, 0x01)
        char_store = str (f.downloadCharacteristics(0x01))
        char_store1= char_store.translate(str.maketrans('','', ',[]'))
    
        return positionNumber, char_store1
        
    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        exit(1)


def main ():
    #GPIO.setmode(GPIO.BCM)
    print("chao mung ban den voi he thong dang ki thong tin ca nhan")
    print("go done de thoat chuong trinh,go ok de bat dau dang ki!")
    status="" 
    status=input("nhap trang thai : ")
    while (status!='done'):
        if(status=='ok'):
            name=input ("Nhap ten    : ")
            age=input("nhap tuoi   : ")
            result=fingerscan()
            while(result[0]==-1):
                print('vui long thu lai...')
                result=fingerscan()
            if(result[0]!=-1):
                id_finger=result[0]
                print('ID cua ban: %i' %id_finger)
                print(' \n')
                templ_finger=result[1]
                face(id_finger,name)
                print("\n [da xac nhan thong tin khuon mat")
                cam.release()
                cv2.destroyAllWindows()
                print ("\n bat dau training du lieu khuon mat. Vui long doi ...")
                faces,ids = getImagesAndLabels('/home/pi/Downloads/project/doan/finger/dataset/'+str(name))
                recognizer.train(faces, np.array(ids))
                recognizer.write('/home/pi/Downloads/project/doan/finger/trainer/trainer.yml')
                print("\n {0} khuon mat da duoc train".format(len(np.unique(ids))))
                time=0
                curs.execute("CREATE TABLE %s(id int(10) primary key auto_increment,time datetime not null)" %name)
                curs.execute("INSERT INTO data (id, name,age, time) VALUES ('%i', '%s', '%s', '%s')" %(id_finger, name,age, time )) 
                db.commit()
                print("hoan tat dang ki.go ok de tiep tuc dang ki them,nhan done de thoat")
                status=input("nhap trang thai  : ")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print ("Goodbye!")