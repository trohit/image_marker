#!/usr/bin/python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# Needs 
# set modeline 
# enabled in your ~/.vimrc file.
# https://wiki.python.org/moin/Vim
##############################################################################
# App to watermark images
# works with python 3
# Made from :
# https://stackoverflow.com/questions/43309343/working-with-user-uploaded-image-in-flask
# 08-Oct-2017  Rohit
# Dependencies
# sudo apt-get install git python-opencv python-pip
##############################################################################
from flask import Flask, flash, render_template, request, session, abort
from flask import jsonify
from werkzeug.utils import secure_filename

import cv2
import sys
import errno    
import os
import hashlib
import binascii


######## config ########
INCOMING_FOLDER = 'static/uploads'
OUTGOING_FOLDER = 'static/downloads'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'JPG', 'PNG'])
CONFIG_SALT = "image marker"


########################

app = Flask(__name__)

app.config['INCOMING_FOLDER'] = INCOMING_FOLDER
app.config['OUTGOING_FOLDER'] = OUTGOING_FOLDER
app.config['SALT'] = CONFIG_SALT
# max allowed is 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# retruns last bytes of MD5 hash
def get_hash(plaintext, salt):
    plaintext = plaintext.encode('utf-8')
    salt = salt.encode('utf-8')
    dk = hashlib.pbkdf2_hmac('md5', (plaintext), (salt), 1)
    res_utf = binascii.hexlify(dk)
    res_str = res_utf.decode('utf-8')
    return res_str[-8:]

# https://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def rgb2hex(r,g,b):
    hex = "#{:02x}{:02x}{:02x}".format(r,g,b)
    return hex

def hex2rgb(hexcode):
    rgb = tuple(map(ord,hexcode[1:].decode('hex')))
    return rgb

def hex2rgb(hexcode):
    rgb = tuple(map(ord,hexcode[1:].decode('hex')))
    return rgb

def getFontScale(img, scale=1):
    height, width, channels = img.shape
    #return ((height/2000) * scale)
    return ((height/1000) * int(scale))

# colors are bgr, not rgb ( so red is (0,0,255)
# http://www.rapidtables.com/web/color/RGB_Color.htm
def getColor(x):
    
    return {
        "blue"        :(255, 0, 0, 0),
        "green"        :(0, 255, 0, 0),
        "red"        :(0, 0, 255, 0),
        "yellow"        :(0, 255, 255, 0),
        "white"        :(255, 255, 255, 0),
        "black"        :(0, 0, 0, 0)
    }.get(x,(0,0,0,0))


def watermark_img(filename, watermark_label, gen_salt, watermark_color, fontSize, thickness=1, placement = "topright", wizcolor='black'):
    src_full_path = os.path.join(app.config['INCOMING_FOLDER'], filename)
    # destination filename will be decided later
    #print("reading filename from:" + str(src_full_path))
    img = cv2.imread(src_full_path, 1)
    if img is None:
        #print("could not find image" + str(src_full_path))
        #flash("could not find image" + str(src_full_path))
        abort(406)
    height, width, channels = img.shape
    stat = dict()
    stat["w"] = width
    stat["h"] = height
    stat["c"] = channels


    #version=2
    # https://stackoverflow.com/questions/37191008/load-truetype-font-to-opencv
    # http://www.codesofinterest.com/2017/07/more-fonts-on-opencv.html
    # open cv supports limited fonts. To use Truetype fonts, will need to use Pillow.
    #enum HersheyFonts {
    #    FONT_HERSHEY_SIMPLEX        = 0, //!< normal size sans-serif font
    #    FONT_HERSHEY_PLAIN          = 1, //!< small size sans-serif font
    #    FONT_HERSHEY_DUPLEX         = 2, //!< normal size sans-serif font (more complex than FONT_HERSHEY_SIMPLEX)
    #    FONT_HERSHEY_COMPLEX        = 3, //!< normal size serif font
    #    FONT_HERSHEY_TRIPLEX        = 4, //!< normal size serif font (more complex than FONT_HERSHEY_COMPLEX)
    #    FONT_HERSHEY_COMPLEX_SMALL  = 5, //!< smaller version of FONT_HERSHEY_COMPLEX
    #    FONT_HERSHEY_SCRIPT_SIMPLEX = 6, //!< hand-writing style font
    #    FONT_HERSHEY_SCRIPT_COMPLEX = 7, //!< more complex variant of FONT_HERSHEY_SCRIPT_SIMPLEX
    #    FONT_ITALIC                 = 16 //!< flag for italic font
    #};
    font = cv2.FONT_HERSHEY_SIMPLEX
    fontScale               = getFontScale(img, fontSize)
    #print("fontScale:" + str(fontScale))
    #print("fontSize:" + str(fontSize))
    fontColor               = getColor(watermark_color)
    lineType                = 1


    # http://docs.opencv.org/modules/core/doc/drawing_functions.html#gettextsize
    # Returns bounding box and baseline -> ((width, height), baseline)
    textSize         = cv2.getTextSize(watermark_label, font, fontScale, thickness)
    label_width     = textSize[0][0]
    label_height     = textSize[0][1]

    # Write some Text x,y
    # ensue we leave enough height margin(y) for text to fit
    margin_startx = 10
    margin_starty = int(label_height+(height/60))
    margin_endx = width - 10
    margin_endy = height - 10

    topLeftCornerOfText     = (margin_startx, margin_starty)
    #bottomLeftCornerOfText  = (margin_startx, int(height - (label_height + margin_starty)))
    bottomLeftCornerOfText  = (margin_startx, int(height - (label_height)))
    topRightCornerOfText  = (margin_endx - label_width, margin_starty)
    bottomRightCornerOfText  = (margin_endx - label_width, int(height - (label_height)))

    """
	        <option selected value="topleft">TopLeft</option>
	        <option value="topright">TopRight</option>
	        <option value="bottomleft">BottomLeft</option>
	        <option value="bottomright">BottomRight</option>
	        <option value="center">Center</option>
    """       
    if placement == "topleft":
        selectedCornerOfText = topLeftCornerOfText
    elif placement == "bottomleft":    
        selectedCornerOfText = bottomLeftCornerOfText
    elif placement == "topright":    
        selectedCornerOfText = topRightCornerOfText
    elif placement == "bottomright":    
        selectedCornerOfText = bottomRightCornerOfText
        """
    elif placement == "center":    
        selectedCornerOfText = centerCornerOfText
"""

    """
    selectedCornerOfText = topLeftCornerOfText
    selectedCornerOfText = bottomLeftCornerOfText
    selectedCornerOfText = topRightCornerOfText
    selectedCornerOfText = bottomRightCornerOfText
    """
    # TODO
    #x , y , w , h
    # https://stackoverflow.com/questions/15589517/how-to-crop-an-image-in-opencv-using-python
    #best_corner     = find_brightest_corner(img,mark,margin)
    #print('best_corner:' + str(best_corner))

    #print('w x h:' + str(width) + "x" + str(height) + ":" + str(channels))
    #print('watermark info:w x h:' + str(textSize[0]))
    #print(str(textSize))
    #print('lh:' + str(label_height))
    #print('lw:' + str(label_width))

    cv2.putText(img, watermark_label,
        selectedCornerOfText,
        font,
        fontScale,
        fontColor,
        int(thickness*1),
        lineType)
    filePrefix = filename.split('.')[0]
    fileSuffix = filename.split('.')[1]

    hash_str = get_hash(filename, gen_salt)
    dst_full_path = os.path.join(app.config['OUTGOING_FOLDER'], filePrefix + '_' + hash_str + '.' + fileSuffix)
    watermarkedFile = dst_full_path
    stat['watermark_color'] = watermark_color
    stat['font'] = font
    stat['fontScale'] = fontScale
    stat['fontColor'] = fontColor
    stat['fontSize'] = fontSize
    stat['thickness'] = thickness
    stat['placement'] = placement
    stat['markedFilePath'] = watermarkedFile
    stat['markedFileName'] = str(filePrefix) + "_" + str(watermark_label) + "." + fileSuffix
    stat['label_width'] = label_width
    stat['label_height'] = label_height
    cv2.imwrite(watermarkedFile, img)
    return stat

