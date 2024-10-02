# server: receive slices from more than one client and combine them into one image
# client: send slices to server according to the order

import socket
import cv2
import sys
import numpy as np

import pickle
class ImageClient:
      def __init__(self,ip,port):
            self.ip = ip
            self.port = port
            self.order = 0
            try:
                  self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            except socket.error as msg:
                  print("Failed to create socket. Error code: "+str(msg[0])+", Error message: "+msg[1])
                  sys.exit()
      
      def connect(self):
            while True:
                  try:
                        self.s.connect((self.ip,self.port))
                        break
                  except:
                        continue
      
      def send(self,data):
            while True:
                  try:
                        self.s.send(data)
                        break
                  except:
                        print("send error")
                        continue
      
      def close(self):
            self.s.close()

      def send_image(self,filename):
            img = cv2.imread(filename)
            res,img = cv2.imencode('.bmp',img)
            img = img.tobytes()
            with open('results.bmp','wb') as f:
                  f.write(img)
            print(len(img))
            # get clwrite(ient order from server
            rec_data = self.s.recv(2048)
            m_bytes = bytearray(rec_data)
            data = bytes(m_bytes[1024:])
            buff = bytes(m_bytes[:1024])
            print(data)
            client_num = int(str(data.decode('utf-8','ignore'))[6:].strip())
            self.order = int(str(buff.decode('utf-8','ignore'))[6:].strip())
            print(self.order,client_num)
            # send slices to server
            print(len(img)//1024)
            
            buff_size = 0
            cur = 0
            for i in range(len(img)//1024+1):
                  if (i+1)*1024 > len(img):
                        print(i)
                        cur+=1
                        data_array = bytearray()
                        data_array += ("buffer:"+str(len(img[i*1024:]))+(2048-3-len(img[i*1024:])-7)*' ').encode()
                       # print(str(len(img[i*1024:])))
                        print(len(data_array))
                        data_array += img[i*1024:]
                        buff_size += len(img[i*1024:])
                        print(len(data_array))
                        #buff_size += len(img[i*1024:])
                        #print(buff_size)
                        #data_array += ("buffer"+str(i)+(1024-6-len(str(i)))*' ').encode()
                        #print("aa")
                        #b = bytes(data_array[:1024])
                        #print(int(bytes(data_array[:1024]).decode('utf-8','ignore')[7:].strip()))
                        #print(len(data_array))
                        print("buff_size",buff_size)
                        self.send(data_array)
                  elif i%client_num == self.order:

                        cur+=1
                        data_array = bytearray()
                        #data_array += img[i*1024:(i+1)*1024]
                        print(i)
                        #print("7322222")
                        data_array += ("buffer"+str(i)+(1024-6-len(str(i)))*' ').encode()
                        data_array += img[i*1024:(i+1)*1024]
                        buff_size += 1024
                        print(buff_size)
                        #data_array += ("buffer"+str(i)+(1024-6-len(str(i)))*' ').encode()
                        self.send(data_array)
            #print(i*1024)
            # send finish signal
            print(len(img))
            print(cur)
            data_array += ("buffer"+str(-1)+(1024-6-len(str(-1)))*' ').encode()
            data_array += ("buffer"+str(-1)+(1024-6-len(str(-1)))*' ').encode()
            #data_array += img[i*1024:(i+1)*1024]
            #data_array += ("buffer"+str(-1)+(1024-6-len(str(-1)))*' ').encode()
            print("last")
            print()
            self.send(data_array)
            
      def main(self):
            self.connect()
            self.send_image("1-2.bmp")
            self.close()

            
class ImageServer:
      def __init__(self,ip,port, client_num):
            self.ip = ip
            self.port = port
            try:
                  self.s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            except socket.error as msg:
                  print("Failed to create socket. Error code: "+str(msg[0])+", Error message: "+msg[1])
                  sys.exit()
            
            self.s.bind((self.ip,self.port))
            self.s.listen(5)
            self.client_num = client_num
            self.conn_lst = []
            self.addr_lst = []
            self.status_lst = []
            self.buffer = []
            self.buffer_size = 0  # the size of the buffer
      
      def accept(self):
            conn,addr = self.s.accept()
            self.conn_lst.append(conn)
            self.addr_lst.append(addr)
            data_array = bytearray()
            data_array += ("buffer"+str(len(self.conn_lst)-1)+(1024-6-len(str(len(self.conn_lst)-1)))*' ').encode()
            data_array += ("buffer"+str(self.client_num)+(1024-6-len(str(self.client_num)))*' ').encode()

            self.conn_lst[-1].send(data_array) 
            self.status_lst.append(0)
            print("Accept connection from ",addr)
      
      def receive(self):
            for i in range(len(self.conn_lst)):
                  data = self.conn_lst[i].recv(2048)
                  if data:
                        # if data (order, slice) is received, put it into buffer
                        if (data[0] > 0):
                              print("received data from ",self.addr_lst[i])
                              self.buffer.append(data)
                              self.buffer_size += len(data)
                        elif (data[0] == -1):
                              print("received finish signal from ",self.addr_lst[i])
                              self.status_lst[i] = 1
      
      def close(self):
            self.s.close()
            for i in range(len(self.conn_lst)):
                  self.conn_lst[i].close()

      def main(self):
            while True:
                  # accept connections
                  if len(self.conn_lst) <= self.client_num:
                        self.accept()
                        continue                                             
                  # receive data from clients
                  self.receive()
                  # if all clients send finish signal, combine slices into one image
                  if sum(self.status_lst) == len(self.conn_lst):
                        print("all clients send finish signal")
                        self.combine()
                        break
            
            #handle the rest of the data in buffer
            sorted_buffer = sorted(self.buffer, key=lambda x: x[0])
            img1 = cv2.imread('1-2.bmp')
            img1 = img1.tobytes()
            img = b''
            #extract slices from buffer
            for i in range(len(sorted_buffer)):
                  if i%len(self.conn_lst) == self.order:
                        img += sorted_buffer[i][1]
            # save image
            img = np.frombuffer(img, dtype=np.uint8)
            img = img.reshape((512,512,3))
            cv2.imwrite("result.jpg",img)
            print(img==img1)
            self.close()

a = ImageClient('localhost',24001)           
a.main()
# img = cv2.imread('1-1.bmp')
# img = img.tobytes()
                              
# print(img[0:1024])