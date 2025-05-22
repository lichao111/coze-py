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
    def robot_report(report_info: str):
        # mock sleeping
        #time.sleep(1)
        # get target report info
        report_info = json.loads(report_info)
        report_info_target = report_info.get("target")
        logging.info(f"report: {report_info_target}")

    @staticmethod
    def robot_finding(target_json: str):
        # mock sleeping
        target = json.loads(target_json).get("target")
        logging.info(f"finding started target: {target}")
        #time.sleep(1)
        logging.info("finding finished, cost 5 seconds")
        global robot_finding_status
        robot_finding_status = "started"
        return "success"

    @staticmethod
    def robot_cancel(task):
        # mock sleeping
        target = json.loads(task).get("target")
        #time.sleep(1)
        if target == 1:
            logging.info("cancel 建图任务")
        elif target == 2:
            logging.info("cancel 导航任务")
        elif target == 3:
            logging.info("cancel 寻人任务")
            global robot_finding_status
            robot_finding_status = "stopped"
        elif target == 4:
            logging.info("cancel 跟随任务")
        else:
            logging.info("cancel 其他任务")
        return "success"

    @staticmethod
    def get_function(name: str):
        return {
            "robot_report": LocalPluginMocker.robot_report,
            "robot_finding": LocalPluginMocker.robot_finding,
            "robot_cancel": LocalPluginMocker.robot_cancel,
        }[name]


# `handle_stream` is used to handle events. When the `CONVERSATION_CHAT_REQUIRES_ACTION` event is received,
# the `submit_tool_outputs` method needs to be called to submit the running result.
def handle_stream(stream: Stream[ChatEvent]):
    conversation_id = ''
    for event in stream:
        if event.chat != None:
            conversation_id = event.chat.conversation_id
        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
            logging.info(f"message: {event.message.content}")

        if event.event == ChatEventType.CONVERSATION_CHAT_REQUIRES_ACTION:
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


robot_finding_status = None

if __name__ == "__main__":
    # The intelligent entity will call LocalPluginMocker.get_schedule to obtain the schedule.
    # get_schedule is just a mock method.
    mock_input_file = os.path.join(os.path.dirname(__file__), "test_data/input_finding.json")
    inputs = json.load(open(mock_input_file, "r", encoding="utf-8"))
    logging.info(f" inputs number: {len(inputs)}")

    result_json = os.path.join(os.path.dirname(__file__), "test_data/result_finding.json")
    result = {}
    total_count = len(inputs)
    failed_count = 0
    for input in tqdm(inputs, desc="Processing", unit="input"):
        logging.info(f"=======>inputs: {input}<=========")
        conversation_id = ''
        mapping_start_message = input.get("start")
        mapping_stop_message = input.get("stop")

        conversation_id = handle_stream(
            coze.chat.stream(
                bot_id=bot_id,
                user_id=user_id,
                additional_messages=[
                    Message.build_user_question_text(mapping_start_message),
                ],
                conversation_id=conversation_id,
            )
        )

        if robot_finding_status != "started":
            result[mapping_start_message] = "failed"
            failed_count += 1
            json

        handle_stream(
            coze.chat.stream(
                bot_id=bot_id,
                user_id=user_id,
                additional_messages=[
                    Message.build_user_question_text(mapping_stop_message),
                ],
                conversation_id=conversation_id,
            )
        )

        if robot_finding_status != "stopped":
            result[mapping_stop_message] = "failed"
            failed_count += 1
            json.dump(result, open(result_json, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
        logging.info(f"=======>conversation_id: {conversation_id}<=========")
    result["total_count"] = total_count
    result["failed_count"] = failed_count
    result["success_rate"] = (total_count - failed_count) / total_count
    json.dump(result, open(result_json, "w", encoding="utf-8"), ensure_ascii=False, indent=4)