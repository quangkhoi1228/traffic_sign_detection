from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.core.files.storage import FileSystemStorage
import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import io
import random
from tensorflow.keras.models import load_model
from PIL import Image
import os
import sys
import shutil
import logging


os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'


def getCurrentPath():
    currentPythonFilePath = os.path.dirname(os.path.abspath(__file__))
    return currentPythonFilePath


def getParentPath():
    currentPythonFilePath = os.path.dirname(os.path.abspath(__file__))
    path_sep = os.path.sep
    components = currentPythonFilePath.split(path_sep)
    return path_sep.join(components[:-1])


def getProjectPath():
    return getParentPath()


def uploadFile(request):
    context = {}
    if request.method == 'POST':
        uploaded_file = request.FILES['image']
        fs = FileSystemStorage()
        projectPath = getProjectPath()
        fs.save(projectPath+'/media/upload/' +
                uploaded_file.name, uploaded_file)
        context['url'] = '/media/upload/' + uploaded_file.name
        return context


def imreadx(url):
    img = io.imread(url)
    outimg = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return outimg


def imshowx(img, title='B2DL'):
    fig_size = plt.rcParams["figure.figsize"]
    fig_size[0] = 12
    fig_size[1] = 4
    plt.rcParams["figure.figsize"] = fig_size

    plt.axis('off')
    plt.title(title)
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    plt.show()


def imshowgrayx(img, title='BD2L'):
    plt.axis('off')
    plt.title(title)
    plt.imshow(img, cmap=plt.get_cmap('gray'))
    plt.show()


def getAllFileNameInFolder(link):
    arr = os.listdir()
    return(arr)


def checkWidthHeight(cnt):
    x, y, w, h = cv2.boundingRect(cnt)
    a, b, c, d = x, y, w, h

    widthDivisionHeightRatio = w/h

    if widthDivisionHeightRatio <= 1.5 and widthDivisionHeightRatio >= 0.6:
        if w <= 30 or h <= 30:
            # print('x:'+str(x))
            # print('y:'+str(y))
            # print('w:'+str(w))
            # print('h:'+str(h))
            # print('w/h:'+str(widthDivisionHeightRatio))
            return False
        else:

            return True
    else:
        # print('x:'+str(x))
        # print('y:'+str(y))
        # print('w:'+str(w))
        # print('h:'+str(h))
        # print('w/h:'+str(widthDivisionHeightRatio))
        return False


def caculateColorPixelPercent(link, colorRangeObject):
    minRange1 = colorRangeObject['minRange1']
    maxRange1 = colorRangeObject['maxRange1']
    minRange2 = colorRangeObject['minRange2']
    maxRange2 = colorRangeObject['maxRange2']
    img = cv2.imread(link)
    size = img.size
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask_r1 = cv2.inRange(hsv, minRange1, maxRange1)
    mask_r2 = cv2.inRange(hsv, minRange2, maxRange2)
    mask_r = cv2.bitwise_or(mask_r1, mask_r2)
#     imshowgrayx(mask_r,'Mask for Red Region')
    target = cv2.bitwise_and(img, img, mask=mask_r)
    x, y, w, h = cv2.boundingRect(mask_r)
    num_brown = cv2.countNonZero(mask_r)
    # print('w'+str(w))
    # print('h'+str(h))
    if h == 0:
        return 0
    else:
        perc_brown = num_brown/float(w*h)*100
        return perc_brown


def checkColorPercent(link, colorRangeObject):
    red = {
        'minRange1': (0, 100, 100),
        'maxRange1': (10, 255, 255),
        'minRange2': (160, 100, 100),
        'maxRange2': (180, 255, 255),
    }
    white = {
        'minRange1': np.array([0, 0, 168]),
        'maxRange1': np.array([172, 111, 255]),
        'minRange2': np.array([0, 0, 168]),
        'maxRange2': np.array([172, 111, 255]),
    }

    blue = {
        'minRange1': np.array([80, 100, 100]),
        'maxRange1': np.array([160, 255, 255]),
        'minRange2': np.array([80, 100, 100]),
        'maxRange2': np.array([105, 255, 255]),
    }

    black = {
        'minRange1': (0, 0, 0),
        'maxRange1': (180, 255, 30),
        'minRange2': (0, 0, 0),
        'maxRange2': (180, 255, 30),

    }

    color = colorRangeObject['color']

    redPercent = caculateColorPixelPercent(link, red)
    whitePercent = caculateColorPixelPercent(link, white)
    bluePercent = caculateColorPixelPercent(link, blue)
    # print(redPercent)
    # print(whitePercent)

    if color == 'red':
        if redPercent >= 20 and whitePercent >= 10:
            return True
        else:
            return False

    if color == 'blue':
        print('blue'+str(bluePercent))
        print('white'+str(whitePercent))
        return True

    if color == 'black':

        return True


