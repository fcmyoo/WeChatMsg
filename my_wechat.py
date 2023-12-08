import base64
import codecs
import json
import math
import os
import random
import time

import jieba
import numpy
import numpy as np
import pandas
from PIL import Image
from matplotlib import pyplot as plt
from matplotlib.image import imread
from PIL import Image
from wordcloud import WordCloud, ImageColorGenerator

from app.DataBase import msg_db
from app.DataBase.db_parsing import read_img_dat, parse_xml_string, decompress_CompressContent, read_audio, \
    read_BytesExtra


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


def load_file_segment():
    """
    读取文件并分词
    :return: 分词结果
    """
    # 读取文本文件并分词
    f = codecs.open(u"Ceibayy.txt", 'r', encoding='utf-8')
    # 打开文件
    content = f.read()
    # 读取文件到content中
    f.close()
    # 关闭文件
    segment = []
    # 保存分词结果
    segs = jieba.cut(content)
    # 对整体进行分词
    for seg in segs:
        if len(seg) > 1 and seg != '\r\n':
            # 如果说分词得到的结果非单字，且不是换行符，则加入到数组中
            segment.append(seg)
    return segment


def get_words_count_dict():
    segment = load_file_segment()
    # 获得分词结果
    df = pandas.DataFrame({'segment': segment})
    words_count = df.groupby(
    ["segment"]
    )["segment"].agg(
    [("计数",numpy.size)]
    ).reset_index().sort_values(by="计数", ascending=False)
    # # 按词分组，计算每个词的个数
    # words_count = words_count.reset_index().sort_values(by="计数", ascending=False)
    # 在agg方法中直接重命名列名
    words_count = words_count.rename(columns={"计数": "count"})
    return words_count


def get_word_cloud():
    """
    生成词云
    :return: 词云
    """
    words_count = get_words_count_dict()
    bimg = imread('app/my_test/Images/wechat.jpg')
    img = Image.open('app/my_test/Images/wechat.jpg').convert('RGBA')
    bimg = bimg.astype(np.uint8)
    img_array = np.array(img)
    # 读取我们想要生成词云的模板图片
    # wordcloud = WordCloud(background_color='white', mask=bimg, font_path='simhei.ttf')
    # 获得词云对象，设定词云背景颜色及其图片和字体

    # 如果你的背景色是透明的，请用这两条语句替换上面两条
    # bimg = imread('ai.png')
    wordcloud = WordCloud(background_color=None, mode='RGBA', mask=img_array, font_path='simhei.ttf')

    words = words_count.set_index("segment").to_dict()
    # 将词语和频率转为字典
    wordcloud = wordcloud.fit_words(words["count"])
    # 将词语及频率映射到词云对象上
    bimgColors = ImageColorGenerator(bimg)
    wordcloud.generate(' '.join(words_count['segment']))
    # 生成颜色
    plt.axis("off")
    # 关闭坐标轴
    plt.imshow(wordcloud)
    # 绘色
    plt.show()


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


def load_base64_img_data(start_time, end_time, username_md5, FileStorage_path):
    """
    获取图片的base64数据
    :param start_time: 开始时间戳
    :param end_time:  结束时间戳
    :param username_md5: 用户名的md5值
    :return:
    """
    # 获取CreateTime的最大值日期
    min_time = time.strftime("%Y-%m", time.localtime(start_time))
    max_time = time.strftime("%Y-%m", time.localtime(end_time))
    img_path = os.path.join(FileStorage_path, "MsgAttach", username_md5, "Image") if FileStorage_path else ""
    if not os.path.exists(img_path):
        return {}
    # print(min_time, max_time, img_path)
    paths = []
    for root, path, files in os.walk(img_path):
        for p in path:
            if p >= min_time and p <= max_time:
                paths.append(os.path.join(root, p))
    # print(paths)
    img_md5_data = {}
    for path in paths:
        for root, path, files in os.walk(path):
            for file in files:
                if file.endswith(".dat"):
                    file_path = os.path.join(root, file)
                    fomt, md5, out_bytes = read_img_dat(file_path)
                    out_bytes = base64.b64encode(out_bytes).decode("utf-8")
                    img_md5_data[md5] = f"data:{fomt};base64,{out_bytes}"
    return img_md5_data


def load_base64_audio_data(MsgSvrID, MediaMSG_all_db_path):
    wave_data = read_audio(MsgSvrID, is_wave=True, DB_PATH=MediaMSG_all_db_path)
    if not wave_data:
        return ""
    video_base64 = base64.b64encode(wave_data).decode("utf-8")
    video_data = f"data:audio/wav;base64,{video_base64}"
    return video_data


