import warnings
import requests
import argparse
import platform
import getpass
import getpass
import json
import sys
import os

parser = argparse.ArgumentParser()

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

    def get_user_info(self):
        args = parser.parse_args();
        if args.account or args.password:
            if args.account and args.password:
                self.login_info['user_account'] = args.account
                self.login_info['user_password'] = args.password
                return
            else:
                raise Exception("The two parameters '--account' and '--password' need to be used together")

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
            raise Exception(f'Not support {sys_env} yet')

        try:
            if recorded:
                with open(record_path, 'r') as read:
                    self.login_info = json.load(read)
            else:
                self.login_info['user_account'] = input('account:')
                self.login_info['user_password'] = getpass.getpass('password:')
                with open(record_path, 'w') as write:
                    json.dump(self.login_info, write)
        except Exception:
            raise Exception('Failed to read or write json file')

    # 获得服务器发给的 jsessionid， 将其加入Cookie中
    def add_jsessionid(self):
        url = 'https://yqtb.sut.edu.cn/login/base'

        # headers 中有些信息不是必须的(有些信息服务器不会检查), 但为了模拟真实使用浏览器打卡避免被查到，把所有header信息补全
        l_headers = self.base_headers.copy()
        l_headers['Upgrade-Insecure-Requests'] = '1'
        l_headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        l_headers['Sec-Fetch-Site'] = 'none'
        l_headers['Sec-Fetch-Mode'] = 'navigate'
        l_headers['Sec-Fetch-User'] = '?1'
        l_headers['Sec-Fetch-Dest'] = 'document'

        try:
            r = requests.get(url=url, headers=l_headers, verify=False)
        except Exception:
            raise Exception('Failed to get jsessionid')
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

        try:
            r = requests.post(url=url, headers=l_headers, json=self.login_info, verify=False)
        except Exception:
            raise Exception('Failed to get login results')

        return r.json()

    # 获得打卡日期json
    def get_homedate(self):
        url = 'https://yqtb.sut.edu.cn/getHomeDate'

        l_headers = self.base_headers.copy()
        l_headers['Content-Length'] = '0'
        l_headers['Referer'] = 'https://yqtb.sut.edu.cn/home'

        try:
            r = requests.post(url=url, headers=l_headers, verify=False)
        except Exception:
            raise Exception('Failed to get homedate form')

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
            raise Exception('Failed to login, check your account and password')

        homedate_json = self.get_homedate()
        if homedate_json['code'] != 200:
            raise Exception('Received a bad response when while getting homedate form')

        latest_date_json = homedate_json['datas']['hunch_list'][0]
        yesterday_date_json = homedate_json['datas']['hunch_list'][1]

        if latest_date_json['state'] == 0:
            if yesterday_date_json['state'] == 0:
                raise Exception("Can't get your clock-in information for yesterday")

            push_res = self.push_punch_form(
                latest_date_json['date1'], yesterday_date_json['date1'])
            if push_res['code'] != 200:
                raise Exception("Can't push clock-in form to server")


if __name__ == '__main__':
    warnings.filterwarnings('ignore')
    group = parser.add_argument_group('must be used together')
    group.add_argument('--account', '-u', help='your account used for clock-in')
    group.add_argument('--password', '-p', help="your account's password")

    cl = ClockIn()
    try:
        cl.clock_in()
        print('Success')
    except Exception as err:
        print(f'Failed to clock-in: {err}')
        sys.exit(-1)
