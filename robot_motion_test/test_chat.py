"""
This example is about how to use the streaming interface to start a chat request
and handle chat events
"""

import json
import logging
import os
import time
from typing import Optional, List

from cozepy import COZE_CN_BASE_URL,ChatEvent, ChatEventType, Stream,Coze, DeviceOAuthApp, Message, TokenAuth, setup_logging, ToolOutput  # noqa


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


# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=get_coze_api_token()), base_url=get_coze_api_base())

# Create a bot instance in Coze, copy the last number from the web link as the bot's ID.
# bot_id = os.getenv("COZE_BOT_ID") or "bot id"
bot_id = "7526822492665888783"
# The user id identifies the identity of a user. Developers can use a custom business ID
# or a random string.
user_id = "user id"
# Whether to print detailed logs
is_debug = os.getenv("DEBUG")

if is_debug:
    setup_logging(logging.DEBUG)

# Call the coze.chat.stream method to create a chat. The create method is a streaming
# chat and will return a Chat Iterator. Developers should iterate the iterator to get
# chat event and handle them.

def handle_stream(stream: Stream[ChatEvent]) -> None:
    """
    Handle the chat stream events.
    """
    for event in stream:
        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
            print(event.message.content, end="", flush=True)
        elif event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
            print("\nChat completed with token usage:", event.chat.usage.token_count)
        elif event.event == ChatEventType.CONVERSATION_CHAT_REQUIRES_ACTION:
            print("Chat requires action:", event.chat.required_action.submit_tool_outputs.tool_calls)

conversation_id = ""
def run_chat_stream(input: str):
    is_first_reasoning_content = True
    is_first_content = True
    global conversation_id
    start_time = time.time()
    first_replay_time = None
    for event in coze.chat.stream(
        bot_id=bot_id,
        user_id=user_id,
        additional_messages=[
            Message.build_user_question_text(input),
        ],
        conversation_id=conversation_id,
    ):
        if first_replay_time is None:
            first_replay_time = time.time() - start_time
        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
            if event.message.reasoning_content:
                if is_first_reasoning_content:
                    is_first_reasoning_content = not is_first_reasoning_content
                    print("----- reasoning_content start -----\n> ", end="", flush=True)
                print(event.message.reasoning_content, end="", flush=True)
            else:
                if is_first_content and not is_first_reasoning_content:
                    is_first_content = not is_first_content
                    print("----- reasoning_content end -----")
                print(event.message.content, end="", flush=True)

        if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
            print()
            print("token usage:", event.chat.usage.token_count)
        if event.chat != None:
            conversation_id = event.chat.conversation_id
        
        if event.event == ChatEventType.CONVERSATION_CHAT_REQUIRES_ACTION:
            tool_calls = event.chat.required_action.submit_tool_outputs.tool_calls
            tool_outputs: List[ToolOutput] = []
            for tool_call in tool_calls:
                logging.info(f"function call: {tool_call.function.name} {tool_call.function.arguments}")
                if tool_call.function.arguments == '':
                    # If the function does not require any arguments, pass an empty string.
                    output = json.dumps({"response":""})
                else :
                    output = json.dumps({"response": ""})
                tool_outputs.append(ToolOutput(tool_call_id=tool_call.id, output=output))

            handle_stream(coze.chat.submit_tool_outputs(
                conversation_id=event.chat.conversation_id,
                chat_id=event.chat.id,
                tool_outputs=tool_outputs,
                stream=True,
            ))
    finish_time = time.time() - start_time
    print(f"first_replay_time: {first_replay_time}, finish_time: {finish_time}")
    return first_replay_time, finish_time

if __name__ == "__main__":
    # Run the chat stream
    firt_time_list = []
    finish_time_list = []
    # first_time , finish_time = run_chat_stream("今天出门我遇到了张三和李四")
    # firt_time_list.append(first_time)
    # finish_time_list.append(finish_time)
    # first_time , finish_time = run_chat_stream("你能给我讲个笑话吗")
    # firt_time_list.append(first_time)
    # finish_time_list.append(finish_time)
    # first_time , finish_time = run_chat_stream("你知道我今天出门遇到了谁吗")
    # firt_time_list.append(first_time)
    # finish_time_list.append(finish_time)
    first_time , finish_time = run_chat_stream("我不想和你聊天了")
    firt_time_list.append(first_time)
    finish_time_list.append(finish_time)
    print(f"total_count: {len(firt_time_list)}, failed_count: 0, success_rate: 1.0, first_replay_time_avg: {sum(firt_time_list)/len(firt_time_list)}, finish_time_avg: {sum(finish_time_list)/len(finish_time_list)}")