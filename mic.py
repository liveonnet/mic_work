import sys
import os
import wave
import time
import json
import asyncio
from datetime import datetime
import requests
from enum import Enum
from math import ceil
import pyaudio
from array import array
from initlog import get_my_log
from initlog import singleton_run

logger = get_my_log('my_ddns_notify.log')
info, debug, warn = logger.info, logger.debug, logger.warning

class RecordStatus(Enum):
    STOP = 0
    START = 1

class RecordManager(object):
    THRESHOLD = 800 

    def __init__(self, file_name):
        self.out_file = file_name

        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 16000
#-#        self.CHUNK = 16384
        self.CHUNK = self.RATE
#-#        self.RECORD_SECONDS = 25

        self.p = None
        self.status = RecordStatus.STOP
        self.slience_at = None  # 静默计数器
        self.slient_duration_before_stop = 5  # 30  # 未达到阈值30秒后停止记录
#-#        self.hdl_out = None

#-#        self.buf = b''
#-#        self.sample_size = 0
#-#        self.byte_per_sec = 0

    def write_data(self, data):
#-#        if not self.hdl_out:
#-#            self.hdl_out = wave.open(self.out_file, 'wb')
#-#            self.hdl_out.setnchannels(self.CHANNELS)
#-#            self.hdl_out.setsampwidth(self.p.get_sample_size(self.FORMAT))
#-#            self.hdl_out.setframerate(self.RATE)
#-#            info('wav file created. %s', self.out_file)
#-#        self.hdl_out.writeframes(data)

#-#        open(self.out_file, 'ab').write(data)
        sys.stdout.buffer.write(data)  # 关键点 写二进制数据到标准输出 http://stackoverflow.com/questions/908331/how-to-write-binary-data-in-stdout-in-python-3
#-#        self.buf += data
#-#        if len(self.buf) >= self.byte_per_sec:
#-#            sys.stdout.buffer.write(data[:self.byte_per_sec])  # 关键点 写二进制数据到标准输出 http://stackoverflow.com/questions/908331/how-to-write-binary-data-in-stdout-in-python-3
#-#            self.buf = self.buf[self.byte_per_sec:]
#-#            info('output %s, left %s', self.byte_per_sec, len(self.buf))

    def is_slience(self, data):
        as_ints = array('h', data)
        max_value = max(as_ints)
        if max_value > RecordManager.THRESHOLD:
            debug('no slience %s > %s', max_value, RecordManager.THRESHOLD)
            return False
        else:
            debug('slience %s <= %s', max_value, RecordManager.THRESHOLD)
        return True

    def record(self):
        self.clean()
        self.p = pyaudio.PyAudio()
        while 1:
            stream = self.p.open(format=self.FORMAT,
                            channels=self.CHANNELS, 
                            rate=self.RATE, 
                            input=True,
                            output=True,
                            frames_per_buffer=self.CHUNK)
            try:
                info("* recording")
#-#                self.sample_size = self.p.get_sample_size(self.FORMAT)
#-#                self.byte_per_sec = self.sample_size * self.CHANNELS * self.RATE
#-#                info('sample_size %s byte_per_sec %s', self.sample_size, self.byte_per_sec)
                pre_data = None  # 保存超过阈值前的一段时间内的音频数据
#-#                for i in range(0, ceil(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                while 1:
                    data = stream.read(self.CHUNK)
                    if not self.is_slience(data):  # 触发阈值
                        if self.slience_at:
                            self.slience_at = None  # 清空静默计时器
                        if self.status == RecordStatus.STOP:  # 从非记录状态转到记录状态
                            info('* start pre data %s', len(pre_data) if pre_data else 0)
                            self.status = RecordStatus.START
                            if pre_data:
                                self.write_data(pre_data)  # 先补写之前的部分音频
                                pre_data = None
                        self.write_data(data)
                    else:  # 未触发阈值
                        if self.status == RecordStatus.START:
                            self.write_data(data)  # 即使未触发阈值，在记录状态下仍然写音频数据
                            if not self.slience_at:
                                self.slience_at = time.time()
                            elif time.time() - self.slience_at > self.slient_duration_before_stop:  # 静默计时器超时，进入非记录状态
                                info('* stop (slience since %s)', datetime.fromtimestamp(self.slience_at).strftime('%Y-%m-%d %H:%M:%S'))
                                self.status = RecordStatus.STOP
#-#                                break
                        else:  # 非记录状态下记录之前的部分音频
                            pre_data = data
            finally:
                stream.stop_stream()
                stream.close()

        info("* done")
        self.clean()

    def clean(self):
#-#        if self.hdl_out:
#-#            try:
#-#                self.hdl_out.close()
#-#            finally:
#-#                info('file closed. %s', self.out_file)
#-#                self.hdl_out = None
        if self.p:
            try:
                self.p.termiate()
            finally:
                self.status = RecordStatus.STOP
                self.p = None


if __name__ == '__main__':
    out_file = '/tmp/t.wav'
    RecordManager(out_file).record()