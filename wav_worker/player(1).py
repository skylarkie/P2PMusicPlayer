import hashlib
import binascii
import pyaudio
import audioop
import time
import wave
import json
import threading

def hex2dec(hex,rev=True):
    if rev:
        hex = str(hex)[2:-1]
        new_hex = ''.join(reversed([hex[i:i+2] for i in range(0, len(hex), 2)]))
        new_hex = "0X" + new_hex
    else:
        new_hex = hex
    result_dec = int(new_hex, 16)
    return result_dec

def thread_send(so_lst,info):
    nframe = info['ChunkSize']//(info['NumChannels']*info['BitsPerSample']/8)
    total_second = nframe/info['SampleRate']
    if len(so_lst)!=0:
        data_array = bytearray()
        chunk_num = 0
        #data_array.append(("sec:"+str(chunk_num)+(1024-4-len(str(chunk_num)))*' ').encode())
        sample = [info['BitsPerSample']/8,info["NumChannels"],info['SampleRate'],total_second]
        data = json.dumps(sample).encode()
        chunk_num = 0
        data_array += ("sec:"+str(chunk_num)+(1024-4-len(str(chunk_num)))*' ').encode()
        data_array += data
        for so in so_lst:
            so.send(data_array)
    print("done sending info")
def thread_send_data(so_lst,data):
    #print("1111")
    data_array = bytearray()
    chunk_num = 0
    data_array += ("sec:"+str(chunk_num)+(1024-4-len(str(chunk_num)))*' ').encode()
    data_array += data   
    if len(so_lst)!=0:
        for so in so_lst:
            so.send(data_array)
def thread_send_sec(so_lst,second):
    #print("eeee")
    data_array = bytearray()
    chunk_num = 0
    data_array += ("sec:"+str(chunk_num)+(1024-4-len(str(chunk_num)))*' ').encode()
    data_array += ("sec:"+str(second)+(1024-4-len(str(second)))*' ').encode()
    #data_array.append(("11"+str(chunk_num)+(1024-6-len(str(chunk_num)))*' ').encode())
   
    if len(so_lst)!=0:
        for so in so_lst:
            so.send(data_array)

            
            
            #so.send(str(current_seconds).encode())

