from 格式化大小 import 格式化大小 as fmt_size
import json
import os

one_byte = 1 # 1B
one_k = 1024 # 1KB
half_k = one_k // 2 # 0.5KB, 512B
one_m = one_k * 1024 # 1MB
half_m = one_m // 2 # 0.5MB, 512KB
one_g = one_m * 1024 # 1GB
half_g = one_g // 2 # 0.5GB, 512MB

def write_until_no_left(path, size: int, callback: callable=None, max_count: int=None) -> bool:
    i = 0
    with open(path, 'wb') as f:
        while True:
            if max_count is not None and i >= max_count:
                return True
            try:
                f.write(b'\x00' * size)
                if callback:
                    callback(size)
            except OSError as e:
                if '[Errno 28] No space left on device' in str(e):
                    return False
                else:
                    raise e
            i += 1

def write_until_disk_full(path: str, data: dict, max_one_file: int) -> None:
    now = 0
    def cb(size: int):
        nonlocal now, data
        now += size
        data['total'] += size
        if data['size'] is not None:
            p = now / data['size']
            part2 = f'{fmt_size(data['size'])} {int(p * 100)}%'
        else:
            part2 = 'unknown'
        print(f'\r{data['count']}. {fmt_size(now)}/{part2} {fmt_size(data['total'])} ', end=' ' * 10, flush=True)

    cb(0)

    try:
        for unit in [one_g, half_g, one_m, half_m, one_k, half_k, one_byte]:
            max_count = max_one_file // unit # 最大单文件
            i = 0
            while True:
                file_path = os.path.join(path, f'disk_test_{unit}_{i}.dat')
                if not write_until_no_left(file_path, unit, cb, max_count=max_count):
                    break
                i += 1
    except OSError as e:
        if 'No space left on device' not in str(e):
            raise e

    data['size'] = now

idx_file = os.path.join(os.path.dirname(__file__), 'idx.json')

def load_idx(path: str) -> tuple[dict[str, dict], dict]:
    try:
        with open(idx_file, 'r') as f:
            all_data = json.load(f)
    except FileNotFoundError:
        all_data = {}

    if path not in all_data:
        all_data[path] = {
            'size': None,
            'count': 0,
            'total': 0
        }
    return all_data, all_data[path]

def save_idx(oth: dict[str, dict], path: str, data: dict) -> None:
    oth[path] = data
    with open(idx_file, 'w') as f:
        json.dump(oth, f, indent=4)

def clean(path: str, deep: bool=False) -> None:
    if deep:
        import shutil
        shutil.rmtree(path)
        return

    for file in os.listdir(path):
        try:
            os.remove(os.path.join(path, file))
        except (FileNotFoundError, IsADirectoryError):
            pass

def write_disk(path: str) -> None:
    max_one_file = one_g # 1GB
    dir_path = os.path.join(path, 'disk_test')
    os.makedirs(dir_path, exist_ok=True)
    oth, data = load_idx(path)
    data['count'] += 1

    while True:
        try:
            write_until_disk_full(dir_path, data, max_one_file=max_one_file)
        except KeyboardInterrupt:
            break

        clean(dir_path)

        save_idx(oth, path, data)
        data['count'] += 1

    print('\n中断')
    clean(dir_path, deep=True)
    data['count'] -= 1
    save_idx(oth, path, data)

if __name__ == '__main__':
    write_disk('/Volumes/Lenovo K120')
