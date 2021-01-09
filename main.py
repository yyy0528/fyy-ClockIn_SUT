import requests
import platform
import getpass
import os
import time
import json
import sys

class ClockIn:
    # Content-Length无需指定
    base_headers = {
        'Host': 'yqtb.sut.edu.cn',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Accept': None,
        'Sec-Fetch-Site': None,
        'Sec-Fetch-Mode': None,
        'Sec-Fetch-Dest': None,
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cookie': 'nginx=04c46a5a8190bd9fca20ce66931cf420'
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
            print(f'暂不支持{sys_env}')
            i = input()
            sys.exit(0)

        if recorded:
            with open(record_path, 'r') as read:
                self.login_info = json.load(read)
        else:
            while True:
                self.login_info['user_account'] = input('输入帐号:')
                self.login_info['user_password'] = input('输入密码:')
                r = self.login()
                if r['code'] == 200:
                    with open(record_path, 'w') as write:
                        json.dump(self.login_info, write)
                    break
                else:
                    print(f'帐号或密码错误, 请重新输入')

    # 获得服务器发给的 jsessionid， 将其加入Cookie中
    def add_jsessionid(self):
        url = 'https://yqtb.sut.edu.cn/login/base'

        # headers 中有些信息不是必须的(有些信息服务器不会检查), 但为了模拟真实使用浏览器打卡避免被查到，把所有header信息补全
        l_headers = self.base_headers
        l_headers['Upgrade-Insecure-Requests'] = '1'
        l_headers[
            'Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        l_headers['Sec-Fetch-Site'] = 'none'
        l_headers['Sec-Fetch-Mode'] = 'navigate'
        l_headers['Sec-Fetch-Dest'] = 'document'
        r = requests.get(url=url, headers=l_headers)
        add_cookie = r.headers['Set-Cookie']
        add_cookie = add_cookie[: add_cookie.index(';')]
        self.base_headers['Cookie'] = self.base_headers['Cookie'] + '; ' + add_cookie

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

        l_headers = self.base_headers
        l_headers['Referer'] = 'https://yqtb.sut.edu.cn/login/base'

        r = requests.post(url=url, headers=l_headers, json=self.login_info)

        return r.json()

    # 获得打卡日期json
    def get_homedate(self):
        url = 'https://yqtb.sut.edu.cn/getHomeDate'

        l_headers = self.base_headers
        l_headers['Content-Length'] = '0'
        l_headers['Referer'] = 'https://yqtb.sut.edu.cn/home'

        r = requests.post(url=url, headers=l_headers)

        return r.json()

    # 获得前一天的打卡信息
    def get_yesterday_punch_form(self, yesterday_date: str):
        url = 'https://yqtb.sut.edu.cn/getPunchForm'

        l_headers = self.base_headers
        l_headers['Referer'] = 'https://yqtb.sut.edu.cn/home'

        r = requests.post(url=url, headers=l_headers, json={'date': yesterday_date})
        return r.json()

    # 提交打卡信息
    def push_punch_form(self, now_date: str, yesterday_date: str):
        yesterday_form = self.get_yesterday_punch_form(yesterday_date)
        if yesterday_form['code'] != 200:
            print(f'获取前一天打卡信息失败: {yesterday_form}')
            i = input()
            sys.exit(0)

        url = 'https://yqtb.sut.edu.cn/punchForm'

        l_headers = self.base_headers
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

        r = requests.post(url=url, headers=l_headers, json=true_form)

        return r.json()

    def clock_in(self):
        self.add_jsessionid()
        self.get_user_info()

        login_res = self.login()
        if login_res['code'] != 200:
            print(f'登录失败: {login_res}')
            i = input()
            sys.exit(0)

        getreq_res = self.get_homedate()
        latest_date_json = getreq_res['datas']['hunch_list'][0]
        if getreq_res['code'] != 200:
            print(f'获取打卡时间表失败: {getreq_res}')
            i = input()
            sys.exit(0)
        elif latest_date_json['state'] == 1:
            sys.exit(0)

        push_res = self.push_punch_form(latest_date_json['date1'], getreq_res['datas']['hunch_list'][1]['date1'])
        if push_res['code'] != 200:
            print(f'打卡信息提交失败: {push_res}')
            i = input()
            sys.exit(0)

        print('打卡成功')


if __name__ == '__main__':
    t = time.localtime(time.time())
    if t.tm_hour < 10:
        sys.exit(0)

    for i in range(3):
        ping_res = 0
        if platform.system() == 'Linux':
            ping_res = os.system('ping www.baidu.com -c 3')
        elif platform.system() == 'Windows':
            ping_res = os.system('ping www.baidu.com')
        if ping_res and i == 2:
            print(f'网络连接失败, 程序终止')
            i = input()
            sys.exit(0)
        elif ping_res:
            print(f'网络连接失败, 5秒后进行第{i + 1}次重连')
            time.sleep(5)
        else:
            break

    print('网络连接成功', '\n', '正在打卡...')
    c = ClockIn()
    c.clock_in()
