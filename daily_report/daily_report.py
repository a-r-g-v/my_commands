# Copyright © 2018 Yuki Mukasa. All rights reserved.
# Toggl Report から、日報提出フォームに自動でSubmitを行うコマンド
# pip depencies: requests click selenium chromedriver-binary arrow
# machine depencies: chromium(おそらく、言語がUSでないと動作しない)
# Config にクラス変数として書かれている名前について、環境変数に値が設定されている必要がある
import requests
import click
from selenium import webdriver
import chromedriver_binary
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import arrow
import os
import sys

SELENIUM_RETRIES = 10


class Config(object):
    GOOGLE_ACCOUNT_NAME = None
    GOOGLE_ACCOUNT_PASSWORD = None
    GOOGLE_FORM_URI = None
    TOGGL_WORKSPACE_ID = None
    TOGGL_PROJECT_ID = None
    TOGGL_API_KEY = None

    N = 6

    @classmethod
    def load(cls):
        d = {}
        for k, v in os.environ.items():
            if hasattr(cls, k):
                d[k] = v

        if len(d) != cls.N:
            raise RuntimeError('you should give all config values from enviroment variables')

        c = cls()
        c.__dict__.update(d)
        return c




config = Config.load()

class Report(object):
    def __init__(self, description, start, end):
        self.description = description
        self.start = start
        self.end = end

    @property
    def date(self):
        return self.start.date()

    @property
    def time(self):
        return self.start.strftime("%H:%M:%S") + " - " + self.end.strftime("%H:%M:%S")

    @property
    def delta(self):
        assert self.end >= self.start
        return self.end - self.start

    @classmethod
    def from_toggl(cls, description, start_text, end_text):
        # 2018-04-16T22:00:54+09:00
        start = arrow.get(start_text).datetime
        end = arrow.get(end_text).datetime

        if not end >= start:
            raise ValueError('the start should be less than end')

        return cls(description, start, end)

    def __repr__(self):
        return "<Report: {date} {time} ({delta}) / desc: {description} >".format(date=self.date, time=self.time, description=self.description, delta=self.delta)



class FormData(object):
    def __init__(self, date, reports, next_plan, comment):
        self._date = date
        self._reports = reports

        if not len(next_plan) > 0:
            raise ValueError('len(next_plan) shoud be greater than 0 but {l}'.format(l=len(next_plan)))
            
        self.next_plan = next_plan
        self.comment = comment

    @property
    def form_date(self):
        return self._date.strftime('%m%d%Y')

    @property
    def form_report_time(self):
        return "\n".join([ str(i) + ") " + report.time for i, report in enumerate(self._reports)])

    @property
    def form_report_description(self):
        return "\n".join([ str(i) + ") " + report.description for i, report in enumerate(self._reports)])

    @property
    def total_delta(self):
        import operator
        import functools
        return functools.reduce(operator.add, [report.delta for report in self._reports])

    @property
    def total_delta_hours_minutes_seconds(self):
        def hours_minutes(td):
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            seconds += td.microseconds / 1e6
            return hours, minutes, seconds
        return hours_minutes(self.total_delta)



    def __repr__(self):
        return "<FormData: {date}  / {time} /  {description} / delta: {total_delta} / next: {next_plan} / comment: {comment}>".format(date=self._date, time=self.form_report_time, description=self.form_report_description, total_delta=self.total_delta, next_plan=self.next_plan, comment=self.comment)




def fill_form(account_name, account_password, form_data):
    for a in range(SELENIUM_RETRIES):
        try:
            driver = webdriver.Chrome()
            break
        except ConnectionResetError:
            import time
            time.sleep(1)
            continue
    else:
        raise ConnectionResetError('too many retries had failed')


    try:
        driver.get(config.GOOGLE_FORM_URI)
        driver.implicitly_wait(5)

        try:
            # ログイン画面を対処する
            # FIXME: 例外処理が雑，identifierId で例外が送出された段階で ログイン画面ではない
            driver.find_element(By.ID, 'identifierId').send_keys(account_name + Keys.ENTER)
            driver.implicitly_wait(2)
            driver.find_element(By.NAME, 'password').send_keys(account_password + Keys.ENTER)
            driver.implicitly_wait(5)
        except selenium.common.exceptions.NoSuchElementException:
            # ログイン画面が表示されていなかった場合
            # 例えば，既にログインしているであろう場合は，継続する
            pass


        e = driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[2]/div[2]/div/div[2]/div[1]/div/div[1]/input')
        e.send_keys(form_data.form_date)
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[3]/div[2]/div[1]/div[2]/textarea').send_keys(form_data.form_report_time)
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[4]/div[2]/div[1]/div[2]/div[1]/div/div[1]/input').send_keys(str(form_data.total_delta_hours_minutes_seconds[0]))
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[4]/div[2]/div[3]/div[2]/div[1]/div/div[1]/input').send_keys(str(form_data.total_delta_hours_minutes_seconds[1]))
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[4]/div[2]/div[5]/div[2]/div[1]/div/div[1]/input').send_keys(str(form_data.total_delta_hours_minutes_seconds[2]))
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[6]/div[2]/div[1]/div[2]/textarea').send_keys(form_data.form_report_description)
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[7]/div[2]/div/content/div/label/div/div[1]/div[3]/div').click()
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[8]/div[2]/div[1]/div[2]/textarea').send_keys(form_data.next_plan)
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[9]/div[2]/div/div[1]/div/div[1]/input').send_keys(form_data.comment)
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[10]/div[2]/div/content/div/label/div/div[1]/div[3]').click()
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[2]/div[11]/div[2]/div/content/div/label/div/div[1]/div[3]').click()
        # Submit
        # FIXME: Submit に失敗した場合の処理(画面遷移しなかった場合)として，
        # ユーザに入力を促せるようにしないといけない
        driver.find_element(By.XPATH, '//*[@id="mG61Hd"]/div/div[2]/div[3]/div[1]/div/div').click()

        import time
        time.sleep(15) # FIXME: 例外処理が不完全なので，代わりにユーザに最終画面を表示させる
    finally:
        driver.close()





def report(date, api_token, workspace, project_id):
    useragent = "repoter info@arg.vc"

    since = until = date.strftime('%Y-%m-%d')

    url = "https://{api_token}:api_token@toggl.com/reports/api/v2/details?project_ids={project_ids}&workspace_id={workspace}&since={since}&until={until}&user_agent={useragent}".format(api_token=api_token, since=since, until=until, useragent=useragent, workspace=workspace, project_ids=project_id)
    data = requests.get(url).json()
    if 'data' not in data:
        return []
    
    return [ Report.from_toggl(d["description"], d["start"], d["end"]) for d in data['data']]



@click.command()
@click.option('--date', default=datetime.now().date().strftime('%Y-%m-%d'))
@click.option('--plan', required=True)
@click.option('--comment')
def main(date, plan, comment):
    date = arrow.get(date).date()
    reports = report(date, config.TOGGL_API_KEY, config.TOGGL_WORKSPACE_ID, config.TOGGL_PROJECT_ID)
    print('reports:', reports)
    if not len(reports) > 0:
        print('{date} には report がありません'.format(date=date))
        sys.exit(1)
    form_data = FormData(date, reports, plan,comment)
    fill_form(config.GOOGLE_ACCOUNT_NAME, config.GOOGLE_ACCOUNT_PASSWORD, form_data)


if __name__ == '__main__':
    main()


