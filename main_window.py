
import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow,QApplication,QWidget,QTableWidgetItem,QAbstractItemView
from Ui_tmp import Ui_MainWindow  
from wav_worker.player import *
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap, QIcon
from threading import Thread, Event
import datetime
from database.database import MusicDatabase
from time import sleep
import socket
import time
import pickle
import os
import bisect

class MyMainWindow(QMainWindow,Ui_MainWindow): 
    def __init__(self,parent =None):
        super(MyMainWindow,self).__init__(parent)
        self.setupUi(self)
        #self.lock = threading.Lock()
        # volume
        self.time = QTimer()
        self.database = MusicDatabase('data')
        self.music_info_list = self.database.GetMusicList(self.database.db_folder)
        #print(self.music_info_list)
        self.music_local_name = []
        for data in self.music_info_list:
            self.music_local_name.append(data['filename'])
        self.row = 0
        self.col = 0
        self.button_init()

        self.tableWidget.clicked.connect(self.set_row_col)

        self.pushButton_4.clicked.connect(self.play_pause_music_double)
       # self.pushButton_4.clicked.connect(self.play_music)
        #self.tableWidget.doubleClicked.connect(self.play_music)
        self.pushButton_5.clicked.connect(self.stop_music)
        self.play_event_list = []
        self.cur_player = -1
        self.horizontalSlider.valueChanged.connect(self.set_lyric)
        self.pushButton_6.clicked.connect(self.search)
        self.horizontalSlider.sliderReleased.connect(self.slider_move)
        self.play_event = 0
        self.server_lst = []
        self.abundant_data = []
        self.ser_map = {}
        self.buffer = []
        self.cur_time_buffer = []
        self.rec_stop = 0
        #self.init_player("no music")
        self.stream = -1
        self.client_sock_list = -1
        self.init_network()
        self.music_pc_map = {}
        
        self.p = pyaudio.PyAudio()
        
        self.lyric = -1
        self.sec = -1
        self.last = -1
        self.sample = -1
        self.total_size = 0
    def to_recv(self,sock):
        first = 1
        second = 1
        while True:
            rec_data = sock.recv(2048)
            #print('recv da')
            m_bytes = bytearray(rec_data)
            data = bytes(m_bytes[1024:])
            buff = bytes(m_bytes[:1024])
            #print(len(m_bytes))
            #print(sock)
            if data:
                if str(data.decode('utf-8','ignore'))[:5] == 'music':
                    print("music infor")
                    data = data.decode('utf-8','ignore')[5:].strip()
                    self.init_player(data)
                    print(self.cur_player.cur_sec)
                elif str(data.decode('utf-8','ignore'))[:4]=="sec:":
                    data = data.decode('utf-8','ignore')[4:].strip()
                        
                    self.cur_time_buffer.append(float(data))
                elif str(data.decode('utf-8','ignore'))[:4] == 'play':
                    print(1)
                    print(data.decode('utf-8','ignore'))
                    
                    chunk_num = data.decode('utf-8')[4:].strip()
                    chunk_num = int(chunk_num)
                    #print(chunk_num)
                    chunk = self.cur_player.chunk_return_by_num(chunk_num)
                    data_array = bytearray()
                    data_array += chunk
                    data_array += ("buffer"+str(chunk_num)+(1024-6-len(str(chunk_num)))*' ').encode()
                    #sock.send(chunk)
                    #sock.send(("buffer"+str(chunk_num)+(1024-6-len(str(chunk_num)))*' ').encode())
                    sock.send(data_array)
                    #print("okkkkkk!")
                elif str(data.decode('utf-8','ignore'))[:6] == 'buffer':
                    if self.total_size != 0:
                        while(len(self.buffer)*1024 > self.total_size/2):
                            print("sss")
                            continue
                    num = data.decode('utf-8','ignore')[6:].strip()
                    num = int(num)
                    #print("recv",num)
                    print(num,"buff")
                    #bisect.insort_left(self.buffer,(num,buff))
                    self.buffer.append((num,buff))
                elif first:
                    #print(data.decode())
                    sleep(1)
