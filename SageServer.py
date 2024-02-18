import platform
import subprocess
import config
import FileTools as fileTools
from datetime import datetime, timedelta
import shutil
import psutil
import job
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__, static_folder='static', static_url_path='/')
CORS(app)

# 使用系统
osLinux = True
# 缓存配置tokens
tokens = {}
# token name
tokenName = 'tokens.conf'
# execution log name
executionLogName = 'execution.log'
# pal back dir
palBack = f"{config.workspace}/palBack"
# pal back dir
shutdown_dir = f"{config.workspace}/shutdown"
# game saved
pal_server_saved_unzip = f"{config.palServerPath}{'/Pal/Saved/'}"
pal_server_saved = f"{pal_server_saved_unzip}{'SaveGames'}"
# game saved
pal_server_config_linux = f"{config.palServerPath}/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini"
pal_server_config_win = f"{config.palServerPath}/Pal/Saved/Config/WindowsServer/PalWorldSettings.ini"
pal_server_config_update = f"{config.workspace}/PalWorldSettings_temp.ini"

pal_process_name_linux = ['PalServer-Linux-Test', 'PalServer.sh']
pal_process_name_win = ['PalServer-Win64-Test-Cmd.exe']

pal_config = {}

# 定义一个路由白名单，这些路由不需要校验 token
ROUTES_WITHOUT_TOKEN_CHECK = ['/serverStatus',
                              '/',
                              '/styles.css',
                              '/script.js',
                              '/favicon.ico',
                              '/loadPalBack',
                              '/checkToken', '/downloadSaved',
                              '/vue.global.js']

