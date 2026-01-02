import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json
import shutil

def parse(path):
    file_paths = traverse_folder(path)
    for file_path in file_paths:
        if file_path.endswith('.xml'):
            tree = ET.parse(file_path)
            root = tree.getroot()
            root_str = ET.tostring(root).decode().replace('\n', '')
            soup = BeautifulSoup(root_str, 'xml')
            tables = soup.findAll('table-wrap')
            count = 1
            for table in tables:
                try:
                    info = {}
                    label = table.find('label').get_text()
                    title = table.find("p").get_text().replace(' ', '')
                    info[label] = title

                    # 如果 <thead> 存在，保留它，否则跳过处理
                    thead_tag = table.find('thead')
                    if thead_tag:
                        thead = str(thead_tag)
                        info['thead'] = thead
                    else:
                        info['thead'] = None

                    # 处理 <tbody> 内容
                    tbody = table.find('tbody')
                    tbody_row_list = parse_table(tbody, 'td')
                    if tbody_row_list:
                        tbody_row_list[0][0] = '<tbody>' + tbody_row_list[0][0]
                        tbody_row_list[-1][-1] = tbody_row_list[-1][-1] + '</tbody>'

                    info['tbody'] = tbody_row_list
                    table_name = f'table{count}.json'
                    save(file_path, table_name, info)
                    count += 1
                except Exception:
                    copy_fail_file(file_path)
                    break


def parse_table(tag, child):
    tr_list = []
    if tag:
        trs = tag.findAll('tr')
        for row in trs:
            td_list = []
            tds = row.findAll(child)
            for td in tds:
                td_context = f'<{child}'
                text = td.get_text()
                attrs = td.attrs
                if attrs:
                    if 'rowspan' in attrs:
                        td_context += f' rowspan={attrs["rowspan"]}'
                    if 'colspan' in attrs:
                        td_context += f' colspan={attrs["colspan"]}'
                if text:
                    td_context += f':{text.strip()}'
                td_context += f'>'
                td_list.append(td_context)
            if td_list:
                td_list[0] = '<tr>' + td_list[0]
                td_list[-1] = td_list[-1] + '</tr>'
                tr_list.append(td_list)
    return tr_list


def traverse_folder(folder_path):
    file_paths = []
    for root, dirs, files in os.walk(folder_path):
        for file_name in files:
            abs_file_path = os.path.join(root, file_name)
            file_paths.append(abs_file_path)
    return file_paths


def copy_fail_file(file_path: str):
    path = generate_path(file_path, 'Fail')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    shutil.copy(file_path, path)


def save(file_path: str, table_name: str, info):
    if info:
        path = generate_path(file_path, 'Table')
        os.makedirs(path, exist_ok=True)
        file_path_ = os.path.join(path, table_name)

        with open(file_path_, 'w', encoding='utf-8') as fp:
            json.dump(info, fp, ensure_ascii=False)


def generate_path(file_path, folder_name):
    path_ = os.path.dirname(os.path.dirname(file_path))
    file_name_ = os.path.splitext(os.path.basename(file_path))[0]
    return os.path.join(path_, folder_name, file_name_)


if __name__ == '__main__':
    path = '/Users/zixuanzhao/Desktop/UNSW/Alloy/Code/Failed-TSV-SN'
    parse(path)