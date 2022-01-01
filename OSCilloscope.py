# This Python file uses the following encoding: utf-8

import os
import PySide2
dirname = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(dirname, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from numpy import *
import random
from matplotlib.figure import Figure
from matplotlib import pyplot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
matplotlib.use("Qt5Agg")  # 声明使用QT5
from PyQt5.QtWidgets import QApplication,QMainWindow,QGridLayout,QSizePolicy,qApp,QDialog,QLabel,QAction
#import win32ui
#import win32api
from PyQt5 import QtGui,QtCore
import sys
import MainWindow
import MSV
import OSCimage

#全局变量
X1=0.0                                  #坐标轴原点
dX=20.0                                 #坐标轴宽度
C=0.0                                   #图像纵向平移数
A=1.0                                   #幅值放缩倍数
T1=0                                    #t1滑条初始位置
T2=100                                  #t2滑条初始位置
U=331.45                                #标准状况下的声速m/s

SineWave="sin(x)"                       #正弦波表达式
xsinWave="sin(x)*x"                     #x*sin(x)
SquareWave="where(x%4.0<2,-1.0,1.0)"    #方波
TriangleWave="where(x%8<=4,x%8,8-x%8)"  #三角波
SawToothWave="where(x%6<6,x%4,0)"       #锯齿波
#信号类
class VirtualSignal():
    #信号类构造函数
    def __init__(self,a,c,x):
        self.signal=[0,0]               #信号原数据
        self.a=a                        #幅值
        self.c=c                        #偏移
        self.x=x                        #横坐标
        self.y=0                        #纵坐标
    #重置
    def reset(self):
        self.signal=[0,0]       
        self.a=A                
        self.c=C                
        self.x=[X1,820]
        self.y=0                
    #将原数据进行变换,刷新要输出的数据
    def newSigData(self):                                                   
        self.y=[(i*self.a+self.c+random.uniform(-0.3,0.3)) for i in self.signal]                     #y=a*signal+c每个点加随机数，形成信号波动

class SoundWave(VirtualSignal):                            #声波类
    def __init__(self):
        super(VirtualSignal,self).__init__()
        self.T=random.uniform(15,35)                       #生成随机室温，室温影响声速，u=U*sqrt(T/T0)（绝对温度）
        self.u=U*sqrt((self.T+273.15)/273.15)
        self.f=25
        self.x=50
        self.t=linspace(0,820,50000)
    def newData(self,f,x0):
        A1=2
        a=12.69                                            #声波振幅衰减系数a=0.1269dB/mm=12.69B/m（参考值）
        A2=A1*exp(-a*x0/1000)                              #考虑声波随距离的衰减
        self.f=f
        self.x=x0
        self.signal=A1*cos(2*pi*self.f*(self.t-self.x/(1000*self.u)))+A2*cos(2*pi*self.f*(self.t+self.x/(1000*self.u)))#入射波和反射波叠加，入射波是t-x/u,反射波是t+x/u

#定义画布类，继承FigureCanvasQTAgg
class MyFigure(FigureCanvas):
    def __init__(self,parent=None):
        fig=Figure(figsize=(77,50),facecolor='#8c8c8c',dpi=100) #定义画布
        super(MyFigure,self).__init__(fig)                      #继承父类
        self.axes=fig.add_subplot(111)                          #定义图像
        self.axes.set(facecolor='#ffffff')
#图像子类，继承画布类
class MyPicture(MyFigure):
    #构造函数
    def __init__(self,x1,dx,c,a):                                           
        super(MyPicture,self).__init__()
        self.x1=x1                                              #初始化坐标
        self.dx=dx                                              #初始化坐标轴大小
        self.x2=self.x1+self.dx
        CH1=VirtualSignal(a,c,[self.x1,820])                    #信号类对象，信道1
        CH2=VirtualSignal(a,c,[self.x1,820])                    #信号类对象，信道2
        self.CH=[CH1,CH2]
        self.xindao=0                                           #信道序号
        self.t1=T1                                              #t1滑条初始位置
        self.t2=T2                                              #t2滑条初始位置
        self.update_figure()                                    #更新画布
    def changex(self,x11):                                      #横向滑动坐标轴
        if self.x2<=820:                                        #最大滑动到820
            self.x1=x11
        else:
            self.x1=X1
        self.x2=self.x1+self.dx
    def changeTimer(self,xx):                                   #放缩坐标轴
        if self.dx<=500:                                        #最大放缩520
            self.dx=20+xx
        else:
            self.dx=20
        self.x2=self.x1+self.dx  
    def changeC(self,cc):                                       #更改偏移量
        if self.CH[self.xindao].c<=10:                          #对单个信道操作，最大偏移5
            self.CH[self.xindao].c=cc/10
        else:
            self.CH[self.xindao].c=C
    def changeA(self,aa):                                       #更改幅值
        if self.CH[self.xindao].a<=6:                           #对单个信道操作
            self.CH[self.xindao].a=A+aa
        else:
            self.CH[self.xindao].a=A
    def t1SlideChange(self,t1):                                 #操作时间滑条t1
        self.t1=t1
    def t2SlideChange(self,t2):                                 #操作时间滑条t2
        self.t2=t2
    def update_figure(self):                                    #更新画布
        self.CH[0].newSigData()                                 #每次画图前先刷新信号的y坐标
        self.CH[1].newSigData()
        self.axes.cla()                                         #清除旧的图像
        self.axes.grid(linestyle=':',color='#000000')
        self.axes.set_yticklabels('')                           #不显示刻度值
        self.axes.set_xticklabels('')
        self.axes.axis([self.x1,self.x2,-10,10])                #设置坐标范围
        self.axes.plot(self.CH[0].x,self.CH[0].y,'#0d00ff',self.CH[1].x,self.CH[1].y,'orange',[self.t1/100*self.dx+self.x1,self.t1/100*self.dx+self.x1],[-10,10],'#7FFF00',[self.t2/100*self.dx+self.x1,self.t2/100*self.dx+self.x1],[-10,10],'#7FFF00')
        self.draw()                                             #画图

class MSVdlg(QMainWindow,MSV.Ui_Dialog,QDialog):
    _signal=QtCore.pyqtSignal(ndarray,ndarray)                  #连接主窗口信号
    def __init__(self):
        super(QDialog,self).__init__()
        self.setupUi(self)
        self.sig=SoundWave()
        self.setWindowTitle('声速测量实验')
        self.label_5.setText("室温T={:.1f}℃".format(self.sig.T))
        self.Tips.setText('请在示波器界面选择好信道，再按下Start按钮开始实验')
        self.spinBox.valueChanged.connect(self.newFluency_and_Place)
        self.doubleSpinBox.valueChanged.connect(self.newFluency_and_Place)
        self.pushButton_2.clicked.connect(self.startFunc)
    def newFluency_and_Place(self):                            #更新实验数据
        f=self.spinBox.value()
        x0=self.doubleSpinBox.value()
        self.sig.newData(f,x0)
        self.receivor.move(int(270+(x0-50.0)/300.0*(340-270)),220)
        self._signal.emit(self.sig.signal,self.sig.t)          #将数据发送给主窗口
    def startFunc(self):
        self.newFluency_and_Place()
        self.pushButton_2.setEnabled(False)                    #点击开始后按钮被禁用
        self.Tips.setText('实验中如遇到困难，\n请点击help参考实验指导书')

#定义窗口类，主窗口。继承QMainWindow,MainWindowFirst
class MainWin(QMainWindow,MainWindow.Ui_MainWindow):
    def __init__(self):#构造函数
        super(MainWin,self).__init__()
        self.setupUi(self)
        self.MSVdlg=MSVdlg()
        self.setWindowTitle("简易示波器")
        self.F=MyPicture(X1,dX,C,A)                                         #创建主窗口类下的Picture对象，窗口被创建时创建一个Picture对象
        self.setWindowIcon(QtGui.QIcon(":/image/Img/OSC.ico"))
        self.gridlayout = QGridLayout(self.groupBox_2)                      # 继承容器groupBox_2
        self.gridlayout.addWidget(self.F,0,1)                               #在groupBox_2中添加Picture对象
        self.label_10.setText("%.2f"%(self.F.t1/100*self.F.dx+self.F.x1))   #t1滑条初始化
        self.label_7.setText("%.2f"%(self.F.t2/100*self.F.dx+self.F.x1))    #t2滑条初始化
        self.pushButton_3.clicked.connect(self.ResetKey)                    #reset键
        self.horizontalSlider_3.sliderMoved.connect(self.t1_slide)          #t1滑条信号
        self.horizontalSlider_4.sliderMoved.connect(self.t2_slide)          #t2滑条信号
        self.dial_6.valueChanged.connect(self.TimerMove)                    #时间轴旋钮信号
        self.lineEdit.setPlaceholderText("在这里输入自定义函数")
        self.dial_5.valueChanged.connect(self.AmpliMove)                    #幅值旋钮信号
        self.dial_7.valueChanged.connect(self.XaxisMove)                    #X平移旋钮信号
        self.dial_4.valueChanged.connect(self.YaxisMove)                    #Y平移旋钮信号
        self.actionExit_2.triggered.connect(qApp.quit)                      #菜单栏退出信号
        self.actionSin_x.triggered.connect(self.actSin_x)                   #选择正弦波
        self.actionxsin_x.triggered.connect(self.actxsin_x)                 #选择xsin(x)波
        self.actionSquare_Wave.triggered.connect(self.actSquareWave)        #选择方波
        self.actionTriangle_Wave.triggered.connect(self.actTriangleWave)    #选择三角波
        self.actionSawtooth_Wave.triggered.connect(self.actsawtoothWave)    #选择锯齿波
        self.actionPreview.triggered.connect(self.importfile)               #导入文件
        self.actionMSoundV.triggered.connect(self.MeasureSoundV)            #声速实验实验
        self.pushButton.clicked.connect(self.actMyselfWaveInput)            #确认输入的公式
        self.radioButton_3.clicked.connect(self.CH1Pross)                   #信道1信号
        self.radioButton_4.clicked.connect(self.CH2Pross)                   #信道2信号
    def ResetKey(self):                                                     #复位键实现方法
        self.F.CH[0].reset()                                                #信道1复位
        self.F.CH[1].reset()                                                #信道2复位
        self.F.x1=X1                                                        #图像坐标原点复位
        self.F.dx=dX                                                        #图像坐标宽度复位
        self.F.t1SlideChange(0)                                             #t1滑条复位
        self.F.t2SlideChange(100)                                           #t2滑条复位
        self.F.update_figure()                                              #更新图像
        self.lineEdit.setPlaceholderText('在这里输入自定义函数')                        #输入框复位
        self.horizontalSlider_3.setValue(0)                                 #t1滑条位置复位
        self.horizontalSlider_4.setValue(100)                               #t1滑条位置复位
        self.label_10.setText("%.2f"%(self.F.t1/100*self.F.dx+self.F.x1))   
        self.label_7.setText("%.2f"%(self.F.t2/100*self.F.dx+self.F.x1))
        self.dial_4.setValue(100)                                           #纵向平移复位
        self.dial_5.setValue(20)                                            #幅值复位
        self.dial_6.setValue(20)                                            #时间轴复位
        self.dial_7.setValue(0)                                             #横向平移复位
    def XaxisMove(self,value):                                              #x平移旋钮方法
        self.F.changex(value)
        self.F.update_figure()
    def YaxisMove(self,value):                                              #y轴旋钮方法
        self.F.changeC(value-100)
        self.F.update_figure()
    def AmpliMove(self,value):                                              #幅值旋钮方法
        self.F.changeA((value-19)/20)
        self.F.update_figure()
    def TimerMove(self,value):                                              #时间轴旋钮方法
        self.F.changeTimer(value-19)
        self.label_10.setText("%.2f"%(self.F.t1/100*self.F.dx+self.F.x1))
        self.label_7.setText("%.2f"%(self.F.t2/100*self.F.dx+self.F.x1))
        self.F.update_figure()
    def t1_slide(self,value):                                               #t1滑条方法
        self.F.t1SlideChange(self.horizontalSlider_3.value())
        self.F.update_figure()
        self.label_10.setText("%.2f"%(self.F.t1/100*self.F.dx+self.F.x1))
    def t2_slide(self,value):                                               #t2滑条方法
        self.F.t2SlideChange(self.horizontalSlider_4.value())
        self.F.update_figure()
        self.label_7.setText("%.2f"%(self.F.t2/100*self.F.dx+self.F.x1))
    def CH1Pross(self):                                                     #信道1方法
        self.F.xindao=0
        self.label_9.setText('1')
    def CH2Pross(self):                                                     #信道2方法
        self.F.xindao=1
        self.label_9.setText('2')
    def actSin_x(self):                                                     #设置信道波形——正弦波sin(x)
        x=linspace(0,820,20000)                                             #生成横坐标数据
        self.F.CH[self.F.xindao].signal=eval(SineWave)                      #生成纵坐标原数据
        self.F.CH[self.F.xindao].x=x                                        #将纵坐标保存至信号类
        self.F.update_figure()
    def actxsin_x(self):                                                    #设置信道波形x*sin(x)
        x=linspace(0,820,20000)
        self.F.CH[self.F.xindao].signal=eval(xsinWave)
        self.F.CH[self.F.xindao].x=x
        self.F.update_figure()
    def actSquareWave(self):                                                #设置信号方波
        x=linspace(0,820,20000)                                             
        self.F.CH[self.F.xindao].signal=eval(SquareWave)
        self.F.CH[self.F.xindao].x=x
        self.F.update_figure()
    def actTriangleWave(self):                                              #设置信号三角波
        x=linspace(0,820,20000)
        self.F.CH[self.F.xindao].signal=eval(TriangleWave)
        self.F.CH[self.F.xindao].x=x
        self.F.update_figure()
    def actsawtoothWave(self):                                              #设置信号锯齿波
        x=linspace(0,820,20000)
        self.F.CH[self.F.xindao].signal=eval(SawToothWave)
        self.F.CH[self.F.xindao].x=x
        self.F.update_figure()
    def actMyselfWaveInput(self):                                           #输入信号转换
        try:
            text=self.lineEdit.text()                                       #获取输入的公式
            x=linspace(0,820,20000)                                         #生成横坐标
            self.F.CH[self.F.xindao].signal=eval(text)                      #生成纵坐标原数据
            self.F.CH[self.F.xindao].x=x
            self.F.update_figure()
        except:
            win32api.MessageBox(0,"输入的函数格式不正确或函数有误，请重新输入")
    def importfile(self):                                                   #文件流数据
        try:
            dlg=win32ui.CreateFileDialog(1)                                 #弹出文件系统
            dlg.SetOFNInitialDir('C:/')                                     #文件系统初始位置
            dlg.DoModal()
            filename=dlg.GetPathName()                                      #获取文件路径
            datax=list()                                                    #初始化横坐标列表
            datay=list()                                                    #初始化纵坐标列表
            with open(filename,'r',encoding='utf8') as fdata:               #打开文件
                for line in fdata.readlines():                              
                    l=line.replace('\n','')                                 #数据格式化
                    l=l.replace(';','')
                    l=l.replace('；','')
                    l=l.replace('，',',')
                    l=l.replace(' ',',')
                    l=l.replace('  ',',')
                    l=l.replace('   ',',')
                    l=l.replace(',,',',')
                    l=l.replace(',,,',',')
                    l=l.replace(', ',',')
                    d=l.split(',')                                          #英文逗号作分隔符
                    datax.append(eval(d[0]))                                #类型转换
                    datay.append(eval(d[1]))
            self.F.CH[self.F.xindao].x=datax                                #将选定信道的横坐标赋值
            self.F.CH[self.F.xindao].signal=datay                           #将选定信道纵坐标原数据幅值
            self.F.update_figure()                                          #刷新（包括是生成新的纵坐标，画图）
        except:
            win32api.MessageBox(0,"选择的文件有误，请重新选择！")             #错误处理
    def MeasureSoundV(self):                                                #打开实验窗口
        self.MSVdlg.show()
        self.MSVdlg._signal.connect(self.getsigData)                        #连接子窗口信号
    def getsigData(self,sig,t):                                             #获取频率和位置，画图
        self.F.CH[self.F.xindao].signal=sig
        self.F.CH[self.F.xindao].x=t
        self.F.update_figure()

#主函数
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui=MainWin()                #创建主窗口类对象
    ui.show()                   #主窗口显示
    sys.exit(app.exec_())
