from rcon.source.proto import Packet
from rcon.source import Client
from rcon.exceptions import WrongPassword, EmptyResponse, UserAbort


class TestRcon:
    def __init__(self, rcon_host, rcon_port, rcon_passwd):
        self.rcon_host = rcon_host
        self.rcon_port = rcon_port
        self.rcon_passwd = rcon_passwd

    def patched_run(self, command: str, *args: str, encoding: str = "utf-8") -> str:
        """Patched run method that ignores SessionTimeout exceptions."""
        request = Packet.make_command(command, *args, encoding=encoding)
        response = self.communicate(request)

        return response.payload.decode(encoding)

    Client.run = patched_run

    def send_command(self, command):
        try:
            with Client(host=self.rcon_host,
                        port=self.rcon_port,
                        passwd=self.rcon_passwd,
                        timeout=30) as client:
                response = client.run(command)
                client.close()
            return True, response
        except WrongPassword:
            return False, "[ RCON ] RCON密码错误,请检查相关设置"
        except EmptyResponse:
            return False, "[ RCON ] 服务器响应为空"
        except UserAbort:
            return False, "[RCON] 用户中断"
        except TimeoutError:
            return False, "[ RCON ] RCON连接超时"
        except ConnectionResetError:
            return False, "[ RCON ] 连接已被远程主机关闭，请重新连接RCON"
        except ConnectionRefusedError:
            return False, "[ RCON ] 连接已被远程主机拒绝"
        except Exception as e:
            return False, f"[ RCON ] 未知错误: {str(e)}"


if __name__ == '__main__':
    rcon = TestRcon(
        rcon_host="139.9.44.222",
        rcon_port=25575,
        rcon_passwd="zp@1234"
    )
    result, response = rcon.send_command("save")
    print(result, response)
