from melo.api import TTS

import os
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import hashlib
import time
import traceback

import sys
import uvicorn
import xml.etree.ElementTree as ET

app = FastAPI()


# 解析 XML 文件
class Configer:
    def __init__(self):   

        xmltree = ET.parse("./conf/config.xml")
        xmlroot = xmltree.getroot()  # 根节点
        # 找到 nginx 节点
        nginx_node = xmlroot.find("nginx")
        # 再找到 port 子节点
        port_node = nginx_node.find("port")
        self.nginx_port = int(port_node.text)


        file_cache_node = xmlroot.find("file_cache")
        self.interval = int(file_cache_node.find("interval").text)
        self.files = int(file_cache_node.find("files").text)
        self.size = int(file_cache_node.find("size").text)
g_configer = Configer()

class Voicer:
    def __init__(self, type: str):
        """
        初始化语音模型
        """
        self.type = type if type in ['EN', 'EN_V2', 'ZH'] else 'ZH'
        self.model = TTS(language=self.type, device='auto')       
        self.speaker_ids = self.model.hps.data.spk2id

        self.output_dir = "./outputs"
        self._cleanup_interval = g_configer.interval  # 清理间隔，单位秒
        self._last_cleanup = 0

    def run_inference(self, text: str, speaker_names: str):
        """
        执行语音合成
        """

        # 生成文件名
        combined_text = f"{self.type}|{speaker_names}|{text}"
        hash_obj = hashlib.sha256(combined_text.encode("utf-8"))
        txt_filename = hash_obj.hexdigest()
        
        output_path = os.path.join(self.output_dir, f"{txt_filename}.wav")
        if os.path.exists(output_path):
            return output_path

        self.cleanup_dir()
        os.makedirs(self.output_dir, exist_ok=True)
        self.model.tts_to_file(text, self.speaker_ids[self.type], output_path, speed=1)
        return output_path
    

    def cleanup_dir(self, max_files=g_configer.files, max_size=g_configer.size):
        """
        清理目录中过多或过大的文件，删除最久未使用的文件

        :param max_files: 文件数量上限（超过就删除）
        :param max_size: 总文件大小上限（单位字节，超过就删除）
        """

        # 增加清理间隔控制
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return  # 距离上次清理不足，不执行

        self._last_cleanup = current_time

        if not os.path.exists(self.output_dir):
            return

        # 获取目录下所有文件的绝对路径
        files = [os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir)]
        files = [f for f in files if os.path.isfile(f)]

        # 按最后访问时间排序，最久未使用的在前面
        files.sort(key=lambda x: os.path.getatime(x))

        # 计算总大小
        total_size = sum(os.path.getsize(f) for f in files)
        total_files = len(files)

        # 删除文件，直到满足条件
        while files:
            if (total_files <= max_files) and (total_size <= max_size):
                break  # 条件满足，不用删除
            file_to_remove = files.pop(0)  # 最旧的文件
            size_removed = os.path.getsize(file_to_remove)
            os.remove(file_to_remove)
            total_size -= size_removed
            total_files -= 1
            print(f"Deleted {file_to_remove}, freed {size_removed} bytes")


# 语音合成的函数
g_voicer = None
def run_inference(type: str, text: str, speaker_names: str):

    global g_voicer  # 声明要在函数中使用/修改全局变量

    if g_voicer == None or g_voicer.type != type:
        g_voicer = Voicer(type)

    audio_file_path = g_voicer.run_inference(text, speaker_names)
    # 返回文件给前端播放
    return FileResponse(audio_file_path, media_type="audio/wav")


# POST 请求 JSON body
class SynthesisRequest(BaseModel):
    type: Optional[str] = ""
    text: str    
    speaker_names: Optional[str] = "ZL2"  # 默认值，可不传


@app.get("/synthesize")
async def synthesize_get(
    type: str = Query("", description="模型类型"),
    text: str = Query(..., description="要合成的文本"),    
    speaker_names: str = Query("ZL2", description="说话人，例如 Alice,Frank"),
):
    try:
        return run_inference(type, text, speaker_names)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/synthesize")
async def synthesize_post(req: SynthesisRequest):
    try:
        return run_inference(req.type, req.text, req.speaker_names)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    """健康检查"""
    return JSONResponse({"status": "ok"})


def start_uvicorn(app, port, host="0.0.0.0"):
    """
    启动 FastAPI/Uvicorn，兼容调试、打包和热重载

    :param app: FastAPI app 对象
    :param port: 监听端口
    :param host: 监听主机，默认 0.0.0.0
    :param reload_interval: 热重载间隔秒数，仅调试模式有效
    """
    is_frozen = getattr(sys, "frozen", False)
    should_reload = not is_frozen  # exe 禁用热重载，开发模式开启

    try:
        print(f"Starting Uvicorn on {host}:{port}, reload={should_reload}")
        uvicorn.run(
            app = "server:app" if should_reload else app,
            host=host,
            port=port,
            reload=should_reload,
            log_level="info"
        )
    except SystemExit as e:
        # 热重载触发的退出会抛 SystemExit
        if not is_frozen:
            print(f"[Debug] Uvicorn exited (SystemExit {e.code}) in debug mode, ignore")
        else:
            raise
    except Exception as e:
        print("[Error] Failed to start Uvicorn:")
        traceback.print_exc()
        if is_frozen:
            # exe 直接退出
            sys.exit(1)

if __name__ == "__main__":
    start_uvicorn(app, port=g_configer.nginx_port)
    
