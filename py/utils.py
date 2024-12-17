import time
import threading
import socket
import hashlib

class SnowflakeIDGenerator:
    def __init__(self, node_id=None, id_length=19, prefix=""):
        self.node_id = node_id if node_id is not None else self._generate_node_id()  # 自动生成节点 ID
        self.epoch_start = int(time.mktime(time.strptime("2023-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"))) * 1000 # 创建生成器，自定义纪元为 2023 年 1 月 1 日 00:00:00
        self.id_length = id_length  # 生成的 ID 总长度
        self.prefix = prefix  # ID 前缀

        self.sequence = 0  # 序列号
        self.last_timestamp = -1  # 上次生成 ID 的时间戳

        self.lock = threading.Lock()  # 保证线程安全

    def _generate_node_id(self):
        """基于主机名和 MAC 地址生成唯一的节点 ID"""
        hostname = socket.gethostname()
        mac = socket.gethostbyname(hostname)
        node_hash = hashlib.md5(f"{hostname}-{mac}".encode()).hexdigest()
        return int(node_hash, 16) & 0x3FF  # 限制节点 ID 最大值为 1023

    def _current_timestamp(self):
        """获取当前时间戳，单位为毫秒"""
        return int(time.time() * 1000)

    def _wait_for_next_millisecond(self, last_timestamp):
        """等待到下一毫秒"""
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    def generate_id(self):
        """生成唯一 ID"""
        with self.lock:
            current_timestamp = self._current_timestamp()

            if current_timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Refusing to generate ID")

            if current_timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF  # 序列号最大值为 4095
                if self.sequence == 0:
                    current_timestamp = self._wait_for_next_millisecond(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = current_timestamp

            # 计算时间戳部分
            timestamp_part = current_timestamp - self.epoch_start

            # 拼接 ID（时间戳 + 节点 ID + 序列号）
            unique_id = (timestamp_part << 22) | (self.node_id << 12) | self.sequence

            # 转为字符串并加上前缀
            unique_id_str = f"{self.prefix}{unique_id}"

            # 如果设置了固定长度，进行截断或填充
            if self.id_length:
                unique_id_str = unique_id_str[:self.id_length].zfill(self.id_length)

            return unique_id_str


class MyTimer:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """记录起始时间"""
        self.start_time = time.time()

    def stop(self):
        """记录结束时间"""
        self.end_time = time.time()

    def elapsed(self):
        """计算并返回过程耗时"""
        if self.start_time is None or self.end_time is None:
            raise ValueError("Timer has not been started or stopped.")
        return self.end_time - self.start_time


def download_picture(picture_url, file_path, file_name):
    pass

# 示例使用
def main():

    generator = SnowflakeIDGenerator(id_length=20, prefix="ID-")

    # 生成唯一 ID
    for _ in range(10):
        print(generator.generate_id())

if __name__ == "__main__":
    main()
