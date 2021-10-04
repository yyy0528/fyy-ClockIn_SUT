import requests
import platform
import getpass
import os
import time
import json
import sys
import traceback


class ClockIn:
    base_headers = {
        'Host': 'yqtb.sut.edu.cn',
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36',
        'Accept': None,
        'Sec-Fetch-Site': None,
        'Sec-Fetch-Mode': None,
        'Sec-Fetch-Dest': None,
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    login_info = {}

    form_info = {
        'punch_form': {
            'mqszd': None,
            'sfybh': None,
            'mqstzk': None,
            'jcryqk': None,
            'glqk': None,
            'jrcltw': None,
            'sjhm': None,
            'jrlxfs': None,
            'xcsj': None,
            'gldd': None,
            'zddw': None
        },
        'date': None
    }

    failed_reason = ""

    def get_user_info(self):
        recorded = False
        record_path = ''
        sys_env = platform.system()
        user_name = getpass.getuser()
        if sys_env == 'Linux':
            if user_name == 'root':
                if os.path.isfile('/root/user_info.json'):
                    recorded = True
                record_path = '/root/user_info.json'
            else:
                if os.path.isfile(f'/home/{user_name}/user_info.json'):
                    recorded = True
                record_path = f'/home/{user_name}/user_info.json'
        elif sys_env == 'Windows':
            if os.path.isfile(f'C:\\Users\\{user_name}\\user_info.json'):
                recorded = True
            record_path = f'C:\\Users\\{user_name}\\user_info.json'
        else:
            self.failed_reason = f'暂不支持{sys_env}'
            sys.exit(0)

        if recorded:
            with open(record_path, 'r') as read:
                self.login_info = json.load(read)
        else:
            self.login_info['user_account'] = input('输入帐号:')
            self.login_info['user_password'] = input('输入密码:')
            with open(record_path, 'w') as write:
                json.dump(self.login_info, write)

    # 获得服务器发给的 jsessionid， 将其加入Cookie中
    def add_jsessionid(self):
        url = 'https://yqtb.sut.edu.cn/login/base'

        # headers 中有些信息不是必须的(有些信息服务器不会检查), 但为了模拟真实使用浏览器打卡避免被查到，把所有header信息补全
        l_headers = self.base_headers.copy()
        l_headers['Upgrade-Insecure-Requests'] = '1'
        l_headers[
            'Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        l_headers['Sec-Fetch-Site'] = 'none'
        l_headers['Sec-Fetch-Mode'] = 'navigate'
        l_headers['Sec-Fetch-User'] = '?1'
        l_headers['Sec-Fetch-Dest'] = 'document'
        r = requests.get(url=url, headers=l_headers, verify=False)
        cookie_info = r.cookies._cookies['yqtb.sut.edu.cn']['/']
        self.base_headers['Cookie'] = 'JSESSIONID={}; nginx={}'.format(cookie_info['JSESSIONID'].value, cookie_info['nginx'].value)

    # 登录
    def login(self):
        url = 'https://yqtb.sut.edu.cn/login'

        self.base_headers['Accept'] = '*/*'
        self.base_headers['Sec-Fetch-Site'] = 'same-origin'
        self.base_headers['Sec-Fetch-Mode'] = 'cors'
        self.base_headers['Sec-Fetch-Dest'] = 'empty'
        self.base_headers['Content-Type'] = 'application/json'
        self.base_headers['X-Requested-With'] = 'XMLHttpRequest'
        self.base_headers['Origin'] = 'https://yqtb.sut.edu.cn'

        l_headers = self.base_headers.copy()
        l_headers['Referer'] = 'https://yqtb.sut.edu.cn/login/base'

        r = requests.post(url=url, headers=l_headers, json=self.login_info, verify=False)

        return r.json()

    # 获得打卡日期json
    def get_homedate(self):
        url = 'https://yqtb.sut.edu.cn/getHomeDate'

        l_headers = self.base_headers.copy()
        l_headers['Content-Length'] = '0'
        l_headers['Referer'] = 'https://yqtb.sut.edu.cn/home'

        r = requests.post(url=url, headers=l_headers, verify=False)

        return r.json()

    # 获得前一天的打卡信息
    def get_yesterday_punch_form(self, yesterday_date: str):
        url = 'https://yqtb.sut.edu.cn/getPunchForm'

        l_headers = self.base_headers.copy()
        l_headers['Referer'] = 'https://yqtb.sut.edu.cn/home'

        r = requests.post(url=url, headers=l_headers, json={'date': yesterday_date}, verify=False)
        return r.json()

    # 提交打卡信息
    def push_punch_form(self, now_date: str, yesterday_date: str):
        yesterday_form = self.get_yesterday_punch_form(yesterday_date)
        if yesterday_form['code'] != 200:
            self.failed_reason = f'获取前一天打卡信息失败: {yesterday_form}'
            sys.exit(0)
        url = 'https://yqtb.sut.edu.cn/punchForm'

        l_headers = self.base_headers.copy()
        l_headers['Referer'] = 'https://yqtb.sut.edu.cn/home'

        # 真实的form, punch_form的值为字符串
        true_form = {
            'punch_form': '',
            'date': now_date
        }

        for field in yesterday_form['datas']['fields']:
            val = field['user_set_value']
            if val != 'null':
                self.form_info['punch_form'][field['field_code']] = val
            else:
                self.form_info['punch_form'][field['field_code']] = ''
        true_form['punch_form'] = json.dumps(self.form_info['punch_form'])

        r = requests.post(url=url, headers=l_headers, json=true_form, verify=False)

        return r.json()

    def clock_in(self):
        self.add_jsessionid()
        self.get_user_info()

        login_res = self.login()
        if login_res['code'] != 200:
            self.failed_reason = f'登录失败: {login_res}'
            sys.exit(0)

        homedate_json = self.get_homedate()
        latest_date_json = homedate_json['datas']['hunch_list'][0]
        yesterday_date_json = homedate_json['datas']['hunch_list'][1]
        if homedate_json['code'] != 200:
            self.failed_reason = f'获取打卡时间表失败: {homedate_json}'
            sys.exit(0)
        elif latest_date_json['state'] == 1:
            # 该状态为已经打卡, 只需要退出程序
            return
        elif yesterday_date_json['state'] == 0:
            self.failed_reason = '昨天你未打卡, 无法获取你的打卡信息，请今天手动打卡后再使用此脚本'
            sys.exit(0)
        push_res = self.push_punch_form(latest_date_json['date1'], yesterday_date_json['date1'])
        if push_res['code'] != 200:
            self.failed_reason = f'打卡信息提交失败: {push_res}'
            sys.exit(0)

        print('打卡成功')


if __name__ == '__main__':
    t = time.localtime(time.time())
    if t.tm_hour < 10:
        sys.exit(0)

    i = 0
    while i < 3:
        ping_res = 0
        if platform.system() == 'Linux':
            ping_res = os.system('ping www.baidu.com -c 3')
        elif platform.system() == 'Windows':
            ping_res = os.system('ping www.baidu.com')
        if ping_res and i == 2:
            print('网络连接失败, 重新连接吗？[y/n]')
            choose = 0
            while choose != 'y' and choose != 'Y' and choose != 'n' and choose != 'N':
                choose = input()
            if choose == 'y' or choose == 'Y':
                i = 0
                continue
            else:
                sys.exit(0)
        elif ping_res:
            print(f'网络连接失败, 5秒后进行第{i + 1}次重连')
            time.sleep(5)
        else:
            break
        i = i + 1

    print('网络连接成功', '\n', '正在打卡...')
    c = ClockIn()
    try:
        c.clock_in()
    except SystemExit:
        print(f"{c.failed_reason}\nfailed!")
        i = input()
    except Exception:
        traceback.print_exc()
        print("failed!")
        i = input()
