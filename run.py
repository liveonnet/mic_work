import sys
import os
import fcntl
from datetime import datetime
import subprocess
import shlex
from time import sleep

class DailyRecording(object):
    def __init__(self):
        self.p_mic = None
        self.p_ffmpeg = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.base_dir)
        self.f_name_stat = None  # stat文件名
        self.f_current_stat = None  # stat文件

    def _inRecording(self):
        return self.p_mic is not None

    def _startRecording(self):
        print('start mic process...')
#-#        f_name = '/mnt/d4/kevin/mic_data/pi_' + subprocess.check_output(shlex.split('date +%Y%m%d_%H%M%S')).decode('utf8').strip() + '.mp3'
        f_name = '/mnt/BK4T_2/mic_data/pi_' + subprocess.check_output(shlex.split('date +%Y%m%d_%H%M%S')).decode('utf8').strip() + '.mp3'
        self.f_name_stat = f_name + '.stat'
        self.p_mic = subprocess.Popen(shlex.split('%s ./mic.py' % sys.executable), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.p_ffmpeg = subprocess.Popen(shlex.split('ffmpeg -y -f s16le -ar 16000 -ac 2 -loglevel quiet -i - -acodec libmp3lame -f mp3 %s' % f_name), stdin=self.p_mic.stdout)
        print('mic process started %s %s' % (f_name, self.p_mic.stderr))
        flags = fcntl.fcntl(self.p_mic.stderr, fcntl.F_GETFL)
        fcntl.fcntl(self.p_mic.stderr, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def _stopRecording(self):
        if self.p_mic:
            now = datetime.now().strftime('%m%d_%H:%M')
            print('\n%s kill mic process ...' % now)
            self.p_mic.kill()
            self.p_mic.communicate()
            print('kill mic process done')
            self.p_mic = None

        if self.p_ffmpeg:
            print('kill ffmpeg process ...')
            self.p_ffmpeg.kill()
            self.p_ffmpeg.communicate()
            print('kill ffmpeg process done')
            self.p_ffmpeg = None

        if self.f_current_stat:
            self.f_current_stat.close()
            self.f_current_stat = None

    def _statusRecording(self, timeout=5):
        s = []
        while 1:
            try:
                s_data = os.read(self.p_mic.stderr.fileno(), 1024)
            except OSError:
                break
            else:
                s.append(s_data if isinstance(s_data, str) else s_data.decode('utf8'))
        print(''.join(s), end='', file=sys.stderr, flush=True)
        if self.f_name_stat:
            if self.f_current_stat:
                if self.f_name_stat != self.f_current_stat.name:
                    self.f_current_stat.close()
                    self.f_current_stat = open(self.f_name_stat, 'a')
            else:
                self.f_current_stat = open(self.f_name_stat, 'a')
            self.f_current_stat.write(''.join(s))

        sleep(timeout)

    def do_work(self):
        today = None
        try:
            while 1:
                now = datetime.now()
                hour = now.strftime('%H%M')
                # 工作日只录下午到晚上的时间段的
                start_hour = '1630'
                end_hour = '2355'
                if now.weekday() in (0, 1, 2, 3, 4) and (hour < start_hour or hour > end_hour):
#-#                start_hour = '0730'
#-#                end_hour = '2355'
#-#                if hour < start_hour or hour > end_hour:
                    if self._inRecording():
                        self._stopRecording()
#-#                    print('not in [%s,%s)' % (start_hour, end_hour))
                    if not int(hour) % 10:
#-#                        print('', file=sys.stderr, flush=True)
                        print(' %s' % now.strftime('%m%d_%H:%M'), end=' ', file=sys.stderr, flush=True)
                    print('x', end='', file=sys.stderr, flush=True)
                    sleep(60)
                    continue

                day = now.strftime('%Y%m%d')
                # 跨天判断
                if today != day:
                    print('\nday changed %s -> %s' % (today, day))
                    today = day
                    if self._inRecording():
                        self._stopRecording()
                    if not self._inRecording():
                        self._startRecording()
                self._statusRecording(5)
        except KeyboardInterrupt:
            print('got Ctrl + C')
        finally:
            self._stopRecording()
            print('done.')


if __name__ == '__main__':
    DailyRecording().do_work()