@app.route('/')
def upload_file():
   return render_template('index.html', title="Image marker",server_ip=request.host)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploader', methods = ['GET', 'POST'])
def after_upload_file():
    # shouldnt it be app.config['INCOMING_FOLDER']
    mkdir_p(INCOMING_FOLDER)
    #mkdir_p(OUTGOING_FOLDER)

    if request.method == 'POST':
        f = request.files['file']
        if f and allowed_file(f.filename):
            s_filename = secure_filename(f.filename)
            src_full_path = os.path.join(app.config['INCOMING_FOLDER'],s_filename)
            print('Src file in :' + src_full_path) 
            f.save(src_full_path)
        else:
            #flash('Improper file')
            abort(406)
        watermark_label = request.form.get('label')
        watermark_color = request.form.get('color')
        wizcolor = request.form.get('wizcolor')
        thickness = request.form.get('thickness')
        fontSize = request.form.get('fontsize')
        placement = request.form.get('placement')

        # only to invalidate earlier cached watermark images
        client_port = request.environ.get('REMOTE_PORT')

        #print("label :" + str(watermark_label))
        #print("color :" + str(watermark_color))
        #print("wizcolor :" + str(wizcolor))
        #print("fontsize :" + str(fontSize))
        #print("placement :" + str(placement))

        gen_salt = app.config['SALT'] + str(client_port)

        stat = watermark_img(f.filename, watermark_label, gen_salt, watermark_color, fontSize, int(thickness), placement)
        _server_ip = request.host.split(":")[0]
        _client_ip = request.headers.get(request.remote_addr)
        # _client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        return render_template('result.html', 
            title="Image marker",
            pred=f.filename,
            markedFileName=stat['markedFileName'],
            markedFilePath=stat['markedFilePath'],
            watermark_color = stat['watermark_color'],
            font = stat['font'],
            fontScale = stat['fontScale'],
            fontColor=stat['fontColor'],
            fontSize=stat['fontSize'],
            thickness=stat['thickness'],
            placement=stat['placement'],
            server_ip=_server_ip,
            server_url=request.host,
            width=stat['w'],
            height=stat['h'],
            label_width = stat['label_width'],
            label_height = stat['label_height'],
            incoming_dir = app.config['INCOMING_FOLDER'],
            outgoing_dir = app.config['OUTGOING_FOLDER']
    )

@app.route("/ip", methods=["GET"])
def get_my_ip():
    #return jsonify({'ip': request.remote_addr}), 200
    return request.environ['REMOTE_ADDR']

@app.route('/<path:path>')
def static_proxy(path):
    print('this is the path')
    # send_static_file will guess the correct MIME type
    return app.send_static_file(path)
def init():
    # make dirs
    upload_dir = "static/uploads"
    download_dir = "static/downloads"
    if not os.path.exists(upload_dir):
        os.mkdirs(upload_dir)
        os.makedirs(upload_dir)
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

if __name__ == '__main__':
    init()
    app.debug = True
    app.run(host='0.0.0.0', port=5000, threaded = True)