def temp():
    friends = []

    # contact_info_lists = micro_msg_db.get_contact()
    # for contact_info_list in contact_info_lists:
    #     # 用户名，昵称，类型，备注，昵称，PY名称初始值，备注PY名称初始值，联系人头像URL，小头像URL，大头像URL
    #     contact_info = {
    #         'UserName': contact_info_list[0],  # 用户名
    #         'Alias': contact_info_list[1],  # 昵称
    #         'Type': contact_info_list[2],  # 类型
    #         'Remark': contact_info_list[3],  # 备注
    #         'NickName': contact_info_list[4],  # 昵称
    #         'smallHeadImgUrl': contact_info_list[7]  # 小头像URL
    #     }
    #     friends.append(contact_info)

    # get_HeadImage(friends)
    # all_head_images()

    # 获取文件夹中所有文件的名字
    images_path = os.listdir(r"D:\code\py\WeChatMsg\app\my_test\Images")
    media_path = os.listdir(r"D:\code\py\WeChatMsg\app\my_test\media")

    type_name_dict = {
        1: {0: "文本"},
        3: {0: "图片"},
        34: {0: "语音"},
        43: {0: "视频"},
        47: {0: "动画表情"},
        49: {0: "文本", 1: "类似文字消息而不一样的消息", 5: "卡片式链接", 6: "文件", 8: "用户上传的 GIF 表情",
             19: "合并转发的聊天记录", 33: "分享的小程序", 36: "分享的小程序", 57: "带有引用的文本消息",
             63: "视频号直播或直播回放等",
             87: "群公告", 88: "视频号直播或直播回放等", 2000: "转账消息", 2003: "赠送红包封面"},
        50: {0: "语音通话"},
        10000: {0: "系统通知", 4: "拍一拍", 8000: "系统通知"}
    }
    username = "Ceibayy"
    res = msg_db.get_messages_lee(username)
    # img_md5_data = load_base64_img_data(res[0][7], res[-1][7], username_md5, images_path)  # 获取图片的base64数据
    word_clouds_list = []
    data = []
    for row in res:
        localId, IsSender, StrContent, StrTalker, Sequence, Type, SubType, CreateTime, MsgSvrID, DisplayContent, CompressContent, BytesExtra = row
        type_name = type_name_dict.get(Type, {}).get(SubType, "未知")
        content = {"src": "", "msg": "", "style": ""}
        if IsSender != 1:
            if type_name == "文本":
                if StrContent.find("淘宝") != -1 or StrContent.find("http") != -1 or StrContent.find(
                        "https") != -1 or StrContent.find("【【") != -1:
                    continue
                word_clouds_list.append(StrContent)
        if Type == 47 and SubType == 0:  # 动画表情
            content_tmp = parse_xml_string(StrContent)
            cdnurl = content_tmp.get("emoji", {}).get("cdnurl", "")
            # md5 = content_tmp.get("emoji", {}).get("md5", "")
            if cdnurl:
                content = {"src": cdnurl, "msg": "表情", "style": "width: 100px; height: 100px;"}

        # elif Type == 49 and SubType == 57:  # 带有引用的文本消息
        #     CompressContent = CompressContent.rsplit(b'\x00', 1)[0]
        #     content["msg"] = decompress_CompressContent(CompressContent)
        #     try:
        #         content["msg"] = content["msg"].decode("utf-8")
        #         content["msg"] = parse_xml_string(content["msg"])
        #         content["msg"] = json.dumps(content["msg"], ensure_ascii=False)
        #     except Exception as e:
        #         content["msg"] = "[带有引用的文本消息]解析失败"
        # elif Type == 34 and SubType == 0:  # 语音
        #     tmp_c = parse_xml_string(StrContent)
        #     voicelength = tmp_c.get("voicemsg", {}).get("voicelength", "")
        #     transtext = tmp_c.get("voicetrans", {}).get("transtext", "")
        #     if voicelength.isdigit():
        #         voicelength = int(voicelength) / 1000
        #         voicelength = f"{voicelength:.2f}"
        #     content["msg"] = f"语音时长：{voicelength}秒\n翻译结果：{transtext}"
        #     src = load_base64_audio_data(MsgSvrID, MediaMSG_all_db_path=media_path)
        #     content["src"] = src
        elif Type == 3 and SubType == 0:  # 图片
            xml_content = parse_xml_string(StrContent)
            md5 = xml_content.get("img", {}).get("md5", "")
            if md5:
                content["src"] = md5
            else:
                content["src"] = ""
            content["msg"] = "图片"
        else:
            content["msg"] = StrContent
        talker = username
        if IsSender == 1:
            talker = "我"
        else:
            if StrTalker.endswith("@chatroom"):
                bytes_extra = read_BytesExtra(BytesExtra)
                if bytes_extra:
                    try:
                        matched_string = bytes_extra['3'][0]['2'].decode('utf-8', errors='ignore')
                        talker_dicts = list(filter(lambda x: x["username"] == matched_string, []))
                        if len(talker_dicts) > 0:
                            talker_dict = talker_dicts[0]
                            room_username = talker_dict.get("username", "")
                            room_nickname = talker_dict.get("nickname", "")
                            room_remark = talker_dict.get("remark", "")
                            talker = room_remark if room_remark else room_nickname if room_nickname else room_username
                        else:
                            talker = matched_string
                    except:
                        pass

        row_data = {"MsgSvrID": MsgSvrID, "type_name": type_name, "is_sender": IsSender, "talker": talker,
                    "content": content, "CreateTime": CreateTime}
        data.append(row_data)

    with open("Ceibayy.txt", "w", encoding="utf-8") as file:
        for row in word_clouds_list:
            file.write(row + "\n")  # 将文本内容写入文件，并在每行末尾添加换行符
    pass

# temp()
get_word_cloud()
pass
