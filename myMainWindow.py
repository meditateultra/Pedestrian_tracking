import os
import shutil
import sys
import time
import threading
import yaml
from PyQt5 import QtGui
from PyQt5.QtWidgets import  QApplication, QMainWindow,QFileDialog

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QUrl, QDir, QFileInfo, Qt, QEvent, QTimer, QDateTime


from PyQt5.QtGui import QIcon,QKeyEvent,QMouseEvent


from PyQt5.QtMultimedia import QMediaContent,QMediaPlayer

import getVideo
from Ui_MainWindow import Ui_MainWindow

class QmyMainWindow(QMainWindow): 

   # 视频处理完成信号
   finished = pyqtSignal(str)
   run_time_start=0.0
   start_time=None
   time_thread_end=False
   thread_video=None
   conf_val=0.3
   def __init__(self, parent=None):
      super().__init__(parent)   #调用父类构造函数，创建窗体
      self.ui=Ui_MainWindow()    #创建UI对象
      self.ui.setupUi(self)      #构造UI界面
      self.duration = 10

      self.player = QMediaPlayer(self)    #创建视频播放器
      self.player.setNotifyInterval(10) #信息更新周期, ms
      self.player.setVideoOutput(self.ui.videoWidget) #视频显示组件

      self.ui.videoWidget.installEventFilter(self)    #事件过滤器

      self.__duration=""
      self.__curPos=""
      
      self.player.stateChanged.connect(self.do_stateChanged)
      self.player.positionChanged.connect(self.do_positionChanged)
      self.player.durationChanged.connect(self.do_durationChanged)

      self.ui.label_4.setText('置信度：'+str(self.conf_val))
      self.ui.conf_slider.setValue(self.conf_val * 100)
      self.ui.conf_slider.valueChanged.connect(self.setConf)

      timer = QTimer(self)
      timer.timeout.connect(self.time_update)
      timer.start()


##  ==============自定义功能函数========================
   def conf_change(self):
      with open('configs/mot/fairmot/_base_/fairmot_dla34.yml','r') as f:
         doc=yaml.safe_load(f)
      doc['JDETracker']['det_thresh']=self.conf_val
      with open('configs/mot/fairmot/_base_/fairmot_dla34.yml', 'w') as f:
         yaml.safe_dump(doc, f, default_flow_style=False)

   def mot(self,fileName):
      self.conf_change()
      cmd_str = 'python tools/infer_mot.py -c configs/mot/fairmot/fairmot_dla34_30e_1088x608.yml \
                                  -o weights=checkpoints/model_final \
                                  --video_file={} --save_videos '.format(fileName)
      os.system(cmd_str)
      seq = fileName.split('/')[-1].split('.')[0]
      pic_path = 'output/mot_outputs/' + seq
      getVideo.images_to_video(pic_path)
      video_file = os.getcwd() + '/' + pic_path + '/' + seq + '_mot.mp4'
      with open('output/mot_results/'+seq+'.txt') as f:
         self.data = []
         for line in f.readlines():
            self.data.append(line.strip())
      return video_file

   def time_update(self):
      if self.time_thread_end:
         datetime = QDateTime.currentDateTime().toTime_t()
         second=datetime-self.start_time
         self.ui.label_2.setText('用时：'+str(second))

   def clearFile(self):
      if os.path.exists('output'):
         shutil.rmtree('output')


##  ==============event处理函数==========================
   def closeEvent(self,event):  #窗体关闭时
   # 窗口关闭时不能自动停止播放，需手动停止
      if (self.player.state()==QMediaPlayer.PlayingState):
         self.player.stop()
      #退出前清空本地缓存
      # self.clearFile()

   def eventFilter(self,watched, event):     ##事件过滤器
      if (watched!=self.ui.videoWidget):
         return super().eventFilter(watched,event)

      #鼠标左键按下时，暂停或继续播放
      if event.type()==QEvent.MouseButtonPress:
         if event.button()==Qt.LeftButton:
            if self.player.state()==QMediaPlayer.PlayingState:
               self.player.pause()
            else:
               self.player.play()

      #全屏状态时，按ESC键退出全屏
      if event.type()==QEvent.KeyPress:
         if event.key() == Qt.Key_Escape:
            if self.ui.videoWidget.isFullScreen():
               self.ui.videoWidget.setFullScreen(False)
        
      return super().eventFilter(watched,event)


   # 视频处理，视频处理完成后发送finished信号
   def work(self, fileName):
      # 在这里写处理视频的逻辑,并将处理后的视频全路径赋值给tackedFileName
      # time.sleep(10)
      tackledFileName = self.mot(fileName)
      self.finished.emit(tackledFileName)

   def display(self, fileName):
      fileInfo=QFileInfo(fileName)
      baseName=fileInfo.fileName()
