import pathlib
import queue
import socket
import subprocess
import sys
import threading
import time

import requests

from wait_net_service import wait_net_service


def reader(stream, tag, buffer):
    """Generic reader for buffer-filling thread"""
    while True:
        line = stream.readline()
        if line:
            buffer.put((tag, line))
        else:
            break


class FlaskAppManager(object):
    def __init__(self, app, **run_kwargs):
        self.app = app
        self.run_kwargs = {
            'passthrough_errors': True, # avoids hanging server on error
            'threaded': True,
        }
        self.run_kwargs.update(run_kwargs)
        self.port = self.run_kwargs.get('port', 5000)

    def __enter__(self):
        print('Starting Flask app "{}"'.format(self.app.name))
        # Create a thread that will contain our running server
        self.thread = threading.Thread(
            target=self.app.run,
            kwargs=self.run_kwargs,
        )
        self.thread.start()
        wait_net_service('127.0.0.1', self.port, timeout=5)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print('Shutting down Flask app "{}"'.format(self.app.name))
        requests.post('http://localhost:{}/_shutdown'.format(self.port))
        self.thread.join()


# class DjangoRunserverThreadManager(object):
#     def __init__(self, app, **run_kwargs):
#         self.app = app
#         self.run_kwargs = {
#             'passthrough_errors': True, # avoids hanging server on error
#             'threaded': True,
#         }
#         self.run_kwargs.update(run_kwargs)
#         self.port = self.run_kwargs.get('port', 5000)
#
#     def __enter__(self):
#         print('Starting Flask app "{}"'.format(self.app.name))
#         # Create a thread that will contain our running server
#         self.thread = threading.Thread(
#             target=self.app.run,
#             kwargs=self.run_kwargs,
#         )
#         self.thread.start()
#         wait_net_service('127.0.0.1', self.port, timeout=5)
#
#     def __exit__(self, exc_type, exc_value, traceback):
#         print('Shutting down Flask app "{}"'.format(self.app.name))
#         requests.post('http://localhost:{}/_shutdown'.format(self.port))
#         self.thread.join()


class DjangoRunserverManager(object):
    def __init__(self, manage, port):
        self.manage = pathlib.Path(manage).resolve()
        if not self.manage.is_file():
            raise RuntimeError('manage.py not found ({})'.format(str(self.manage)))
        self.port = port

    def __enter__(self):
        print('Launching Django')
        self.djsp = subprocess.Popen(
            [sys.executable, str(self.manage), 'runserver', str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            cwd=self.manage.parent,
        )

        self.q = queue.Queue()
        self.threads = [
            threading.Thread(target=reader, args=(*args, self.q), daemon=True)
            for args
            in [
                (self.djsp.stdout, 'out'),
                (self.djsp.stderr, 'err')
            ]
        ]

        for thread in self.threads:
            thread.start()

        wait_net_service('127.0.0.1', self.port, timeout=5)
        time.sleep(1)
        print('ready')
        self.dump()

        return self

    def dump(self):
        while True:
            try:
                tag, line = self.q.get_nowait()
            except queue.Empty:
                break
            else:
                print(tag, line, end='')

    def __exit__(self, exc_type, exc_value, traceback):
        print('Shutting down Django script')
        self.djsp.terminate()
        self.djsp.kill()

        # print('-dj comm')
        # try:
        #     sc_out, sc_err = self.djsp.communicate(timeout=1)
        # except subprocess.TimeoutExpired:
        #     print('-timeout, killing')
        #     self.djsp.kill()
        #     print('-comm retry')

            # sc_out, sc_err = self.djsp.communicate()

        # clean out threads
        print('cleaning threads')
        while True:
            try:
                tag, line = self.q.get_nowait()
            except queue.Empty:
                if self.djsp.poll() is not None:
                    print('Django exited with code {}'.format(self.djsp.returncode))
                    # print('joining threads')
                    # for thread in self.threads:
                    #     thread.join()
                    break
                else:
                    time.sleep(0.1)
            else:
                print(tag, line, end='')

        # print(sc_out)
        # print(sc_err)
        # self.djsp.terminate()
        print('-dj wait..,')
        self.djsp.wait()
#
# import multiprocessing
# import os
# import tempfile
# import django
# from django.core.management import execute_from_command_line

if __name__ == '__main__':
    pass
    # test/demo imports
    #
    # sys.path[0] = str(pathlib.Path(__file__).resolve().parent.parent)
    #
    # os.environ['DJANGO_SETTINGS_MODULE'] = 'appliance_registry.test_settings'
    # with tempfile.TemporaryDirectory() as td:
    #     os.environ['TEMP_DATABASE'] = td + '/db.sqlite'
    #     print(td)
    #     django.setup()
    #
    #     execute_from_command_line(['manage.py', 'migrate'])
    #
    #     # runserver = threading.Thread(
    #     runserver = multiprocessing.Process(
    #         target=execute_from_command_line,
    #         args=(['manage.py', 'runserver', '8003', '--nothreading'],),
    #         daemon=True
    #     )
    #     runserver.start()
    #     wait_net_service('127.0.0.1', 8003, timeout=5)
    #
    #     import requests
    #     print(requests.get('http://localhost:8003/').json())
    #
    #     time.sleep(1)

    # x = subprocess.Popen(
    #     [sys.executable, 'manage.py', 'runserver'],
    #     cwd=pathlib.Path(__file__).resolve().parent.parent,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    #     universal_newlines=True,
    # )
    #
    # q = queue.Queue(maxsize=100)
    # threads = [
    #     threading.Thread(target=reader, args=(*args, q), daemon=True)
    #     for args
    #     in [
    #         (x.stdout, 'out'),
    #         (x.stderr, 'err')
    #     ]
    # ]
    # print('starting')
    # for thread in threads:
    #     thread.start()
    # print('waiting')
    #
    # start = time.monotonic()
    # while time.monotonic() - start < 5:
    #     try:
    #         tag, line = q.get_nowait()
    #     except queue.Empty:
    #         time.sleep(0.1)
    #     else:
    #         print(tag, line, end='')
    # print('terminating')
    #
    # x.terminate()
    # print('waiting')
    #
    # while True:
    #     try:
    #         tag, line = q.get_nowait()
    #     except queue.Empty:
    #         if x.poll() is not None:
    #             for thread in threads:
    #                 thread.join()
    #             break
    #         else:
    #             time.sleep(0.1)
    #     else:
    #         print(tag, line, end='')


    # with DjangoRunserverManager('../manage.py', 8003) as dj:
    #     time.sleep(1)
    #     dj.dump()
    #     time.sleep(1)
    #     dj.dump()
