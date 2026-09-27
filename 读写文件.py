import time
import os

def get_speed(samples: list, sliding_window: float):
    while samples and (samples[-1][0] - samples[0][0]) > sliding_window:
        samples.pop(0)
    if len(samples) < 2:
        return 0.0

    t0, b0 = samples[0]
    t1, b1 = samples[-1]
    delta_t = t1 - t0
    if delta_t <= 0:
        return 0.0
    return (b1 - b0) / delta_t

def 写文件(
    路径: str,
    大小: int,
    块大小: int = 1024 * 1024,
    滑动窗口: float=1.0,
    回调: callable=None,
) -> tuple[list[tuple[float, int | float]], float]:
    回调 = 回调 or (lambda x: None)
    记录 = []
    样本 = []
    速度 = 0.0
    已写入 = 0
    块 = b'\x00' * 块大小
    文件 = os.open(路径, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)

    开始时间 = time.time()
    while True:
        剩余 = 大小 - 已写入
        if 剩余 <= 0:
            break
        写入大小 = min(块大小, 剩余)
        os.write(文件, 块[:写入大小])
        os.fsync(文件)
        已写入 += 写入大小

        现在 = time.time()
        样本.append((现在, 已写入))
        速度 = get_speed(样本, 滑动窗口)
        if 速度 > 0.0:
            记录.append((现在, 已写入, 速度))
            回调(记录)
    结束时间 = time.time()

    os.close(文件)
    return 记录, 结束时间 - 开始时间

def 读文件(
    路径: str,
    块大小: int = 1024 * 1024,
    滑动窗口: float = 1.0,
    回调: callable = None,
) -> tuple[list[tuple[float, int | float]], float]:
    回调 = 回调 or (lambda x: None)
    记录 = []
    样本 = []
    速度 = 0.0
    已读取 = 0
    文件 = os.open(路径, os.O_RDONLY)

    开始时间 = time.time()
    while True:
        data = os.read(文件, 块大小)
        if not data:
            break
        本次读入 = len(data)
        已读取 += 本次读入
        现在 = time.time()
        样本.append((现在, 已读取))
        速度 = get_speed(样本, 滑动窗口)
        if 速度 > 0.0:
            记录.append((现在, 已读取, 速度))
            回调(记录)
    结束时间 = time.time()

    os.close(文件)
    return 记录, 结束时间 - 开始时间