#                    print("first",data.decode())
                    print("Sss")

                    self.abundant_data.append(pickle.loads(data))
                    first = 0
                elif second:
                    #print("second rev")
                        #data = sock.recv(1024)
                    sleep(1)
                    print("sss",data.decode())
                    second = 0
                    
                    sample = json.loads(data)
                    if self.stream == -1:
                        self.sample = sample
                        print(sample[0],sample[1],sample[2],sample[3])
                        self.stream = self.p.open(format=self.p.get_format_from_width(sample[0]),
                        channels=sample[1],
                        rate=sample[2],
                        output=True)
                        self.total_size = (sample[3] * float(sample[2]))*(sample[1]*sample[0])
                        print("ee_cur")
                        #self.cur_player.set_pyaudio(self.stream)
                        #self.cur_player.total_second = sample[3]
                        self.MusicInit(sample[3])
                       # self.cur_player.mw = self.horizontalSlider
                        print("done setting!")
                else:
                            #self.cur_player = Music_player(data,self.server_lst)
                    print("end")
                    #print(data.decode())
                    
                    self.buffer.append((0,data))
                            #data = sock.recv(1024)
                            #data = data.decode()
                            #self.cur_time_buffer.append(float(data))
                        

    
    def acc(self):
        while True:
            
            client_sock, client_add = self.tcp_socket.accept()
            print(client_add)
            self.client_sock_list.append(client_sock)
            self.client_add_list.append(client_add)
            #client_sock.
            self.server_lst.append(client_sock)
            host = '10.13.40.72'
            port_nums = [24130,24131]
            cur = 0
            #for port in port_nums:
            self.ser_map[str(client_add[0])+str(client_add[1])] = client_sock
            print(self.ser_map)
            print("server connect")
            print("Ssssssssssssssssssssssssssssssssssssssssssss")
            tt1 = Thread(target=self.to_recv,args=(client_sock,))
            tt1.start()
    def con(self):
        #self.server_lst.append(socket.socket(socket.AF_INET,socket.SOCK_STREAM))
        host = '10.13.47.160'
        port_nums = [24130,24131]
        cur = 0
        p = [10002,10003]
        for port in port_nums:
            Address = (host,port)
            s_new = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s_new1 = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            #self.server_lst.append(socket.socket(socket.AF_INET,socket.SOCK_STREAM))
            #so = self.server_lst[cur]
            s_new.bind(('10.13.47.160',p[cur]))
            #s_new1.bind(('10.13.40.72',10003))
            self.ser_map[str(host)+str(port)] = s_new
            
            while s_new.connect_ex(Address)!=0:
                continue
            
            #s_new1.connect(Address)
            self.client_sock_list.append(s_new)
            #self.server_lst.append(s_new1)
            self.ser_map[str(host)+str(port)] = self.client_sock_list[cur]
            cur+=1
            data_array = bytearray()
            #data_array.append(("play"+str(cur_chunk_num)+(1024-4-len(str(cur_chunk_num)))*' ').encode())
             #   data_array.append(("play"+str(cur_chunk_num)+(1024-4-len(str(cur_chunk_num)))*' ').encode())
            data = pickle.dumps(self.music_info_list)
            chunk_num = 0
            data_array += ("sec:"+str(chunk_num)+(1024-4-len(str(chunk_num)))*' ').encode()
            data_array += data
            print('done')
            print()
            s_new.send(data_array)
            tt1 = Thread(target=self.to_recv,args=(s_new,))
            tt1.start()


    def play_rec_music(self):
        
        #cnt = 0
            #cnt = 0
        
        while True:
            
            if (len(self.buffer)==0):
                #cnt+=1
                #if cnt %10000000==0:
                    #  print("inini")
                pass
            else:
                #print("play music")
                
                if self.rec_stop:
                   # print(1)
                    continue
                #print(self.rec_stop)
                #print("ssss")
                print(self.buffer[0][0])
                #print("Sssssss")
                
                self.buffer.sort(key=lambda x:x[0])
                print("sorted",self.buffer[0][0])
                self.stream.write(self.buffer[0][1])
                print("write")
                num = self.buffer[0][0]
                print(num)
                total_chunk = num*1024
                #cur_sec = total_chunk/self.sample[3]
                t = total_chunk//(self.sample[0]*self.sample[1])
                current_seconds = t/float(self.sample[2]) 
                #print(current_seconds)
                self.horizontalSlider.setValue(current_seconds)
                self.buffer.pop(0)
                if self.cur_player == -1:
                    continue
                # if self.cur_player.other_music:
                #     print("send")
                #     thr1 = threading.Thread(target=thread_send_data,args=(self.server_sock_list,self.buffer[0][1],num,))
                #     thr1.start()
                
    def init_network(self):
        #print("network")
        self.tcp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        host ='10.13.47.160'
        port = 24130
        Address = (host,port)
        for data in self.music_info_list:
            data['locate'] = 10002
        self.tcp_socket.bind(Address)
        self.tcp_socket.listen(5)
        self.client_add_list = []
        self.client_sock_list = []
        self.server_add_list = []
        self.server_sock_list = []
        self.Thread_pool = []
        for data in self.music_info_list:
            data['info'] = [host,10003]
        #for i in range(1):
            #client_sock, client_add = self.tcp_socket.accept()
            # self.client_sock_list.append(client_sock)
            # self.client_add_list.append(client_add)
            #print("Ssssssssssssssssssssssssssssssssssssssssssss")
        t0 = Thread(target=self.acc)
            #self.Thread_pool.append(self.t1)
        sleep(0.1)
        t0.start()
        t2 = Thread(target=self.con)
        thread_rec_play = Thread(target=self.play_rec_music)
        t2.start()
        thread_rec_play.start()
        print("Sssssssssssssssssssssss")

    
    def slider_move(self):
        print("move.....................")
        #self.play_event.stop()
        self.cur_player.stop = 1
        #sleep(0.02)
        self.play_event.join()
        self.cur_player.stop_flag = 1
        
        #self.cur_player.stream.close()
        self.cur_player.stream.stop_stream()
        self.cur_player.stream.close()
        self.cur_player.p.terminate()
        
        print("okkk")
        v = self.horizontalSlider.value()
        print(v)
        self.cur_player.stop_flag = 0
        #self.cur_player.state = 0
        #self.play_event.join()
        #sleep(0.02)
        # #self.play_event.set()
        self.play_event = Thread(target=self.play_pause_music_double)
        # #self.cur_player.state = 1
        self.cur_player.cur_sec = v
        #self.cur_player.stop_flag = 0
        print(self.cur_player.cur_sec)
        self.cur_player.stop = 0
        self.cur_player.state = 0
        self.pushButton_4.setObjectName("Start")
        #self.pushButton_4.setIcon(QIcon('./resources/pause.png'))
        self.cur_player.reinit_stream()
        sleep(0.1)
        self.play_event.start()

        #self.play_event.start()
    def search(self):
        
        data = self.textEdit.toPlainText()
        #print(data)
        cur_row= 0
        print("Search",data)
        self.database.music_info_list = self.music_info_list
        data_ = self.database.query(data)
        
        for m in data_:
            filename = m['filename']
            duration = m['duration']
            artist = m['artist']
            album = m['album']
            network = m['network']
            if not artist:
                artist = "None"
            if not album:
                album = "None"
            if not filename:
                filename = "None"
            self.tableWidget_2.setItem(cur_row,1,QTableWidgetItem(filename))
            self.tableWidget_2.setItem(cur_row,2,QTableWidgetItem(str(datetime.timedelta(seconds=int(duration)))))
            self.tableWidget_2.setItem(cur_row,3,QTableWidgetItem(artist))
            self.tableWidget_2.setItem(cur_row,4,QTableWidgetItem(album))
            self.tableWidget_2.setItem(cur_row,5,QTableWidgetItem(network))
            cur_row += 1


    def init_table(self):
        cur_row = 0
        print("11")
        #cur_cnt = self.tableWidget.rowCount()
        if self.abundant_data:
            for data_l in self.abundant_data:
                for data in data_l:
                    if data['filename'] not in self.music_pc_map:
                        self.music_pc_map[data['filename']] = []
                    if data['filename'] in self.music_local_name:
                        self.music_pc_map[data['filename']].append(data['info'])
                        continue
                    else:
                        self.music_pc_map[data['filename']].append(data['info'])
                        data['network']='network'
                        self.music_info_list.append(data)
                        self.music_local_name.append(data['filename'])
        print(self.music_pc_map)
        self.database.music_info_list = self.music_info_list
        self.tableWidget.setRowCount(len(self.music_info_list))
        for m in self.music_info_list:
            filename = m['filename']
            duration = m['duration']
            artist = m['artist']
            album = m['album']
            network = m['network']
           # print(cur_row)
            if not artist:
                artist = "None"
            if not album:
                album = "None"
            if not filename:
                filename = "None"
            self.tableWidget.setItem(cur_row,1,QTableWidgetItem(filename))
            self.tableWidget.setItem(cur_row,2,QTableWidgetItem(str(datetime.timedelta(seconds=int(duration)))))
            self.tableWidget.setItem(cur_row,3,QTableWidgetItem(artist))
            self.tableWidget.setItem(cur_row,4,QTableWidgetItem(album))
            self.tableWidget.setItem(cur_row,5,QTableWidgetItem(network))
            cur_row += 1
    
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        print(self.music_info_list)
        return
    def button_init(self):
        self.pushButton.clicked.connect(self.display_list)
        self.pushButton_2.clicked.connect(self.display_search)
    def display_search(self):
        self.stackedWidget.setCurrentIndex(1)
    def display_list(self):
        print("11111")
        self.init_table()
        self.stackedWidget.setCurrentIndex(0)
        #self.init_table()

    def set_row_col(self,Item):
        self.row = Item.row()
        self.col = Item.column()
        print(self.row,self.col)

    def init_player(self,text):
        print(text)
        #self.t4 = 
        if (text) not in os.listdir("./data/"):
            print("other_music player init")
            self.cur_player = Music_player('other_music',self.client_sock_list)
        elif self.cur_player == -1:
            print("player_init")
            self.cur_player = Music_player("./data/"+text,self.client_sock_list)
            second = self.cur_player.getTotalSec()
            print('second',second)
            self.MusicInit(second)
        elif self.cur_player.filename != "./data/"+text:
            print("ok")
            self.cur_player.stream.close()
            self.cur_player.p.terminate()
            self.cur_player.f.close()
            self.cur_player.stop = 1
            self.play_event.join()

            del self.cur_player
            self.cur_player = Music_player("./data/"+text,self.client_sock_list)
            second = self.cur_player.getTotalSec()
            print('second',second)
            self.MusicInit(second)
        else:
            return
    
    def stop_music(self):
        print("Stop!!!")
        if self.cur_player==-1:
            return
        else:
            self.cur_player.stop_flag = 1
            self.pushButton_4.setIcon(QIcon('./resources/play.png'))



    def init_request_music(self,request_lst,text):
        data_array = bytearray()
        data_array += ('music'+text+(1024-5-len(text))*' ').encode()
        data_array += ('music'+text+(1024-5-len(text))*' ').encode()

        for so in request_lst:
            
            so.send(data_array)

            print("sssssssend")

    def set_lyric(self):
        print("!11")
        _translate = QtCore.QCoreApplication.translate
        #self.label.setText(_translate("MainWindow", self))
        min_ = str(datetime.timedelta(seconds=int(self.horizontalSlider.value())))
        self.label.setText(_translate("MainWindow", min_))
        if self.lyric == -1:
            print("dd")
            return
        #print(self.lyric)
        second = self.horizontalSlider.value()
        set_text = self.lyric[0]
        for index in range(0,len(self.sec)):
            if self.sec[index] < second:
                set_text = self.lyric[index]
        print(set_text)
        self.textEdit_2.setText(set_text)
    def play_pause_music_double(self):
        if self.col == 0 and self.row == 0:
            return
        else:
            text = self.tableWidget.item(self.row,1).text()
            if text == self.last:
                self.play_event = Thread(target=self.play_pause_music)
                self.play_event.daemon = True
                self.play_event.start()
                return 
            #if len(self.play_event_list) ==0:
            else:
                self.last = text
                self.init_player(text)
                self.request_lst = []
                if (text) not in os.listdir("./data/"):
                    print("another")
                    add_list = self.music_pc_map[text]
                    print(add_list)
                    for add in add_list:
                        self.request_lst.append(self.ser_map[str(add[0])+str(add[1])])
                    #self.request_lst[0].send(('play:'+text).encode())
                    print(self.request_lst)
                    t = Thread(target=self.init_request_music,args=(self.request_lst,text,))
                    t.start()
                    self.cur_player.set_request_lst(self.request_lst)
                    while True:
                        if self.stream == -1:
                            continue
                        break
                    self.textEdit_2.setText("No Lyrics")
                
                lyric_filename = text[:-4]+".lrc"
                print(lyric_filename)
                sec = []
                lyric = []
                print(os.listdir("./lyris/"))
                if lyric_filename not in os.listdir("./lyris/"):
                    self.lyric = -1
                    self.sec = -1
                    self.textEdit_2.setText('No lyrics')
                else:

                    with open("./lyris/"+lyric_filename) as file:
                        raw_text = file.readlines()
                        for i in range(0, len(raw_text)):
                            line = raw_text[i]
                            #print(line)
                            sec.append(float(line[1:3]) * 60 + float(line[4:9]))
                            #print(float(line[1:3]) * 60 + float(line[4:9]))
                            if i == len(raw_text):
                                lyric.append(line[10:len(line)])
                            else:
                                lyric.append(line[10:len(line)])
                        print(lyric)
                        
                    self.lyric = lyric
                    self.sec = sec
                
                self.play_event = Thread(target=self.play_pause_music)
                self.play_event.daemon = True
                self.play_event.start()
            
            #     #self.play_event_list.append(event)
            #     #self.play_event_list.pop()
            # else:
            #     print("event1")
            #     event1 = threading.Thread(target=self.play_stop_music)
            #     event1.start()
            #     self.play_event_list[0].join()
            #     event1.join()

    def play_pause_music(self):
        #print(self.cur_player)
        #return
        #second = self.cur_player.getTotalSec()

        #self.MusicInit(second)
        if self.pushButton_4.objectName() == "Start":
            self.pushButton_4.setObjectName("Pause")
            
            self.pushButton_4.setIcon(QIcon('./resources/pause.png'))
            if self.cur_player.state ==1 :
                self.cur_player.state = 0
                
                #print(self.cur_player.cur_sec)
                if self.cur_player.other_music:
                    print("restart")
                    self.cur_player.request_flag = 0
                    self.rec_stop = 0
                #self.cur_player.play_music()
                
                
            else:

                self.cur_player.mw = self.horizontalSlider
                self.cur_player.text_layout = self.textEdit_2
                
                if self.cur_player.other_music:
                    print("request")
                    self.cur_player.state = 0
                    self.cur_player.request_music_chunk()
                else:
                    print("play")
                    
                    second = self.cur_player.getTotalSec()
                    #print('second',second)
                    #self.MusicInit(second)
                    
                    print(self.cur_player.cur_sec)
                    self.cur_player.play_music()
                
        else:
            #print(11)
            self.pushButton_4.setObjectName("Start")
            self.pushButton_4.setIcon(QIcon('./resources/play.png'))
            self.cur_player.state= 1
            if self.cur_player.other_music:
                print("Stop!!")
                self.cur_player.set_request_flag(1)

                self.rec_stop = 1
    

    def MusicInit(self,second):

        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_translate("MainWindow", "00:00"))
        min_ = str(datetime.timedelta(seconds=int(second)))
        self.label_2.setText(_translate("MainWindow",min_))
        ## init slider
        print("start")
        self.horizontalSlider.setMaximum(second)
        self.horizontalSlider.setValue(second)
        #self.horizontalSlider.setSingleStep(1)
        

        
if __name__ == "__main__":


    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec_())    
