#music database
import sqlite3
import os
import json
from tinytag import TinyTag

class MusicDatabase:
      def __init__(self, db_folder=None):
            self.db_folder = db_folder
            if not db_folder is None:
                  self.music_info_list = self.GetMusicList(db_folder)
            self.music_info_list = []
      def GetMusicList(self, db_folder):
            #get music list from database
            files = os.listdir(db_folder)
            music_info_list = []
            for file in files:
                  if file.endswith(".mp3") or file.endswith(".flac") or file.endswith(".wav"):
                        tag = TinyTag.get(os.path.join(db_folder, file))
                        info = {
                              'filename': file,
                              'title': tag.title,
                              'artist': tag.artist,
                              'album': tag.album,
                              'duration':tag.duration,
                              'network': 'local'
                        }
                        print(tag)
                        if tag.extra:
                              info['extra'] = tag.extra
                        #print(tag)
                        music_info_list.append(info)
            #save info list to json
            json_data = json.dumps(music_info_list, indent=4)
            f = open(os.path.join(db_folder, "music_info_list.json"), 'w')
            f.write(json_data)
            f.close()
            self.music_info_list = music_info_list
            return music_info_list

      def query(self,data):
            cand = []
            print(data)

            for m in self.music_info_list:
                  flag = 0
                  #print(m)
                  for j in m.values():
                       # print(j)
                        if data in str(j):
                              flag = 1
                        #      print("ok")
                              break
                  if flag == 1:
                        cand.append(m)
                        flag = 0
            #print(cand)
            return cand

a = MusicDatabase('data')