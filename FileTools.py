import configparser
import datetime
import os
import zipfile
import re
import config

def create_directory_if_not_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    return dir_path

def create_file_if_not_exists(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8'):
            pass  # 创建一个空文件
    return file_path

# 获取指定目录下的所有文件名
def get_all_filenames(directory):
    create_directory_if_not_exists(directory)
    filenames = []
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)):
            filenames.append(filename)
    return filenames

def file_exists(file_path):
    return os.path.exists(file_path)

# 源文件,目标地址
def zip_file(source_directory, target_file):
    with zipfile.ZipFile(target_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_directory):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, os.path.dirname(source_directory))
                zipf.write(file_path, rel_path)

# 源文件,目标地址
def unzip_file(zip_file_path, extract_dir):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)


def get_conf(file_path):
    if file_path == '':
        return {}
    # 创建 ConfigParser 实例
    ini_config = configparser.ConfigParser()

    # 读取INI文件，并指定编码方式为utf-8
    with open(file_path, encoding='utf-8') as f:
        ini_config.read_file(f)
    optionsettings = ini_config.get('/Script/Pal.PalGameWorldSettings', 'OptionSettings')
    # 使用正则表达式来匹配键值对
    pairs = re.findall(r'(\w+)=(?:"([^"]+)"|(\w+))', optionsettings)

    # 创建空字典
    result = {}

    # 遍历匹配的键值对并添加到字典中
    for key, value1, value2 in pairs:
        # 确定值的来源，优先选择双引号内的值
        value = value1 if value1 else value2
        # 根据需要转换字符串为相应类型
        if value.isdigit():
            value = int(value)
        elif value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        # 添加到字典中
        result[key] = value
    return result

def json_to_conf(data, file_path):
    pairs_list = []

    # 遍历字典中的每个键值对，并将其转换为字符串形式
    for key, value in data.items():
        # 对于布尔值，将其转换为字符串形式
        if isinstance(value, bool):
            value = str(value).lower()
        # 创建键值对字符串，并添加到列表中
        pairs_list.append(f"{key}={value}")

    # 使用逗号连接所有键值对字符串，并添加括号，形成INI文件内容
    ini_text = "(" + ",".join(pairs_list) + ")"

    # 将结果写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(ini_text)


def delete_old_files(folder_path):
    # 获取当前时间
    current_time = datetime.datetime.now()

    # 获取文件夹内所有文件的路径
    files = os.listdir(folder_path)

    # 循环遍历文件夹内的所有文件
    for file in files:
        file_path = os.path.join(folder_path, file)

        # 获取文件的最后修改时间
        modification_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

        # 计算文件的存活时间
        time_difference = current_time - modification_time

        # 如果文件存活时间大于一天，则删除文件
        if time_difference.days > config.pal_back_day:
            try:
                os.remove(file_path)
                print(f"已删除文件：{file_path}")
            except Exception as e:
                print(f"删除文件失败：{e}")

def keep_latest_files(folder_path, num_to_keep=20):
    # 获取文件夹内所有文件的路径和最后修改时间
    files = [(os.path.join(folder_path, file), os.path.getmtime(os.path.join(folder_path, file)))
             for file in os.listdir(folder_path)]

    # 根据文件的最后修改时间进行排序
    sorted_files = sorted(files, key=lambda x: x[1], reverse=True)

    # 保留最新的 num_to_keep 个文件，删除其余文件
    for i, (file_path, _) in enumerate(sorted_files):
        if i >= num_to_keep:
            try:
                os.remove(file_path)
                print(f"已删除文件：{file_path}")
            except Exception as e:
                print(f"删除文件失败：{e}")