import xml.etree.ElementTree as ET
import os
import sys
import easyocr

def vobsub_xml_png_to_srt(xml_file, png_dir, output_srt):
    """
    将 XML+PNG 格式的 VobSub 字幕转换为 SRT 字幕。

    Args:
        xml_file: XML 文件的路径。
        png_dir: PNG 图片所在的目录路径。
        output_srt: 输出 SRT 文件的路径。
    """

    # 创建 reader 对象，指定要识别的语言
    reader = easyocr.Reader(['ch_tra']) 

    # 解析 XML 文件
    tree = ET.parse(xml_file)
    root = tree.getroot()

    with open(output_srt, 'w', encoding='utf-8') as f:
        for i, event in enumerate(root.findall('Events/Event')):
            start_time = event.get('InTC')
            end_time = event.get('OutTC')
            img_filename = event.find('Graphic').text
            img_path = os.path.join(png_dir, img_filename)

            # 使用 EasyOCR 识别图片
            result = reader.readtext(img_path)

            # 拼接识别结果
            text = '\n'.join([r[1] for r in result])

            # 将时间转换为 SRT 格式
            start_time = convert_time(start_time)
            end_time = convert_time(end_time)

            # 写入 SRT 文件
            f.write(f'{i+1}\n')
            f.write(f'{start_time} --> {end_time}\n')
            f.write(f'{text}\n\n')

def convert_time(time, fps=29.97):
    """将 XML 中的时间格式转换为 SRT 格式

    XML 格式: HH:MM:SS:FF (帧)
    SRT 格式: HH:MM:SS,mmm (毫秒)
    """
    times = time.split(':')
    hours = int(times[0])
    minutes = int(times[1])
    seconds = int(times[2])
    frames = int(times[3])

    # 将帧转换为毫秒
    milliseconds = int(frames * 1000 / fps)

    return f'{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}'

# 示例用法
name = sys.argv[1]
print(name)
xml_file = f'{name}/{name}.xml'  # 替换为你的 XML 文件路径
png_dir = name  # 替换为你的 PNG 文件夹路径
output_srt = f'{name}.srt'  # 替换为你的输出 SRT 文件路径

vobsub_xml_png_to_srt(xml_file, png_dir, output_srt)
