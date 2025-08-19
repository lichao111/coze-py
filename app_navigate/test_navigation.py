"""
This use case teaches you how to use local plugin.
"""

import json
import os
import time
from typing import List, Optional
import logging
from tqdm import tqdm

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

from cozepy import (  # noqa
    COZE_CN_BASE_URL,
    ChatEvent,
    ChatEventType,
    ChatStatus,
    Coze,
    DeviceOAuthApp,
    Message,
    MessageContentType,
    Stream,
    TokenAuth,
    ToolOutput,
)

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
    logging.info(f"Please Open: {device_code.verification_url} to get the access token")
    return device_oauth_app.get_access_token(device_code=device_code.device_code, poll=True).access_token


# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=get_coze_api_token()), base_url=get_coze_api_base())
# Create a bot instance in Coze, copy the last number from the web link as the bot's ID.
bot_id = os.getenv("COZE_BOT_ID")
# The user id identifies the identity of a user. Developers can use a custom business ID
# or a random string.
user_id = "python_test"


# These two functions are mock implementations.
class LocalPluginMocker(object):
    @staticmethod
    def navigate(task):
        # mock sleeping
        target = json.loads(task).get("target")
        #time.sleep(1)
        if target == 1:
            logging.info("==========>返回主页")
        elif target == 2:
            logging.info("==========>助浴")
        elif target == 3:
            logging.info("==========>点餐")
        elif target == 4:
            logging.info("==========>上门清洁")
        elif target == 5:
            logging.info("==========>适老化改造")
        else:
            logging.info("==========>识别失败")
        return "success"

    @staticmethod
    def get_function(name: str):
        return {
            "navigate_to": LocalPluginMocker.navigate,
        }[name]


# `handle_stream` is used to handle events. When the `CONVERSATION_CHAT_REQUIRES_ACTION` event is received,
# the `submit_tool_outputs` method needs to be called to submit the running result.
def handle_stream(stream: Stream[ChatEvent]):
    conversation_id = ''
    start = time.time()
    for event in stream:
        if event.chat != None:
            conversation_id = event.chat.conversation_id
        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
            end = time.time()
            logging.info(f"message delta time cost {end - start} seconds")
            logging.info(f"message: {event.message.content}")

        if event.event == ChatEventType.CONVERSATION_CHAT_REQUIRES_ACTION:
            logging.info("action time cost %s seconds", time.time() - start)
            start = time.time()
            if not event.chat.required_action or not event.chat.required_action.submit_tool_outputs:
                continue
            tool_calls = event.chat.required_action.submit_tool_outputs.tool_calls
            tool_outputs: List[ToolOutput] = []
            for tool_call in tool_calls:
                logging.info(f"function call: {tool_call.function.name} {tool_call.function.arguments}")
                local_function = LocalPluginMocker.get_function(tool_call.function.name)
                if tool_call.function.arguments == '':
                    # If the function does not require any arguments, pass an empty string.
                    output = json.dumps({"response": local_function()})
                else :
                    output = json.dumps({"response": local_function(tool_call.function.arguments)})
                tool_outputs.append(ToolOutput(tool_call_id=tool_call.id, output=output))

            handle_stream(
                coze.chat.submit_tool_outputs(
                    conversation_id=event.chat.conversation_id,
                    chat_id=event.chat.id,
                    tool_outputs=tool_outputs,
                    stream=True,
                )
            )

        if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
            logging.info("token usage: %s", event.chat.usage.token_count)


    return conversation_id


robot_nivagation_status = None

if __name__ == "__main__":
    # The intelligent entity will call LocalPluginMocker.get_schedule to obtain the schedule.
    # get_schedule is just a mock method.
    mock_input_file = os.path.join(os.path.dirname(__file__), "test_data/error.json")
    inputs = json.load(open(mock_input_file, "r", encoding="utf-8"))
    logging.info(f" inputs number: {len(inputs)}")

    result = {}
    total_count = len(inputs)
    failed_count = 0
    for input in tqdm(inputs, desc="Processing", unit="input"):
        logging.info(f"=======>inputs: {input}<=========")
        conversation_id = ''
        

        conversation_id = handle_stream(
            coze.chat.stream(
                bot_id=bot_id,
                user_id=user_id,
                additional_messages=[
                    Message.build_user_question_text(input),
                ],
                conversation_id=conversation_id,
            )
        )


        logging.info(f"=======>conversation_id: {conversation_id}<=========")

    result["total_count"] = total_count
    result["failed_count"] = failed_count
    result["success_rate"] = (total_count - failed_count) / total_count
