# ComicWalkerWalker

## A spider program written to grab the whole free comics on a specific page at comic-walker.com, with friendly text UI :)
## CWW：一个用于抓取comic-walker免费漫画阅读网站的漫画的爬虫程序

## How to use

* Environment: Python 2.7

* $ python main.py
* Another way which does not require a python environment: run dist/main/main.exe if you are using Windows
* 如果您不明白上上行是什么意思，您也可以使用一种不依赖Python环境的方法启动：Windows系统下，双击dist/main/main.exe运行！

* Follow the instructions then. Comics will be saved in separate folders/directories.
* 根据提示操作即可，漫画将被保存在单独的文件夹

* You may change sys.defaultencoding if you are using os other than Windows, for example, sys.setdefaultencoding('utf-8')
* 如果您在使用非Windows系统可能需要使用sys.setdefaultencoding('utf-8')修改默认编码

* Have Fun!

* If you have any question, please push an issue.

* Pull requests are welcomed!

#### Note

The source files are written in Python2 syntax. To build the executable file under Windows, please use Pyinstaller:
```cmd
# You may install the old versions of the following tools
pip install pip==18.1
pip install pefile==2017.8.1
pip install pyinstaller==3.4

pyinstaller main.py
```
