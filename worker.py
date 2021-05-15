import json
import urllib.parse
import boto3
import numpy as np
import tempfile
from io import BytesIO
from PIL import Image
Image.MAX_IMAGE_PIXELS = 1000000000
import json
from scipy import signal

print('Loading function')

s3 = boto3.client('s3')

threshold = 127

def get_s3(bucket, key):
    bytes_buffer = BytesIO()
    s3.download_fileobj(Bucket=bucket, Key=key, Fileobj=bytes_buffer)
    return bytes_buffer

def fast_random_bool(shape):
    n = np.prod(shape)
    nb = -(-n // 8)     # ceiling division
    b = np.frombuffer(np.random.bytes(nb), np.uint8, nb)
    return np.unpackbits(b)[:n].reshape(shape).view(bool)

def load_file_as_numpy(bucket, key, threshold, noise=0):
    ext = key.split(".")[-1]
    
    if ext == "txt":
        tmp_file = get_s3(bucket, key)
        input_bytes = np.genfromtxt(tmp_file.getvalue().decode().splitlines(), delimiter=' ').astype('uint8')
        img = input_bytes.copy()
    else:
        tmp_file = get_s3(bucket, key)
        img = np.array(Image.open(tmp_file).convert('L'))
        input_bytes = (img < threshold)
    if noise:
        input_bytes = np.logical_and(input_bytes, fast_random_bool(input_bytes.shape))
    return img, input_bytes

#run the game of life on an array padded
kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
def life(arr):
    res = signal.convolve2d(arr, kernel, boundary='fill', mode='same')
    return (((arr == 1) & (res > 1) & (res < 4)) | ((arr == 0) & (res == 3))).astype('uint8')

def pad_img(img):
    new_img = np.zeros((img.shape[0]+2, img.shape[1]+2))
    new_img[1:-1, 1:-1] = img
    return new_img

def worker_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    if key.split('.')[-1] == "json" or key.split('.')[-1] == "gif":
        return "Double triggered"
    prefix = key.split('.')[0] 
    json_file = prefix + '.json'
    params = json.loads(get_s3(bucket, json_file).getvalue().decode())
    num_evolutions, scale, threshold, duration, noise = get_params(params)

    output_imgs = []
    img, numpy_img = load_file_as_numpy(bucket, key, threshold, noise)
    numpy_img = pad_img(numpy_img)
   
    gen_data = np.kron(img, np.ones((scale, scale))) 
    for i in range(int(2/(duration/1000))):
        output_imgs.append( Image.fromarray(gen_data).convert('P') ) 
    gen_data = np.kron(numpy_img[1:-1, 1:-1], np.ones((scale, scale)))
    for i in range(int(2/(duration/1000))):
        output_imgs.append(Image.fromarray( (255-gen_data*255).astype(np.uint8) ).convert('P'))
    for i in range(num_evolutions):
        numpy_img = life(numpy_img)
        gen_data = np.kron(numpy_img[1:-1, 1:-1], np.ones((scale, scale)))
        output_imgs.append(Image.fromarray( (255-gen_data*255).astype(np.uint8) ).convert('P'))
    
    write_img_to_s3(bucket, prefix, duration, output_imgs)
    return (bucket, key, "SUCCESS")

def write_img_to_s3(bucket, prefix, duration, output_imgs):
    img_buffer = BytesIO()
    output_imgs[0].save(img_buffer, save_all=True, format='GIF', append_images=output_imgs[1:], optimize=False, duration=duration, loop=0)
    img_buffer.seek(0)
    s3.put_object(Body=img_buffer, Bucket=bucket, Key=f'{prefix}.gif')

def get_params(params):
    num_evolutions = int(params['evo'])
    scale = int(params['scale'])
    threshold = int(params['thresh'])
    duration = int(params['dur'])
    noise = int(params['noise'])
    return num_evolutions,scale,threshold,duration,noise
