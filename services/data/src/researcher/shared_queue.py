"""共享队列 - 进程间通信"""
import multiprocessing as mp

def create_shared_queue(maxsize: int = 1000) -> mp.Queue:
    """创建共享队列"""
    return mp.Queue(maxsize=maxsize)
