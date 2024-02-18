function meAlert(message) {
    alert(message);
    setTimeout(function(){
        var alertBox = document.querySelector('.alert');
        alertBox.style.opacity = 0;
        setTimeout(function(){
            alertBox.style.display = 'none';
        }, 1000);
    }, 2000);
}

const app = Vue.createApp({
    data() {
        return {
            admin: false,
            buttonsDisabled: false,
            isRunning: false, // 默认服务器未运行
            loading: false, // 控制加载动画显示与隐藏
            filenames: [],
            configurations: [], // 配置更新数据
            loadingPage: true ,
            savedList: true,
        };
    },
    mounted() {
        this.fetchData();
        this.initAdmin();
    },
    methods: {
            saveToken(){
                var token = prompt("在这里输入你的TOKEN！", '')
                if(token !== null){
                    fetch('/checkToken',{
                        headers: {
                            "Authorization": token
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if(data.success){
                            this.admin = true;
                            localStorage.setItem("admin",true);
                        }else{
                            this.admin = false;
                            localStorage.removeItem("admin")
                            meAlert("TOKEN不存在");
                        }
                    })
                    localStorage.setItem("token", token)
                }
            },
        req(url, options = {}) {
            // 设置默认请求方法为 GET
            options.method = options.method || 'GET';
            options.headers = options.headers || {};

            // 添加 token 到请求头中
            options.headers['Authorization'] = localStorage.getItem("token");

            // 如果有传入参数，则将参数添加到请求中
            if (options.data) {
                options.body = JSON.stringify(options.data);
                options.headers['Content-Type'] = 'application/json';
            }
            this.$confirm
            // 发送请求
            return fetch(url, options);
        },
        initAdmin(){
            var admin = localStorage.getItem("admin")
            if(admin == null){
                this.admin = false;
            }else{
                this.admin = admin;
            }
        },
        fetchData() {
            this.loading = true; // 显示加载动画
            this.buttonsDisabled = true;
            // 发送请求到你的接口
            fetch('/serverStatus')
                .then(response => response.json())
                .then(data => {
                    // 根据接口返回的数据设置服务器状态和样式
                    this.isRunning = data.success;
                })
                .catch(error => {
                    console.error('Error fetching data:', error);
                })
                .finally(() => {
                    this.loading = false; // 隐藏加载动画
                    this.buttonsDisabled = false;
                });
        },
        startServer() {
            this.sendRequest('/start');
        },
        stopServer() {
            if(confirm("确认关闭服务") == true){
                this.sendRequest('/shutdown');
            }
        },
        restartServer() {
            if(confirm("确认重启服务器") == true){
                this.sendRequest('/restart');
            }
        },
        sendRequest(url) {
            this.buttonsDisabled = true
            this.loading = true; // 显示加载动画
            this.req(url,{})
                .then(response => response.json())
                .catch(error => {
                    console.error('Error sending request:', error);
                })
                .finally(() => {
                    this.buttonsDisabled = false;
                    this.fetchData()
                });
        },
        savedManager(){
            this.buttonsDisabled = true
            this.loadingPage = true;
            this.req('/loadPalBack',{})
                .then(response => response.json())
                .then(data => {
                    this.filenames = data.filenames
                })
                .catch(error => {
                    console.error('Error sending request:', error);
                })
                .finally(() => {
                    this.buttonsDisabled = false;
                    this.loadingPage = false;
                });
        },
        restoreSaved(filename){
            if(confirm("确认恢复存档: [" + filename + "]\r这需要关闭服务器！") == true){
                this.loadingPage = true
                this.savedList = false
                this.req('/restoreBack',{
                    method: 'POST',
                    data: filename
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.success);
                })
                .catch(error => {
                    console.error('Error sending request:', error);
                })
                .finally(() => {
                    this.loadingPage = false;
                    this.savedList = true;
                    this.fetchData();
                });
            }
        },
        downloadSaved(filename){
            if(confirm("确认下载存档: [" + filename + "] ?") == true){
                this.loadingPage = true
                this.savedList = false
                fetch('/downloadSaved?filename=' + filename)
                .then(response => {
                    if (!response.ok) {throw new Error('下载文件失败');}
                    // 将响应转换为 blob 对象
                    return response.blob();
                })
            .catch(error => {
                console.error('下载文件失败:', error);
            })
            .finally(() => {
                    this.loadingPage = false;
                    this.savedList = true;
                });
            }
        }



    }
});

// 挂载 Vue 实例到页面中的 #app 元素
app.mount('#app');