##      baseName=os.path.basename(fileName)
      self.ui.LabCurMedia.setText(baseName)

      # curPath=fileInfo.absolutePath()
      # QDir.setCurrent(curPath)   #重设当前目录
      media=QMediaContent(QUrl.fromLocalFile(fileName))
      self.player.setMedia(media)   #设置播放文件
      self.player.play()
      self.player.pause()
      self.time_thread_end=False



   def execute(self, fileName):
      # 将视频处理完成的信号finished与播放视频display连接
      # 这样在视频处理完成后会调用display方法
      self.finished.connect(self.display)
      # 开启视频处理的线程
      self.thread_video = threading.Thread(target=self.work, args=(fileName,))
      self.thread_video.start()
        
##  ==========由connectSlotsByName()自动连接的槽函数============        
   @pyqtSlot()    ##打开文件
   def on_btnOpen_clicked(self):
      self.ui.label_2.setText('用时：0')
      self.player.stop()
      curPath=QDir.currentPath()  #获取系统当前目录
      title="选择视频文件" 
      filt="视频文件(*.wmv *.avi *mp4 *flv);;所有文件(*.*)"
      fileName,flt=QFileDialog.getOpenFileName(self,title,curPath,filt)
      if (fileName==""):
         return
      self.run_time_start=time.time()
      self.time_thread_end=True
      self.start_time=QDateTime.currentDateTime().toTime_t()
      self.execute(fileName)
      

   @pyqtSlot()    ##播放
   def on_btnPlay_clicked(self):
      self.player.play()

   @pyqtSlot()    ##暂停
   def on_btnPause_clicked(self):
      self.player.pause()

   @pyqtSlot()    ##停止
   def on_btnStop_clicked(self):
      self.player.stop()

   @pyqtSlot()    ##全屏
   def on_btnFullScreen_clicked(self):
      self.ui.videoWidget.setFullScreen(True)

   @pyqtSlot()    ##静音按钮
   def on_btnSound_clicked(self):
      mute=self.player.isMuted()
      self.player.setMuted(not mute)
      if mute:
         self.ui.btnSound.setIcon(QIcon(":/icons/images/volumn.bmp"))
      else:
         self.ui.btnSound.setIcon(QIcon(":/icons/images/mute.bmp"))
         
   @pyqtSlot(int)  ##音量调节
   def on_sliderVolumn_valueChanged(self,value):
      self.player.setVolume(value)

   @pyqtSlot(int)  ##播放进度调节
   def on_sliderPosition_valueChanged(self,value):
      self.player.setPosition(value)
      
        
##  =============自定义槽函数===============================        

   def do_stateChanged(self,state):    ##状态变化
      isPlaying= (state==QMediaPlayer.PlayingState)
      
      self.ui.btnPlay.setEnabled(not isPlaying)
      self.ui.btnPause.setEnabled(isPlaying)
      self.ui.btnStop.setEnabled(isPlaying)

   def do_durationChanged(self,duration):    ##文件长度变化
      self.ui.sliderPosition.setMaximum(duration)
      self.duration = duration
      secs=duration/1000   #秒
      mins=secs/60         #分钟
      secs=secs % 60       #余数秒
      self.__duration="%d:%d"%(mins,secs)
      self.ui.LabRatio.setText(self.__curPos+"/"+self.__duration)

   def do_positionChanged(self,position): ##当前播放位置变化
      if (self.ui.sliderPosition.isSliderDown()):
         return  #如果正在拖动滑条，退出
      # print(self.data)
      self.ui.label_3.setText('目标数目：' + self.data[min(round(position / self.duration * len(self.data)) + 1, len(self.data)) - 1])
      self.ui.sliderPosition.setSliderPosition(position)
      secs=position/1000   #秒
      mins=secs/60         #分钟
      secs=secs % 60       #余数秒
      self.__curPos="%d:%d"%(mins,secs)
      self.ui.LabRatio.setText(self.__curPos+"/"+self.__duration)

   def setConf(self,v):
      self.conf_val=v/100
      text=str(self.conf_val)
      self.ui.label_4.setText('置信度：'+text)



##  ============窗体测试程序 ================================
if  __name__ == "__main__":        #用于当前窗体测试
   app = QApplication(sys.argv)    #创建GUI应用程序
   form=QmyMainWindow()            #创建窗体
   form.show()
   sys.exit(app.exec_())
