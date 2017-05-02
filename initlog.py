#coding=utf8

import os
import sys
from functools import wraps
from io import StringIO
import inspect
import traceback
import logging
import logging.handlers

LOG_DIR = '/tmp'
_LOCAL_PATH_ = os.path.abspath(os.path.dirname(__file__))
for _path in (os.path.abspath(_LOCAL_PATH_ + '/../..'), os.path.abspath(_LOCAL_PATH_ + '/../../lib'), os.path.abspath(_LOCAL_PATH_ + '/../../applib')):
    if _path not in sys.path:
        sys.path.append(_path)

def get_my_log(logname):
    global info, debug, error
    rlog = logging.getLogger()
    rlog.setLevel(logging.DEBUG)
    rlog.handlers = [_h for _h in rlog.handlers if not isinstance(_h, logging.StreamHandler)]

    log_sh = logging.StreamHandler()
    log_sh.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(funcName)s %(lineno)d | %(message)s', '%H:%M:%S')  # LogFormatter()
    log_sh.setFormatter(fmt)
    rlog.addHandler(log_sh)  # add handler(s) to root loggerll

    logfile = os.path.join(LOG_DIR if LOG_DIR else _LOCAL_PATH_, logname)
    log_filehdl = logging.handlers.TimedRotatingFileHandler(logfile, when='midnight', backupCount=5)
    log_filehdl.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s %(levelname)1.1s %(processName)s %(module)s %(funcName)s %(lineno)d | %(message)s', '%H:%M:%S')
    log_filehdl.setFormatter(fmt)
    rlog.addHandler(log_filehdl)  # add handler(s) to root logger
    rlog.info('log file %s %s', log_filehdl.baseFilename, log_filehdl.mode)
    return rlog


def flat_list(x):
    for _x in x:
        if isinstance(_x, (list, tuple)):
            for _f in _x:
                yield _f
        else:
            yield _x


def singleton_run(identifier):
    u'''通过检查pid文件保证同时只执行一个脚本实例
    '''
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            f_pid = os.path.join(LOG_DIR if LOG_DIR else '/tmp', 'pid_%s.txt' % identifier)
            try:
                fd = os.open(f_pid, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, ('%d' % os.getpid()).encode('utf8'))
            except Exception as e:
                print(e)
                print('''
                **************************************************************
                    app exit !!!
                    reason: %s already exists ! please check:
                    1) this app is already running ?
                    2) last run didn\'t exit normally ?
                    if this app is REALLY not running, delete %s and try launch this app again.''' % (f_pid, f_pid))
                sys.exit(-2)
            else:
                r = None
                try:
                    if inspect.iscoroutinefunction(func):
                        r = await func(*args, **kwargs)
                    else:
                        r = func(*args, **kwargs)
                except StandardError:
                    ei = sys.exc_info()
                    sio = StringIO()
                    traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
                    s = sio.getvalue()
                    sio.close()
                    if s[-1:] == "\n":
                        s = s[:-1]
                    print('got Exception:\n%s' % (s, ))
                    r = None
                finally:
                    try:
                        os.close(fd)
                        os.remove(f_pid)
                    except:
                        pass
                    return r
        return wrapper
    return decorator


