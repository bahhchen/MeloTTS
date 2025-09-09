from melo.api import TTS

import os
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
import hashlib

app = FastAPI()

class Voicer:
    def __init__(self, type: str):
        """
        初始化语音模型
        """
        self.type = type if type in ['EN', 'EN_V2', 'ZH'] else 'ZH'
        self.model = TTS(language=self.type, device='auto')
        self.speaker_ids = self.model.hps.data.spk2id

    def run_inference(self, text: str, speaker_names: str):
        """
        执行语音合成
        """

        # 生成文件名
        combined_text = f"{self.type}|{speaker_names}|{text}"
        hash_obj = hashlib.sha256(combined_text.encode("utf-8"))
        txt_filename = hash_obj.hexdigest()

        output_dir = "./outputs"
        output_path = os.path.join(output_dir, f"{txt_filename}.wav")
        if os.path.exists(output_path):
            return output_path

        os.makedirs(output_dir, exist_ok=True)
        self.model.tts_to_file(text, self.speaker_ids[self.type], output_path, speed=1)
        return output_path

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

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=18774, reload=True)
