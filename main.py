import requests
import json
import pandas as pd
import numpy as np
from pandas import Series,DataFrame
from numpy.random import randn,rand
import matplotlib.pyplot as plt
import time
from uploader import QiniuUploader
from nvitop import CudaDevice
import os
from config import Config

config = Config()

HOST = config.env["HOST"]
INTERVAL = config.env["INTERVAL"]
WEBHOOK_URL = config.env["WEBHOOK_URL"]["DINGDING"]

# os.environ['CUDA_VISIBLE_DEVICES'] = config.env["CUDA_VISIBLE_DEVICES"]


def getGpuInfo(): 
    data = []
    devices = CudaDevice.all()  # or `Device.cuda.all()` to use CUDA ordinal instead
    for device in devices:
        data.append([device.memory_used(), device.memory_free()])
    return data
    
def drawPicture(data):
    count = len(data)
    w_factor = 5
    h_factor = 4
    if len(data) == 1:
        rows = 1
        size = 1
    else:
        size = 2
        rows = count // size
        if rows%size:
            rows += 1
    width = w_factor * size
    height = h_factor * rows    
    fig = plt.figure(figsize=(width, height))    
    # 画出饼图
    labels=['Used','Free']
    # 每块对应的颜色
    colors=['lightskyblue','green']
    # 将每一块分割出来，值越大分割出的间隙越大
    explode=(0.05,0.05)
    
    for i,v in enumerate(data):
        # 第i+1个子图
        position = int(f"{rows}{size}{i+1}")
        ax = fig.add_subplot(position)
        ax.pie(v,
                colors=colors,
                labels=labels,
                explode=explode,
                # 数值设置为保留固定小数位的百分数
                autopct='%.2f%%', 
                # 无阴影设置
                shadow=False, 
                # 逆时针起始角度设置
                startangle=90, 
                # 数值距圆心半径背书距离
                pctdistance=0.5, 
                # 图例距圆心半径倍距离
                labeldistance =1.05 
               )
        # x,y 轴刻度一致，保证饼图为圆形
        ax.axis('equal')
        ax.legend(loc='best')
        ax.set_title(f'GPU/{i}')
    
    ts = time.time()
    dt = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime(ts))
    # replace . with _
    prefix = '_'.join(a.split('.'))
    file_name = f'images/{prefix}_gpu_status_{dt}.jpg'
    # 将饼图保存到本地，格式为jpg格式，每英寸点数分辨率设置为200
    fig.savefig(file_name, dpi=200)
    return file_name
    
def upload2qiniu(file_name):
    handle = QiniuUploader()
    url = handle.upload(file_name, file_name)
    return url
    
def send_dingding_message(webhook, content, img_url):
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
         "msgtype": "markdown",
         "markdown": {
             "title": f"{IP} GPU 使用情况",
             "text": f"{content} \n\n ![screenshot]({img_url})"
         }
    }
    response = requests.post(webhook, headers=headers, data=json.dumps(data))
    
    if response.status_code == 200:
        print('消息发送成功')
        return True
    else:
        print('消息发送失败')
        return False
        
def check_send(data, last_send):
    free = False
    for used, _ in data:
        if used <= 204800:
            free = True
            break
    if last_send == -1 and free:
        return True
    if last_send != -1 and time.time() - last_send > INTERVAL and free:
        return True
    return False
    
def main():
    use_signal = -1
    last_send = -1
    failed_time = 3
    # 替换为你自己的 Webhook 地址
    webhook_url = WEBHOOK_URL
    # 替换为你想要发送的消息内容
    message_content = f'{HOST} 有空闲可用的显卡啦! \n快点来炼丹啦！'
    # os.system("nvitop --colorful &")
    print("Watching...")
    while True:
        data = getGpuInfo()
        need_send = check_send(data, last_send)
        
        if need_send:
            last_send = time.time()
            ts = time.time()
            dt = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime(ts))  
            print(f"{message_content} ----- send time:{dt}")
            # draw and save file
            file_name = drawPicture(data)
            # upload to qiuniu cloud bucket
            url = upload2qiniu(file_name)
            # send message to dingding robot
            success = send_dingding_message(webhook_url, message_content, url)
            
            if not success:
                failed_time -= 1
                
            if failed_time < 0:
                break

if __name__ == '__main__':
    main()
