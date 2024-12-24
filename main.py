'''
使用说明：自己看代码吧，懒得说啦


'''
import os
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time
import sys

# 网站地址
addr = 'http://zhihui.guet.edu.cn/'


# 在这里输入爬取的账号密码
pa_id = ''
pa_password = ''

# 在这里输入答题的账号密码
qut_id = ''
qut_password = ''

# read为读写译 listen为视听说
text_name = 'listen_answer.txt'
# text_name = 'read_answer.txt'

# enter_page函数进到试题界面
def enter_page(addr, id, password, browser_name):
    driver = browser_open(browser_name)
    driver.get(addr)
    driver.maximize_window()

    ##登录账号
    time.sleep(2)
    driver.find_element(By.ID, 'name').send_keys(id)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.XPATH, '//*[@id="Submit1"]').click()

    ##进到在线测试“研究生英语界面”
    time.sleep(2)
    ###跳转到新页面
    all_handles = driver.window_handles
    driver.switch_to.window(all_handles[-1])
    driver.find_element(By.LINK_TEXT, '在线测试').click()
    time.sleep(2)

    '''
    `这里为老师的公布试题集的名称
    '''

    driver.find_element(By.LINK_TEXT, '研究生听力：Passage').click()
    # driver.find_element(By.LINK_TEXT, '研究生听力：News Report').click()
    # driver.find_element(By.LINK_TEXT, '研究生听力：Conversation').click()
    # driver.find_element(By.LINK_TEXT, '研究生听力：Recording').click()


    time.sleep(1)
    return all_handles, driver


# browser的启动
def browser_open(browser='edge'):
    '''
    使用方法：打开”firefox“、”chrome“
    driver = browser_open('firefox')   driver = browser_open('edge')
    '''
    try:
        if browser == 'edge':
            driver = webdriver.Edge()
            return driver
        elif browser == 'firefox':
            driver = webdriver.Firefox()
            return driver
        else:
            print("Not found browser! You can enter 'firefox' or 'edge'.")
    except Exception as msg:
        print("open browser error: %s", msg)

    # 爬取答案
def ans_crawing(addr, id, password, browser_name):
    answer = {}
    ans_handles, ans_driver = enter_page(addr, id, password, browser_name)

    # 点击 '我的测试' 链接
    ans_driver.find_element(By.LINK_TEXT, '我的测试').click()
    ## 获取当前页面的链接（即第一页链接）
    current_page_link = ans_driver.current_url
    WebDriverWait(ans_driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'sabrosus')))  # 等待页面加载
    # 获取所有分页链接，并过滤掉非数字的页码链接（如“上一页”和“下一页”）
    pages = ans_driver.find_elements(By.CLASS_NAME, 'sabrosus')
    # 将当前页（第一页）链接加入到页面链接列表的开头
    ans_page_links = [current_page_link] +[page.get_attribute('href') for page in pages if page.text.strip().isdigit()]

    for k in range(len(ans_page_links)):
        ans_driver.get(ans_page_links[k])
        WebDriverWait(ans_driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, '查看')))  # 等待“查看”链接出现

        # 获取所有试题链接
        exam_elems = ans_driver.find_elements(By.LINK_TEXT, '查看')

        for exam_elem in exam_elems:
            exam_elem.click()
            WebDriverWait(ans_driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="cztable"]//center/strong')))  # 等待标题加载

            # 定位到标题元素并获取标题
            ans_elem_name = ans_driver.find_element(By.XPATH, '//div[@class="cztable"]//center/strong')
            ans_name = ans_elem_name.text.strip().replace('：', '').replace(' ', '')

            # 爬取答案并进行清洗
            temp = []
            mobanhangs = ans_driver.find_elements(By.CLASS_NAME, 'mobanhang')
            for l in mobanhangs:
                temp.append(l.text.strip())

            # 答案清洗，删除无效答案
            cleaned_answers = []
            for answer_text in temp:
                if '正确答案' in answer_text:
                    answer_text = answer_text.replace('正确答案：', '').replace('\n', '').strip()
                    cleaned_answers.append(answer_text)

            if cleaned_answers:
                answer[ans_name] = cleaned_answers

            # 返回到上一个页面
            ans_driver.back()

        # 确保“查看”链接更新
        WebDriverWait(ans_driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, '查看')))

    # 关闭所有窗口
    for handle in ans_handles:
        ans_driver.switch_to.window(handle)
        ans_driver.close()

    # 将爬取的答案保存到txt文件中
    dict_to_txt(answer)

    return answer

