# ClockIn_SUT

一个仅适用与SUT学生的自动打卡脚本, 暂不支持mac os(主要我没用过不知道把文件放哪XD)   
该脚本会自动抓取你前一天的打卡记录, 并根据前一天的打卡信息完成今天的打卡(也就是说如果你换了地方后的第一天就得自己打卡了) 
## Windows
如果你有python环境, 你可以将python脚本放在一个特定位置, 然后创建一个bat批处理文件, 内容如下(假定python存放位置为D:\\Temp):
```bat
python D:\Temp\ClockIn.py
```
然后将bat文件移动到Windows启动目录(C:\Users\你的Windows账户名\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup), 就可完成自动打卡
## Linux
不同发行版自启脚本的方式不同, 以下仅提供Arch版本:  
```

```
