import asyncio
import json
import logging
import os
import time
from typing import Optional

from cozepy import (
    COZE_CN_BASE_URL,
    AsyncCoze,
    AsyncTokenAuth,
    AsyncWebsocketsAudioSpeechClient,
    AsyncWebsocketsAudioSpeechEventHandler,
    DeviceOAuthApp,
    InputTextBufferAppendEvent,
    InputTextBufferCompletedEvent,
    SpeechAudioCompletedEvent,
    SpeechAudioUpdateEvent,
    setup_logging,
)
from cozepy.log import log_info
from cozepy.util import write_pcm_to_wav_file


def get_coze_api_base() -> str:
    # The default access is api.coze.cn, but if you need to access api.coze.com,
    # please use base_url to configure the api endpoint to access
    coze_api_base = os.getenv("COZE_API_BASE")
    if coze_api_base:
        return coze_api_base

    return COZE_CN_BASE_URL  # default


def get_coze_api_token(workspace_id: Optional[str] = None) -> str:
    # Get an access_token through personal access token or oauth.
    coze_api_token = os.getenv("COZE_API_TOKEN")
    if coze_api_token:
        return coze_api_token

    coze_api_base = get_coze_api_base()

    device_oauth_app = DeviceOAuthApp(client_id="57294420732781205987760324720643.app.coze", base_url=coze_api_base)
    device_code = device_oauth_app.get_device_code(workspace_id)
    print(f"Please Open: {device_code.verification_url} to get the access token")
    return device_oauth_app.get_access_token(device_code=device_code.device_code, poll=True).access_token


def setup_examples_logger():
    coze_log = os.getenv("COZE_LOG")
    if coze_log:
        setup_logging(logging.getLevelNamesMapping().get(coze_log.upper(), logging.INFO))


setup_examples_logger()

kwargs = json.loads(os.getenv("COZE_KWARGS") or "{}")


class AsyncWebsocketsAudioSpeechEventHandlerSub(AsyncWebsocketsAudioSpeechEventHandler):
    """
    Class is not required, you can also use Dict to set callback
    """

    def __init__(self):
        self.delta = []
        self.request_start_time = None
        self.request_end_time = None

    async def on_closed(self, cli: "AsyncWebsocketsAudioSpeechClient"):
        log_info("[examples] connect closed")

    async def on_input_text_buffer_completed(
        self, cli: "AsyncWebsocketsAudioSpeechClient", event: InputTextBufferCompletedEvent
    ):
        log_info("[examples] Input text buffer completed")

    async def on_speech_audio_update(self, cli: AsyncWebsocketsAudioSpeechClient, event: SpeechAudioUpdateEvent):
        self.delta.append(event.data.delta)

    async def on_error(self, cli: AsyncWebsocketsAudioSpeechClient, e: Exception):
        log_info("[examples] Error occurred: %s", e)

    async def on_speech_audio_completed(
        self, cli: "AsyncWebsocketsAudioSpeechClient", event: SpeechAudioCompletedEvent
    ):
        self.request_end_time = time.time()
        log_info("[examples] Speech audio completed")
        # 只在最后一次请求时保存文件
        if hasattr(self, 'save_last_file') and self.save_last_file:
            write_pcm_to_wav_file(b"".join(self.delta), "output.wav")
        self.delta = []

    def start_request(self):
        self.request_start_time = time.time()
        self.delta = []

    def get_request_time(self):
        if self.request_start_time and self.request_end_time:
            return self.request_end_time - self.request_start_time
        return None


async def main():
    coze_api_token = get_coze_api_token()
    coze_api_base = get_coze_api_base()

    # Initialize Coze client
    coze = AsyncCoze(
        auth=AsyncTokenAuth(coze_api_token),
        base_url=coze_api_base,
    )

    # Create event handler
    event_handler = AsyncWebsocketsAudioSpeechEventHandlerSub()

    speech = coze.websockets.audio.speech.create(
        on_event=event_handler,
        **kwargs,
    )

    # Test texts
    test_texts = [
        "你今天好吗? 今天天气不错呀",
        "请问您需要什么帮助",
        "欢迎使用语音合成服务",
        "测试文本转语音功能"
    ]

    num_runs = 100
    total_time = 0
    successful_requests = 0

    print(f"开始进行 {num_runs} 次语音合成性能测试...")
    print("=" * 60)

    # 建立一次连接，进行100次请求
    async with speech() as client:
        for i in range(num_runs):
            try:
                # 选择测试文本（循环使用）
                text = test_texts[i % len(test_texts)]
                
                # 标记是否为最后一次请求（用于保存文件）
                if i == num_runs - 1:
                    event_handler.save_last_file = True
                
                # 开始计时
                event_handler.start_request()
                
                # 发送请求
                await client.input_text_buffer_append(
                    InputTextBufferAppendEvent.Data.model_validate(
                        {
                            "delta": text,
                        }
                    )
                )
                await client.input_text_buffer_complete()
                await client.wait()
                
                # 获取请求耗时
                request_time = event_handler.get_request_time()
                if request_time:
                    total_time += request_time
                    successful_requests += 1
                    if i % 10 == 0 or i == num_runs - 1:  # 每10次或最后一次打印进度
                        print(f"[{i+1}/{num_runs}] c: {request_time:.3f}s, 文本: {text[:20]}...")
                else:
                    print(f"[{i+1}/{num_runs}] 请求失败")

            except Exception as e:
                print(f"[{i+1}/{num_runs}] 请求出错: {e}")
                continue

    print("=" * 60)
    if successful_requests > 0:
        avg_time = total_time / successful_requests
        print(f"性能测试完成!")
        print(f"总请求数: {num_runs}")
        print(f"成功请求数: {successful_requests}")
        print(f"失败请求数: {num_runs - successful_requests}")
        print(f"总耗时: {total_time:.3f}s")
        print(f"平均耗时: {avg_time:.3f}s")
        print(f"请求成功率: {(successful_requests/num_runs)*100:.1f}%")
    else:
        print("所有请求都失败了!")


if __name__ == "__main__":
    asyncio.run(main())