# 将一键多值的字典写入text
def dict_to_txt(answer):
    with open(text_name, 'w') as f:
        for key in answer:
            f.write('\n')
            f.writelines(str(key) + '：' + str(answer[key]))
        f.close()


# 将text文档转成一键多值的字典导入
def txt_to_dict(text_name):
    with open(text_name, 'r', encoding='gbk') as fr:
        dict_temp = {}
        for line in fr:
            # 跳过空行
            if not line.strip():
                continue  # 如果是空行，则跳过这一行

            v = line.strip().split('：')
            v[1] = v[1].replace('[', '')
            v[1] = v[1].replace(']', '')
            v[1] = v[1].replace('\'', '')
            v[0] = v[0].replace(' ', '')
            v[0] = v[0].replace('：', '')
            v[0] = v[0].replace(':', '')
            temp_list = v[1].strip(', ').split(', ')
            dict_temp[v[0]] = temp_list
        fr.close()
    return dict_temp

# 做题
def do_exercise(addr, id, password, answer, browser_name):
    qut_handles, qut_driver = enter_page(addr, id, password, browser_name)
    wait = WebDriverWait(qut_driver, 10)
    ## 获取当前页面的链接（即第一页链接）
    current_page_link = qut_driver.current_url

    ## 爬取页数
    pages = qut_driver.find_elements(By.CLASS_NAME, 'sabrosus')

    # 移除“上一页”和“下一页”链接，只保留数字页链接
    page_links = [page.get_attribute('href') for page in pages if page.text.isdigit()]
    # 将当前页（第一页）链接加入到页面链接列表的开头
    qut_page_links = [current_page_link] + page_links  # 当前页是 current_page_link，后续页是从 page_links 获取
    # qut_page_links = page_links
    # 遍历所有页面链接
    for j in range(len(qut_page_links) ):
        qut_driver.get(qut_page_links[j])

        # 等待 "查看" 链接加载完成
        exam_elems = WebDriverWait(qut_driver, 10).until(
            EC.presence_of_all_elements_located((By.LINK_TEXT, '查看'))
        )
        handle_pages = qut_driver.current_window_handle

        # 遍历所有 "查看" 链接并点击
        for exam_elem in exam_elems:
            exam_elem.click()
            time.sleep(2)

            # 切换到新窗口
            handles = qut_driver.window_handles
            qut_driver.switch_to.window(handles[-1])

            # 等待并获取题目标题
            title_elem_name = WebDriverWait(qut_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="right_main960"]//center/strong'))
            )
            title_name = title_elem_name.text.strip().replace(' ', '').replace('：', '').replace(':', '')

            # 处理特定题目名称
            if 'AnalyticalListening2(2)' in title_name:
                title_name = title_name.replace('AnalyticalListening2(2)', 'Analy.Listening2(2)')
            elif 'AnalyticalListening2(1)' in title_name:
                title_name = title_name.replace('AnalyticalListening2(1)', 'Analy.Listening2(1)')
            elif 'AnalyticalListening1(1)' in title_name:
                title_name = title_name.replace('AnalyticalListening1(1)', 'Analy.Listening1(1)')
            elif 'AnalyticalListening1(2)' in title_name:
                title_name = title_name.replace('AnalyticalListening1(2)', 'Analy.Listening1(2)')

            if title_name.startswith('【国际学术交流英语视听说】2'):
                title_name = title_name.replace('【国际学术交流英语视听说】2', '【国际学术交流英语视听说2】')

            # 判断该题是否有答案
            if title_name in answer:
                daan_list = answer[title_name]

                # 判断该题是否已做过
                elem_tj = qut_driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_ceshis')
                if elem_tj.text != '该测试题您无法继续提交试卷':
                    # 填写答案 - 处理段落式答案
                    if 'FurtherListening3' in title_name:
                        qut_driver.find_element(By.XPATH, '/html/body/div[2]/div[3]/form/table/tbody/tr[1]/td/table/tbody/tr[5]/td/div[2]/div[2]/span/input').click()
                        frame = qut_driver.find_element(By.XPATH, '/html/body/div[2]/div[3]/form/table/tbody/tr[1]/td/table/tbody/tr[5]/td/div[2]/div[2]/div/div/div[2]/iframe')
                        qut_driver.switch_to.frame(frame)
                        elem = qut_driver.find_element(By.CLASS_NAME, 'ke-content')
                        elem.send_keys(Keys.TAB)
                        elem.send_keys(str(daan_list[0]))
                        time.sleep(1)
                        qut_driver.switch_to.default_content()

                    # 非段落式答案处理
                    else:
                        # 处理【国际学术交流英语视听说1】U1AnalyticalListening2题
                        if title_name == '【国际学术交流英语视听说1】U1AnalyticalListening2':
                            fu = 3
                            for f in range(3):
                                temp = daan_list[f]
                                daan_list.insert(fu, temp)
                                fu += 1

                        daan_elems = WebDriverWait(qut_driver, 10).until(
                            EC.presence_of_all_elements_located((By.NAME, 'setdaan'))
                        )

                        e_temp = 0
                        for e in range(len(daan_elems)):
                            if daan_elems[e_temp].get_attribute('type') == 'hidden':
                                daan_elems.remove(daan_elems[e_temp])
                            else:
                                e_temp += 1

                        # 填空题或选择题
                        for k in range(len(daan_elems)):
                            if daan_elems[k].tag_name == 'input':  # 填空题
                                daan_elems[k].send_keys(daan_list[k])

                            elif daan_elems[k].tag_name == 'select':  # 选择题
                                selector = Select(daan_elems[k])
                                if daan_list[k] == 'A':
                                    selector.select_by_value('A')
                                elif daan_list[k] == 'B':
                                    selector.select_by_value('B')
                                elif daan_list[k] == 'C':
                                    selector.select_by_value('C')
                                elif daan_list[k] == 'D':
                                    selector.select_by_value('D')
                                else:
                                    print(f'题目选项异常：{daan_elems[k].text}')
                                    sys.exit()

                    # 提交答案
                    tj_button = WebDriverWait(qut_driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'html body.index_body div.content div.right_main960 form#endfrom table tbody tr td#ctl00_ContentPlaceHolder1_ceshis div#tjing input#wanchengedn.ibut'))
                    )
                    time.sleep(2)
                    tj_button.click()
                    time.sleep(2)

                    # 处理“答题完成”弹框
                    text = qut_driver.switch_to.alert.text
                    qut_driver.switch_to.alert.accept()
                    time.sleep(3)

            qut_driver.close()
            qut_driver.switch_to.window(handle_pages)

    # 关闭所有窗口
    for handle in qut_handles:
        qut_driver.switch_to.window(handle)
        qut_driver.close()

    print("做完题啦！")
    return

if __name__ == "__main__":
    # read_answer = ans_crawing(addr,pa_id,pa_password,'edge') # 爬答案 不用的话可以注释掉
    # answer = txt_to_dict("read_answer.txt") # 读写译
    answer = txt_to_dict("listen_answer.txt") # 视听说
    # do_exercise(addr, qut_id, qut_password, answer, 'edge') #做
    os.system("pause")
