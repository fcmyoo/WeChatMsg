import math
import os
import random

import numpy as np
from PIL import Image
from wordcloud import WordCloud

from app.DataBase import msg_db, micro_msg_db, micro_msg
from app.DataBase.data import get_contacts


def get_head_image(friends):
    # 保存好友头像
    if "HeadImages" not in os.listdir():
        os.mkdir('HeadImages')
    os.chdir("HeadImages")

    # 获取文件夹中所有文件的名字
    file_names = os.listdir("/app/my_test/HeadImages")

    # 创建一个空列表来存储.jpg图片文件名（不包括.jpg后缀）
    jpg_names = []
    for file_name in file_names:
        if file_name.endswith('.jpg'):
            # 分离文件名和扩展名
            name_without_extension = os.path.splitext(file_name)[0]
            # 将文件名添加到列表中
            jpg_names.append(name_without_extension)

    for friend in friends:
        if friend['UserName'] in jpg_names:
            continue
        img = friend['smallHeadImgUrl']
        # img_1 = misc_db.get_avatar_buffer(friend['UserName'])
        import requests

        # 图片的URL地址
        url = img
        if url == '':
            continue
        # 发送GET请求并获取图片内容
        response = requests.get(url)

        # 检查请求是否成功
        if response.status_code == 200:
            # 打开一个文件（以二进制写入模式），写入图片数据
            with open(friend['UserName'] + '.jpg', "wb") as f:
                print("正在下载%s.jpg" % friend["NickName"])
                f.write(response.content)
            print("图片下载成功")
        else:
            print("图片下载失败，状态码：", response.status_code)


def get_word_cloud(text, mask_path):
    """
    生成词云
    :param text: 文本
    :param mask_path: 蒙版路径
    :return: 词云
    """
    # 读取蒙版
    mask = np.array(Image.open(mask_path))
    # 生成词云
    word_cloud = WordCloud(
        font_path="C:/Windows/Fonts/simhei.ttf",
        background_color="white",
        max_words=2000,
        mask=mask,
        max_font_size=100,
        random_state=42,
    ).generate(text)
    return word_cloud


def all_head_images():
    # 把好友头像都生成在一张图片上
    x = 0  # x坐标初始为0
    y = 0  # y坐标初始为0
    images = os.listdir("HeadImages")  # 获取"HeadImages"文件夹下的所有文件
    print(len(images))  # 打印文件数量
    random.shuffle(images)  # 对文件列表进行随机重排
    new_image = Image.new('RGBA', (1200, 2350))

    # 计算每行的图片数量
    num_images = len(images)
    sqrt_num_images = int(math.sqrt(num_images))
    width = 50
    height = 50

    # 遍历所有文件
    for i in images:
        image = Image.open('HeadImages/' + i)  # 打开对应的图片文件
        image = image.resize((width, height), Image.LANCZOS)  # 调整图片大小为指定宽度
        new_image.paste(image, (x * width, y * height))  # 将图片粘贴到新图片指定位置
        x += 1  # x坐标加1
        if x == sqrt_num_images:  # 如果x坐标等于行数
            x = 0  # 重置x坐标为0
            y += 1  # y坐标加1

    # 如果最后一行不足一行，则填充空白
    while x < sqrt_num_images:
        new_image.paste(Image.new('RGBA', (width, height)), (x * width, y * height))
        x += 1

    # 如果最后一行仍然不足一行，则填充空白直到满足所需的行数
    remaining_images = len(images) % sqrt_num_images
    if remaining_images > 0:
        for _ in range(sqrt_num_images - remaining_images):
            new_image.paste(Image.new('RGBA', (width, height)), (x * width, y * height))
            x += 1
    # 保存新图片为'all.png'
    new_image.save('all.png')


micro_msg_db.init_database()

friends = []

contact_info_lists = micro_msg_db.get_contact()
for contact_info_list in contact_info_lists:
    # 用户名，昵称，类型，备注，昵称，PY名称初始值，备注PY名称初始值，联系人头像URL，小头像URL，大头像URL
    contact_info = {
        'UserName': contact_info_list[0],  # 用户名
        'Alias': contact_info_list[1],  # 昵称
        'Type': contact_info_list[2],  # 类型
        'Remark': contact_info_list[3],  # 备注
        'NickName': contact_info_list[4],  # 昵称
        'smallHeadImgUrl': contact_info_list[7]  # 小头像URL
    }
    friends.append(contact_info)

# get_HeadImage(friends)
# all_head_images()

res = msg_db.get_messages("cooer_gl")

pass
