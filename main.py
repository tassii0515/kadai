import datetime

log_path = "log.log"
output_path = "output.log"
N = 1 # 設問2のN
m = 1 # 設問3のm
t = 500 # 設問3のt
n = 1 # 設問4 のN
hold = 2
memory = {}
subnet_memory = {}
accident_memory = {}
subnet_accident_memory = {}
subnet_accident_lost_memory = {}
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
        f.write(f"{address} が {accident} から {period} 間サーバーが故障していました。\n")

def write_log_subnet_accident(address, period, accident):
    # ログファイルに故障を書き込み
    with open(output_path, mode='a', encoding='utf-8') as f:
        f.write(f"{address} が {accident} から {period} 間ネットワークに障害がありました。\n")
    lost_memory_list = []
    subnet_accident_lost_memory[address] = lost_memory_list

def write_log_heavy(address, period, oldtime):
    # ログファイルに通信の負荷を書き込み
    with open(output_path, mode='a', encoding='utf-8') as f:
        f.write(f"{address} が {oldtime} から {period} 間サーバーが過負荷状態になっていました。\n")

def to_date(date):
    # 文字列を date 型に変換
    date = datetime.datetime.strptime(date, '%Y%m%d%H%M%S')
    return date

def set_subnet_lost(subnet_address, subnet_lost):
    subnet_accident_lost_memory.get(subnet_address).append(subnet_lost)
    subnet_accident_lost_memory[subnet_address] = list(set(subnet_accident_lost_memory.get(subnet_address)))

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
        if m <= count:
            break
    ave_time = time_sum/count

    if ave_time < t:
        # 重い通信ではない
        if heavy_memory[address][0]:
            tmp = info[1][0] - heavy_memory.get(address)[1]
            push_log_heavy(address, tmp, heavy_memory.get(address)[1])
    else:
        # 重いデータの更新
        if heavy_memory.get(address)[0]:
            pass
        else:
            heavy_data = (True, old_time)
            heavy_memory[address] = heavy_data

def push_log_heavy(address, tmp, heavy_time):
    write_log_heavy(address, tmp, heavy_time)
    heavy_data = (False, 0)
    heavy_memory[address] = heavy_data

def make_subnet_adress(address):
    subnet,subnet_type = address.split("/")
    if subnet_type == "16":
        subnet = subnet.split(".")
        arrive = subnet[0] + "." +subnet[1]
        lost = subnet[2] + "." + subnet[3]
        return arrive, lost
    elif subnet_type == "24":
        subnet = address.split(".")
        arrive = subnet[0] + "." +subnet[1] + "." + subnet[2]
        lost = subnet[3].split("/")[0]
        return arrive, lost
    else:
        print("error")
        return address, address

def log_scan(log_data):
    for i in log_data:
        address = i[1]
        info = make_info(i)
        subnet_address, subnet_lost = make_subnet_adress(address)
        # 新しいアドレスか
        if address in memory:
            # 前回タイムアウトしていないか
            if memory.get(address)[-1][0]:
                accident_memory[address] = accident_memory.get(address) + 1
                subnet_accident_memory[subnet_address] = subnet_accident_memory.get(subnet_address) + 1
                set_subnet_lost(subnet_address, subnet_lost)

                # 規定回数以上タイムアウトしたか
                if n < subnet_accident_memory.get(subnet_address) and hold <= len(subnet_accident_lost_memory.get(subnet_address)):
                    # 復旧したか
                    if i[2].isdigit():
                        # 復旧 した
                        accident_time = follow_log(subnet_memory.get(subnet_address))
                        period = info[1][0] - accident_time
                        write_log_subnet_accident(subnet_address, period, accident_time)
                        subnet_accident_memory[subnet_address] = 0
                # 規定回数以上タイムアウトしたか
                elif N < accident_memory.get(address) :
                    # 重い通信ログを持っているか
                    if heavy_memory[address][0]:
                        tmp = info[1][0] - heavy_memory.get(address)[1]
                        push_log_heavy(address, tmp, heavy_memory.get(address)[1])
                    # 復旧したか
                    if i[2].isdigit():
                        # 復旧 した
                        accident_time = follow_log(memory.get(address))
                        period = info[1][0] - accident_time
                        write_log_accident(address, period, accident_time)
                        accident_memory[address] = 0

            else:
                # 前回タイムアウトしていない
                accident_memory[address] = 0
                subnet_accident_memory[subnet_address] = 0
                is_heavy(memory.get(address), address, info)
            memory.get(address).append(info)
            subnet_memory.get(subnet_address).append(info)

        # 新しいアドレス
        else:
            info_list = []
            info_list.append(info)
            memory[address] = info_list
            accident_memory[address] = 0

            if subnet_address in subnet_memory:
                if memory.get(address)[-1][0]:
                    subnet_accident_memory[subnet_address] = subnet_accident_memory.get(subnet_address) + 1
                    set_subnet_lost(subnet_address, subnet_lost)
                    if n < subnet_accident_memory.get(subnet_address) :
                        # 復旧したか
                        if i[2].isdigit():
                            # 復旧 した
                            accident_time = follow_log(subnet_memory.get(subnet_address))
                            period = info[1][0] - accident_time
                            write_log_subnet_accident(subnet_address, period, accident_time)
            else:
                lost_memory_list = []
                subnet_accident_lost_memory[subnet_address] = lost_memory_list
                subnet_memory[subnet_address] =info_list
                subnet_accident_memory[subnet_address] = 0
                set_subnet_lost(subnet_address, subnet_lost)

            heavy_list = (False, 0)
            heavy_memory[address] = heavy_list

if __name__ == '__main__':
    log_data = load_log(log_path)
    log_scan(log_data)