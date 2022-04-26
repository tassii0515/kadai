import datetime
log_path ="log.log"
output_path = "output.log"
N = 1
m = 0
t = 500
memory = {}
accident_memory = {}
heavy_memory = {}

def load_log(log_path):
    # ログファイルの読み込み
    log_data = []
    with open(log_path) as f:
        for i in f:
            log_data.append(i.rstrip("\n").split(","))
    return log_data

def write_log_accident(address, period, accident):
    # ログファイルに故障を書き込み
    with open(output_path, mode='a', encoding='utf-8') as f:
        f.write(f"{address} が {accident} から {period} 間故障していました。\n")

def write_log_heavy(address, period, oldtime):
    # ログファイルに通信の負荷を書き込み
    with open(output_path, mode='a', encoding='utf-8') as f:
        f.write(f"{address} が {oldtime} から {period} 間過負荷状態になっていました。\n")

def to_date(date):
    # 文字列を date 型に変換
    date = datetime.datetime.strptime(date, '%Y%m%d%H%M%S')
    return date

def make_info(data):
    time = to_date(data[0])
    mode = True
    # 数値かどうか
    if data[2].isdigit():
        mode = False
    info = [mode, (time, data[2])]
    return info

def follow_log(log_data):
    # 故障の時間を追う
    for i in reversed(log_data):
        if i[0]:
            tmp = i[1][0]
        else:
            break
    return tmp

def is_heavy(adress_data, address, info):
    count = 0
    time_sum = 0
    for i in reversed(adress_data):
        try:
            # 応答時間の合計値を求める
            time_sum += int(i[1][1])
            count += 1
            old_time = i[1][0]
        # - の場合カウントしないで１つ分さらにさかのぼる
        except ValueError as e:
            pass
        if m < count:
            break
    ave_time = time_sum/count

    if ave_time < t:
        # 重い通信ではない
        if heavy_memory[address][0]:
            print(info[1][0])
            print(heavy_memory.get(address)[1])
            tmp = info[1][0] - heavy_memory.get(address)[1]
            push_log_heavy(address, tmp, heavy_memory.get(address)[1])
    else:
        # 重いデータの更新
        if heavy_memory.get(address)[0]:
            pass
        else:
            heavy_data = (True, old_time)
            heavy_memory[address] = heavy_data
            print(heavy_memory.get(address))

def push_log_heavy(address, tmp, heavy_time):
    write_log_heavy(address, tmp, heavy_time)
    heavy_data = (False, 0)
    heavy_memory[address] = heavy_data
    

def log_scan(log_data):
    for i in log_data:
        address = i[1]
        info = make_info(i)
        # 新しいアドレスか
        if address in memory:
            # 前回タイムアウトしていないか
            if memory.get(address)[-1][0]:
                accident_memory[address] = accident_memory.get(address) + 1
                # 規定回数以上タイムアウトしたか
                if N < accident_memory.get(address) :
                    # 復旧したか
                    if i[2].isdigit():
                        # 復旧 した
                        accident_time = follow_log(memory.get(address))
                        period = info[1][0] - accident_time
                        write_log_accident(address, period, accident_time)
            else:
                # 前回タイムアウトしていない
                accident_memory[address] = 0
                is_heavy(memory.get(address), address, info)
            memory.get(address).append(info)

        # 新しいアドレス
        else:
            info_list = []
            heavy_list = (False, 0)
            accident_memory[address] = 0
            heavy_memory[address] = heavy_list
            info_list.append(info)
            memory[address] = info_list

if __name__ == '__main__':
    log_data = load_log(log_path)
    log_scan(log_data)
    