class Music_player:

    def __init__(self,filename,so_lst,chunk=1024) -> None:
        self.filename = filename
        self.info = dict()
        self.p = pyaudio.PyAudio()
        self.so_lst = so_lst
        self.chunk = chunk
        self.state = 0
        self.stop_flag = 0
        self.cur_sec = 50
        self.mw = 0
        self.stop = 0
        self.send_flag = 1
        self.other_music = 0
        self.stream = -1
        self.request_lst = -1
        if filename == 'other_music':
            self.other_music = 1
        else:
            self.f = open(filename, mode="rb")
            self.extract_info(self.filename)
            self.stream = self.p.open(format=self.p.get_format_from_width(self.info['BitsPerSample']/8),
                            channels=self.info["NumChannels"],
                            rate=self.info['SampleRate'],
                            output=True)
    
        # if self.so_lst:
        #     for so in self.so_lst:
        #         t = threading.Thread(target=(self.send_data_chunk),args=(so,))
        #         t.start()
    def set_pyaudio(self,stream):
        self.stream = stream

    def set_request_lst(self,request_lst):
        self.request_lst = request_lst
    
    def extract_info(self,filename, buffer_size=2**10*8):
        self.info["ChunkID"] = self.f.read(4)
        self.info["ChunkSize"] = hex2dec(binascii.hexlify(self.f.read(4)))
        self.info["Format"] = self.f.read(4)
        self.info["Subchunk1ID"] = self.f.read(4)
        self.info["Subchunk1Size"] = hex2dec(binascii.hexlify(self.f.read(4)))
        self.info["AudioFormat"] = hex2dec(binascii.hexlify(self.f.read(2)))
        self.info["NumChannels"] = hex2dec(binascii.hexlify(self.f.read(2)))
        self.info["SampleRate"] = hex2dec(binascii.hexlify(self.f.read(4)))
        self.info["ByteRate"] = hex2dec(binascii.hexlify(self.f.read(4)))
        self.info["BlockAlign"] = hex2dec(binascii.hexlify(self.f.read(2)))
        self.info["BitsPerSample"] = hex2dec(binascii.hexlify(self.f.read(2)))
        self.info["Subchunk2ID"] = self.f.read(4)
        self.info["Subchunk2size"] = hex2dec(binascii.hexlify(self.f.read(4)))
        self.info['data'] = ''
        nframe = self.info['ChunkSize']//(self.info['NumChannels']*self.info['BitsPerSample']/8)
        self.total_second = nframe/self.info['SampleRate']
        #print(self.info)
        if len(self.so_lst)!=0:
            t1 = threading.Thread(target=thread_send,args=(self.so_lst,self.info,))
            t1.start()
        print(self.other_music)
    def getTotalSec(self):
        return self.total_second
    #TODO: 1. connect to player
    #      2. optimize the structure

    # def send_data_chunk(self,so):
    #     print("sending data!!")
    #     tmp = self.cur_sec
    #     while(self.send_flag):
    #         continue
    #     self.send_flag = 0
    #     tf = tmp*float(self.info['SampleRate']) *(self.info['NumChannels']*self.info['BitsPerSample']/8)
    #     tmpfile = open(self.filename, mode="rb")
    #     dump = tmpfile.read(44+int(tf))
    #     del dump
    #     f = tmpfile
    #     cnt = 1
    #     data = f.read(self.chunk)
    #     while(True):
    #         while(self.state):
    #             #print("Stop")
    #             continue
    #         while(self.send_flag):
    #             continue
    #         if data:
    #             so.send(data)
    #         data = f.read(self.chunk)
    #         if data == b'':
    #             break
    
    
    def play_music(self):
        print("start playing")
        self.running = True
        data = self.f.read(self.chunk)
        print("11")
        nframe = self.info['ChunkSize']//(self.info['NumChannels']*self.info['BitsPerSample']/8)
        self.total_second = nframe/self.info['SampleRate']

        self.total_chunk = 0
        offset = 0
        tmp = self.cur_sec
        tf = tmp*float(self.info['SampleRate']) *(self.info['NumChannels']*self.info['BitsPerSample']/8)
        tmpfile = open(self.filename, mode="rb")
        dump = tmpfile.read(44+int(tf))
        
        del dump
        #print(tf)
        self.f = tmpfile
        cnt = 1
        data = self.f.read(self.chunk)
        flag = 0
        while self.running:
            if self.stop:
                print("stop")
                exit(0)
            while(self.state):
                #print(current_seconds)
                continue
            if self.stop_flag==1:
                break
            if data:
                self.stream.write(data)
                self.total_chunk += self.chunk
                t = self.total_chunk//(self.info['NumChannels']*self.info['BitsPerSample']/8)
                current_seconds = t/float(self.info['SampleRate']) + self.cur_sec
                if len(self.so_lst)!=0:
                    #print("fuck")
                    thr1 = threading.Thread(target=thread_send_data,args=(self.so_lst,data,))
                    t1 = threading.Thread(target=thread_send_sec,args=(self.so_lst,current_seconds))
                    thr1.start()
                    t1.start()

                if self.mw!=0:
                    #print("Set value")
                    self.mw.setValue(current_seconds)
                    #print("cur_sec",current_seconds)
                    
                    #self.mw = 0
                    #1
                # if self.so_lst != -1:
                #     for so in self.so_lst:
                #         so.send(data)

                data = self.f.read(self.chunk)
                # if current_seconds >0:
                #     print(current_seconds)
            if data == b'':
                break
        self.cur_sec = current_seconds

    def chunk_return_by_num(self,num):
        file = open(self.filename,mode='rb')
        file.read(44 + 1024*num)
        data = file.read(self.chunk)
        return data
    def request_music_chunk(self):
        print("start requesting other music")
        self.running = True
        cur_chunk_num = 0
        while self.running:
            if self.stop:
                print("stop")
                exit(0)
            while(self.state):
                #print(current_seconds)
                continue
            if self.stop_flag==1:
                break 
            for so in self.request_lst:
                data_array = bytearray()
                data_array += ("play"+str(cur_chunk_num)+(1024-4-len(str(cur_chunk_num)))*' ').encode()
                data_array += ("play"+str(cur_chunk_num)+(1024-4-len(str(cur_chunk_num)))*' ').encode()

                so.send(data_array)
                #so.send(str(cur_chunk_num).encode())
                cur_chunk_num += 1
    
    def play_other_rec_music(self,buffer,cur_seconds):
        self.stream.write(buffer)
        self.mw.setValue(cur_seconds)



# t = Music_player('file_example.wav')
# t.play_music()
# b = 1.2
# a = (str(b)+2*' ')
# a = a.strip()
# print(a)
# print(len(a))