def removeContent(directory):
    folder = directory
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def cropAndDetectTrafficSign(context):

    try:
        currentPythonFilePath = os.getcwd()
        modelUrl = currentPythonFilePath+'/static/model/model.h5'

        saveDetectImageUrl = currentPythonFilePath+'/static/image/'
        url = currentPythonFilePath + context['url']

        imageType = url.split('.')[1]

        img = imreadx(url)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask_r1 = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
        mask_r2 = cv2.inRange(hsv, (160, 100, 100), (180, 255, 255))
        mask_r = cv2.bitwise_or(mask_r1, mask_r2)
        target = cv2.bitwise_and(img, img, mask=mask_r)
        gblur = cv2.GaussianBlur(mask_r, (9, 9), 0)
        edge_img = cv2.Canny(gblur, 30, 150)

        cv2.imwrite(saveDetectImageUrl + 'original.'+imageType, img)
        cv2.imwrite(saveDetectImageUrl + 'markrange1.'+imageType, mask_r1)
        cv2.imwrite(saveDetectImageUrl + 'markrange2.'+imageType, mask_r2)
        cv2.imwrite(saveDetectImageUrl + 'maskforredregion.'+imageType, mask_r)
        cv2.imwrite(saveDetectImageUrl + 'maskforredrigon.'+imageType, target)
        cv2.imwrite(saveDetectImageUrl + 'edgemap.'+imageType, edge_img)

        img2 = img.copy()
        itmp, cnts, hierarchy = cv2.findContours(
            edge_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(img2, cnts, -1, (0, 255, 0), 2)

        cv2.imwrite(saveDetectImageUrl +
                    'contournorestriction.'+imageType, img2)

        img2 = img.copy()
        try:
            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if(area < 1000):
                    continue
                ellipse = cv2.fitEllipse(cnt)
                cv2.ellipse(img2, ellipse, (0, 255, 0), 2)
                x, y, w, h = cv2.boundingRect(cnt)
                a, b, c, d = x, y, w, h
                cv2.rectangle(img2, (x, y), (x+w, y+h), (0, 255, 0), 3)

            cv2.imwrite(saveDetectImageUrl +
                        'contourrestrictedforlargeregion.'+imageType, img2)

            crop = img2[b:b+d, a:a+c]

            cv2.imwrite(saveDetectImageUrl + 'cropimage.'+imageType, crop)

            model = load_model(modelUrl)
            data = []
            image_from_array = Image.fromarray(crop, 'RGB')

            crop = image_from_array.resize((30, 30))

            data.append(np.array(crop))

            X_test = np.array(data)

            X_test = X_test.astype('float32')/255

            prediction = model.predict_classes(X_test)

            return prediction
        except:
            print("cannot border box")
            os.remove(saveDetectImageUrl + 'cropimage.'+imageType)
            cv2.imwrite(saveDetectImageUrl + 'cropimage.'+imageType, img)
            model = load_model(modelUrl)
            data = []
            image_from_array = Image.fromarray(img, 'RGB')
            img = image_from_array.resize((30, 30))
            data.append(np.array(img))
            X_test = np.array(data)
            X_test = X_test.astype('float32')/255
            prediction = model.predict_classes(X_test)
            return prediction
    except:
        print("Bug when model predict")
        return [10000]


def detectColorBoundingTrafficSign(context, resultContext, colorRangeObject):

    minRange1 = colorRangeObject['minRange1']
    maxRange1 = colorRangeObject['maxRange1']
    minRange2 = colorRangeObject['minRange2']
    maxRange2 = colorRangeObject['maxRange2']
    color = colorRangeObject['color']

    if 'listCropImageName' not in resultContext:
        listCropImageName = []
    else:
        listCropImageName = resultContext['listCropImageName']

    projectPath = getProjectPath()
    url = projectPath + context['url']
    img = imreadx(url)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask_r1 = cv2.inRange(hsv, minRange1, maxRange1)
    mask_r2 = cv2.inRange(hsv, minRange2, maxRange2)
    # imshowgrayx(mask_r2,'Mask Range 2')
    mask_r = cv2.bitwise_or(mask_r1, mask_r2)
    # imshowgrayx(mask_r,'Mask for Red Region')
    target = cv2.bitwise_and(img, img, mask=mask_r)
    # imshowx(target,'Mask for Red Rigon')
    gblur = cv2.GaussianBlur(mask_r, (9, 9), 0)
    edge_img = cv2.Canny(gblur, 30, 150)
    # imshowgrayx(edge_img,'edge map')
    img2 = img.copy()
    itmp, cnts, hierarchy = cv2.findContours(
        edge_img.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # cnts, hierarchy = cv2.findContours(edge_img.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

    cv2.drawContours(img2, cnts, -1, (0, 255, 0), 2)
    # imshowx(img2,'Contour - No Restriction')
    currentPythonFilePath = getProjectPath()
    directory = currentPythonFilePath+'/media/trafficsignresult'
    # removeContent(directory)
    os.chdir(directory+'/')
    # for index, cnt in enumerate(cnts):
    #     try:
    #         area = cv2.contourArea(cnt)
    #         ellipse = cv2.fitEllipse(cnt)
    #         cv2.ellipse(img2, ellipse, (0, 255, 0), 2)
    #         isAcceptWidthHeightImage = checkWidthHeight(cnt)
    #         if isAcceptWidthHeightImage == True:
    #             x, y, w, h = cv2.boundingRect(cnt)
    #             crop = img[y:y+h, x:x+w]
    # #             imshowx(crop,'Crop')
    #             filename = color+'_'+str(index)+'_crop.jpg'
    #             # print('  ')
    #             # print(filename)
    #             cv2.imwrite(filename, crop)
    #             cv2.rectangle(img2, (x, y), (x+w, y+h), (0, 255, 0), 3)

    #             isAcceptColorPercent = checkColorPercent(
    #                 filename, colorRangeObject)
    #             if isAcceptColorPercent != True:
    #                 os.remove(filename)
    #                 print('remove'+filename)
    #             else:
    #                 listCropImageName.append(filename)

    #     except NameError:
    #         print("ex")
    #         # logging.exception("message")
    #     except:
    #         print("er")
    #         logging.exception("message")

    hierarchy = hierarchy[0]
    for index, component in enumerate(zip(cnts, hierarchy)):
        currentContour = component[0]
        currentHierarchy = component[1]
        isAcceptWidthHeightImage = checkWidthHeight(currentContour)
        if isAcceptWidthHeightImage == True:
            x, y, w, h = cv2.boundingRect(currentContour)
            path = directory
            # cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
            # cv2.imwrite(os.path.join(path, color+'full.jpg'), img)
            if currentHierarchy[2] < 0:
                # these are the innermost child components
                # cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 3)
                crop = img[y:y+h, x:x+w]

            elif currentHierarchy[3] < 0:
                # these are the outermost parent components
                # cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
                crop = img[y:y+h, x:x+w]

            filename = color+'_'+str(index)+'_crop.jpg'
            # print('  ')
            # print(filename)
            cv2.imwrite(os.path.join(path, filename), crop)
            isAcceptColorPercent = checkColorPercent(
                filename, colorRangeObject)
            if isAcceptColorPercent != True:
                os.remove(filename)
                print('remove'+filename)
            else:
                listCropImageName.append(filename)

    context['listCropImageName'] = listCropImageName


def detectAllTraffic(context):
    currentPythonFilePath = getProjectPath()
    directory = currentPythonFilePath+'/media/trafficsignresult'
    removeContent(directory)
    originContext = context
    resultContext = context
    redColorRangeObject = {
        'minRange1': (0, 100, 100),
        'maxRange1': (10, 255, 255),
        'minRange2': (160, 100, 100),
        'maxRange2': (180, 255, 255),
        'color': 'red'
    }

    detectColorBoundingTrafficSign(
        context, resultContext, redColorRangeObject)

    blueColorRangeObject = {
        'minRange1': (80, 100, 100),
        'maxRange1': (160, 255, 255),
        'minRange2': (80, 100, 100),
        'maxRange2': (105, 255, 255),
        'color': 'blue'
    }

    detectColorBoundingTrafficSign(
        context, resultContext, blueColorRangeObject)

    return resultContext


def detectTrafficSign(request):
    context = uploadFile(request)
    # return context
    resultContext = detectAllTraffic(context)
    return resultContext