# 定义自定义异常类
class MyCustomError(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

    def to_response(self):
        response = jsonify({'error': self.message})
        response.status_code = self.status_code
        return response

# 定义一个请求钩子，在请求处理前进行校验
@app.before_request
def before_request():
    if config.debug:
        return
    # 获取请求路径
    request_path = request.path

    # 如果请求的路径不在白名单中，则需要校验 token
    if request_path not in ROUTES_WITHOUT_TOKEN_CHECK:
        # 获取请求头中的 token
        token = request.headers.get('Authorization')
        # 校验 token 的有效性
        if not token or not token in tokens:
            return jsonify({'error': 'Invalid token'}), 401
        # 记录访问日志
        log_execution(tokens[token], request.path, request.args)

def load_tokens():
    global tokens
    if tokens == {}:
        config_file = fileTools.create_file_if_not_exists(config.workspace+'/' + tokenName)
        with open(config_file, 'r', encoding='utf-8') as f:
            tokens = {line.split(':')[1].strip(): line.split(':')[0].strip() for line in f}

# 记录执行日志
def log_execution(name, action, args):
    file_path = f"{config.workspace}/{executionLogName}"
    log_file = fileTools.create_file_if_not_exists(file_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 写入日志
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp}: {name} - {action} - {args}\n")

#执行系统脚本
def execution_script(headers, scriptName, runName, args):
    # 执行脚本人名称
    name = ''
    try:
        if not headers.get('Authorization'):
            name = 'DEBUG'
        else:
            name = tokens[headers.get('Authorization')]
        execution_script_not_check(scriptName, args)
    except MyCustomError as e:
        raise MyCustomError(e.message, e.status_code)
    except Exception as e:
        # 如果命令执行失败，则捕获异常并处理
        error_output = e.output.strip()  # 移除输出中的换行符和空格
        # 记录执行日志
        log_execution(name, runName + "[ " + error_output + " ]", args)
        raise MyCustomError(error_output, 401)

def execution_script_not_check(scriptName, args):
    # 区分文件目录
    if scriptName.endswith('.sh'):
        script_directory = 'shell'
    elif scriptName.endswith('.bat'):
        script_directory = 'bat'
    else:
        raise MyCustomError("Unsupported script file!", 401)
    # 构建脚本路径
    script_path = f"{config.workspace}/{script_directory}/{scriptName} {args}" if args else f"{config.workspace}/{script_directory}/{scriptName}"
    # 执行脚本
    arguments = args.split(' ')
    if script_directory == 'shell':
        subprocess.run(["sh", f"{config.workspace}/{script_directory}/{scriptName}"] + arguments, check=True)
    elif script_directory == 'bat':
        subprocess.check_output(script_path, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)

# 根据进程名称结束
def kill_process(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            pid = proc.info['pid']
            psutil.Process(pid).terminate()
            print(f"进程 {process_name} (PID: {pid}) 已结束")
            return
    print(f"找不到名为 {process_name} 的进程")

# 检测进程是否存在
def process_is_run():
    process_names = pal_process_name_linux if osLinux else pal_process_name_win
    for process_name in process_names:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                return True
    return False

# 内存监控
def available():
    # 获取系统内存信息
    memory = int(psutil.virtual_memory().available / (1024 ** 2))
    if(memory < config.memory):
        # 打印当前剩余内存（以MB为单位）
        print(f"当前剩余内存: {memory:.2f} MB. 正在重启...")
        restart_server()

@app.route('/loadPalBack', methods=['GET'])
def list_files():
    try:
        # 获取文件列表
        filenames = fileTools.get_all_filenames(palBack)
        # 按照时间倒序排列文件列表
        sorted_filenames = sorted(filenames, key=lambda x: x.replace('Saved_', '').replace('.zip', ''), reverse=True)
        # 返回 JSON 格式的文件名数据
        return jsonify({'filenames': sorted_filenames}), 200
    except Exception as e:
        return str(e), 500

def save_back(is_shutdown):
    # 格式化时间为指定格式
    current_time = datetime.now().strftime("%Y-%m-%d_%H.%M")

    if is_shutdown:
        target_name = f"{shutdown_dir}/Shutdown_Saved_{current_time}.zip"
        fileTools.create_directory_if_not_exists(shutdown_dir)
        fileTools.keep_latest_files(shutdown_dir)
    else:
        target_name = f"{palBack}/Saved_{current_time}.zip"
        fileTools.create_directory_if_not_exists(palBack)
        fileTools.delete_old_files(palBack)

    print(f"Save back {target_name}")
    if osLinux:
        fileTools.zip_file(pal_server_saved, target_name)
    else:
        execution_script_not_check('back.bat', f"{pal_server_saved} {target_name}")

@app.route('/restoreBack', methods=['POST'])
def restore_back():
    fileName = request.json
    # 关闭服务器
    shutdown_server()

    file_path = f"{palBack}/{fileName}"
    # 检测备份文件是否存在
    if not fileTools.file_exists(file_path):
        return jsonify({'error': f"备份文件不存在 [{file_path}]"}), 200

    # 移除原存档
    if fileTools.file_exists(pal_server_saved):
        shutil.rmtree(pal_server_saved)

    # 解压到存档位置
    fileTools.unzip_file(file_path, pal_server_saved_unzip)
    return jsonify({'success': f"存档已恢复至 [{fileName}] "}), 200

@app.route('/downloadSaved', methods=['GET'])
def download_file():
    file_name = request.args.get('filename')
    # 指定要下载的文件路径
    file_path = f"{palBack}/{file_name}"  # 替换为你的文件路径
    # 使用 Flask 的 send_file 函数发送文件
    return send_file(file_path, as_attachment=True)

@app.route('/start', methods=['GET'])
def start_server():
    try:
        with app.app_context():
            if (process_is_run()):
                return jsonify({'success': '服务正在运行中！'}), 200
            if osLinux:
                execution_script_not_check('startPalServer.sh', f"{config.palServerPath}/PalServer.sh {config.startArgs}")
            else:
                subprocess.Popen(f'"{config.palServerPath}/PalServer.exe" {config.startArgs}', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 close_fds=True)
            while not process_is_run():
                return jsonify({'success': '服务启动成功！'}), 200
    except MyCustomError as e:
        return jsonify({'error': e.message}), e.status_code


@app.route('/shutdown', methods=['GET'])
def shutdown_server():
    try:
        with app.app_context():
            process_names = pal_process_name_linux if osLinux else pal_process_name_win
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] in process_names:
                    print(f"结束进程 {proc.info['pid']} - {proc.info['name']}")
                    proc.kill()
            save_back(True)
            return jsonify({'success': '服务已停止'}), 200
    except MyCustomError as e:
        return jsonify({'error': e.message}), e.status_code

@app.route('/restart', methods=['GET'])
def restart_server():
    try:
        with app.app_context():
            shutdown_server()
            start_server()
            return jsonify({'success': '重启成功'}), 200
    except MyCustomError as e:
        return jsonify({'error': e.message}), e.status_code

# 加载配置文件
def loading_config():
    global pal_config
    if osLinux:
        pal_config = fileTools.get_conf(pal_server_config_linux)
    else:
        pal_config = fileTools.get_conf(pal_server_config_win)

@app.route('/loadPalConfig', methods=['GET'])
def get_pal_config():
    if pal_config == '':
        loading_config()
    return jsonify({'success': pal_config}), 200

@app.route('/updateConfg', methods=['GET'])
def update_config(confs):
    for k, v in confs.items():
        if k in confs:
            pal_config[k] = v
    fileTools.json_to_conf(pal_config, pal_server_config_update)
    return jsonify({'success': '更新成功,重启后生效'}), 200

@app.route('/serverStatus', methods=['GET'])
def server_status():
    try:
        return jsonify({'success': process_is_run()}), 200
    except Exception as e:
        return jsonify({'error': e}), 500

@app.route('/checkToken', methods=['GET'])
def check_token():
    token = request.headers.get('Authorization')
    # 校验 token 的有效性
    if not token or not token in tokens:
        return jsonify({'success': False}), 200
    return jsonify({'success': True}), 200


def init():
    global osLinux
    # 创建工作空间
    fileTools.create_directory_if_not_exists(config.workspace)
    osLinux = True if platform.system() == 'Linux' else False
    #loading_config()
    load_tokens()
    job.run()

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    init()
    available()
    app.run(host='0.0.0.0', port=8080)

