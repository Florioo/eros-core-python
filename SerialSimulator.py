from multiprocessing.connection import Connection
import multiprocessing as mp

pipes = {}
class SerialSimulator():
    def __init__(self, pipename, part) -> None:
        if not pipename in pipes:
            pipes[pipename] = mp.Pipe()
    
        self.pipe = pipes[pipename][part]
        
    def read(self):
        return self.pipe.recv()
    
    def write(self, data):
        self.pipe.send(data)
         