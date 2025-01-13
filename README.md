# easyocr_vobsub
将从dvd中的vobsub字幕ocr成srt文件

## 准备工作
- 将提取好的idx+sub字幕放入到一个文件夹内, 简单的情况可以用MakeMKV+gMKVExtract提取
- python装好torch环境, 并装好easyocr库
```python
pip install easyocr
```
- 下载[BDSup2Sub](https://github.com/mjuhasz/BDSup2Sub/wiki)放置到合适的位置

## 将idx+sub提取成xml+png
自行修改BDSup2Sub的路径位置, cd到放字幕的文件夹内
```powershell
Get-ChildItem -Filter *.idx | ForEach-Object -Parallel { mkdir $_.Basename;java -jar ..\BDSup2Sub.jar -i $_ -l zh -o "$($_.Basename)\$($_.Basename).xml" } -ThrottleLimit 16
```
## 生成srt
自行修改xml_png_ocr_to_str.py的路径位置, cd到放字幕的文件夹内
```powershell
Get-ChildItem -Directory | Select-Object -ExpandProperty Name | ForEach-Object -Parallel {python ..\xml_png_ocr_to_str.py $_} -ThrottleLimit 10
```
