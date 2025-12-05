"""
智能任务管理助手测试 - 提醒任务和备忘录功能
"""

print("=== 开始加载 test_reminder.py ===")

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

print("=== 日志配置完成 ===")

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


print("=== get_coze_api_base 函数定义完成 ===")


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


print("=== get_coze_api_token 函数定义完成 ===")

# Init the Coze client through the access_token.
print("=== 开始初始化 Coze 客户端 ===")
coze = Coze(auth=TokenAuth(token=get_coze_api_token()), base_url=get_coze_api_base())
print("=== Coze 客户端初始化完成 ===")

# Create a bot instance in Coze, copy the last number from the web link as the bot's ID.
bot_id = os.getenv("COZE_BOT_ID")
# bot_id = "7554327088040362020"

# The user id identifies the identity of a user. Developers can use a custom business ID
# or a random string.
user_id = "python_test"


# Mock implementations for reminder tools (memo operations are handled in the cloud)
class LocalPluginMocker(object):
    @staticmethod
    def create_reminder(cron_expression: str, task_content: str):
        """创建提醒任务"""
        logging.info(f"创建提醒任务:")
        logging.info(f"  Cron表达式: {cron_expression}")
        logging.info(f"  任务内容: {task_content}")
        return json.dumps({
            "response": "已成功创建提醒任务"
        })

    @staticmethod
    def get_function(name: str):
        return {
            "create_reminder": LocalPluginMocker.create_reminder,
        }[name]


# `handle_stream` is used to handle events. When the `CONVERSATION_CHAT_REQUIRES_ACTION` event is received,
# the `submit_tool_outputs` method needs to be called to submit the running result.
def handle_stream(stream: Stream[ChatEvent]):
    conversation_id = ''
    first_replay_time = None
    assistant_message = ""
    
    for event in stream:
        if event.chat != None:
            conversation_id = event.chat.conversation_id
            
        if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
            if first_replay_time is None:
                first_replay_time = time.time()
            if event.message.content:
                assistant_message += event.message.content
                logging.info(f"message delta: {event.message.content}")

        if event.event == ChatEventType.CONVERSATION_CHAT_REQUIRES_ACTION:
            if not event.chat.required_action or not event.chat.required_action.submit_tool_outputs:
                continue
                
            tool_calls = event.chat.required_action.submit_tool_outputs.tool_calls
            tool_outputs: List[ToolOutput] = []
            
            for tool_call in tool_calls:
                logging.info(f"function call: {tool_call.function.name} {tool_call.function.arguments}")
                
                # 只处理本地工具调用（create_reminder），备忘录操作在云端执行
                try:
                    local_function = LocalPluginMocker.get_function(tool_call.function.name)
                    
                    if tool_call.function.arguments == '':
                        output = local_function()
                    else:
                        arguments = json.loads(tool_call.function.arguments)
                        output = local_function(**arguments)
                        
                    tool_outputs.append(ToolOutput(tool_call_id=tool_call.id, output=output))
                except KeyError:
                    # 备忘录相关操作在云端执行，跳过
                    logging.info(f"Tool {tool_call.function.name} is handled in the cloud, skipping local execution")
                    continue
            
            # submit tool outputs (only if there are local tool outputs)
            if tool_outputs:
                _, _ , assistant_message = handle_stream(
                coze.chat.submit_tool_outputs(
                    conversation_id=event.chat.conversation_id,
                    chat_id=event.chat.id,
                    tool_outputs=tool_outputs,
                    stream=True
                ))

        if event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
            logging.info(f"chat completed, status: {event.chat.status}")
            
    return conversation_id, first_replay_time, assistant_message


if __name__ == "__main__":
    print("=== 进入 main 函数 ===")
    # 加载测试数据
    mock_input_file = os.path.join(os.path.dirname(__file__), "test_data/input_reminder.json")
    inputs = json.load(open(mock_input_file, "r", encoding="utf-8"))
    logging.info(f"inputs number: {len(inputs)}")

    result_json = os.path.join(os.path.dirname(__file__), "test_data/result_reminder.json")
    result = {}
    
    # 统计数据
    total_count = len(inputs)
    failed_count = 0
    success_count = 0
    first_replay_time_list = []
    finish_time_list = []
    
    # 分类统计
    reminder_count = {"total": 0, "success": 0, "failed": 0}
    memo_create_count = {"total": 0, "success": 0, "failed": 0}
    memo_query_count = {"total": 0, "success": 0, "failed": 0}
    memo_update_count = {"total": 0, "success": 0, "failed": 0}
    memo_delete_count = {"total": 0, "success": 0, "failed": 0}
    
    for input_item in tqdm(inputs, desc="Processing", unit="input"):
        logging.info(f"=======>inputs: {input_item}<=========")
        conversation_id = ''
        test_type = input_item.get("type")  # "reminder", "memo_create", "memo_query", etc.
        test_message = input_item.get("message")
        expected_keywords = input_item.get("expected_keywords", [])  # 期望的关键词

        start_time = time.time()
        
        try:
            conversation_id, first_replay_time, assistant_message = handle_stream(
                coze.chat.stream(
                    bot_id=bot_id,
                    user_id=user_id,
                    additional_messages=[
                        Message.build_user_question_text(test_message),
                    ],
                    conversation_id=conversation_id,
                )
            )
            
            if first_replay_time:
                first_replay_time_list.append(first_replay_time - start_time)
            finish_time_list.append(time.time() - start_time)
            
            # 判断是否成功：检查回复中是否包含预期关键词
            is_success = True
            if expected_keywords:
                is_success = any(keyword in assistant_message for keyword in expected_keywords)
            
            if is_success:
                success_count += 1
                result[test_message] = "success"
            else:
                failed_count += 1
                result[test_message] = "failed"
                
            # 分类统计
            if test_type == "reminder":
                reminder_count["total"] += 1
                if is_success:
                    reminder_count["success"] += 1
                else:
                    reminder_count["failed"] += 1
            elif test_type == "memo_create":
                memo_create_count["total"] += 1
                if is_success:
                    memo_create_count["success"] += 1
                else:
                    memo_create_count["failed"] += 1
            elif test_type == "memo_query":
                memo_query_count["total"] += 1
                if is_success:
                    memo_query_count["success"] += 1
                else:
                    memo_query_count["failed"] += 1
            elif test_type == "memo_update":
                memo_update_count["total"] += 1
                if is_success:
                    memo_update_count["success"] += 1
                else:
                    memo_update_count["failed"] += 1
            elif test_type == "memo_delete":
                memo_delete_count["total"] += 1
                if is_success:
                    memo_delete_count["success"] += 1
                else:
                    memo_delete_count["failed"] += 1
            
            logging.info(f"first_replay_time: {first_replay_time - start_time if first_replay_time else 'N/A'}, finish_time: {time.time() - start_time}")
            logging.info(f"assistant_message: {assistant_message}")
            logging.info(f"test result: {'success' if is_success else 'failed'}")
            
        except Exception as e:
            logging.error(f"Error processing input: {e}")
            failed_count += 1
            result[test_message] = f"error: {str(e)}"
            
        logging.info(f"=======>conversation_id: {conversation_id}<=========")

    # 计算总体统计
    result["total_count"] = total_count
    result["success_count"] = success_count
    result["failed_count"] = failed_count
    result["success_rate"] = success_count / total_count if total_count > 0 else 0
    
    # 分类统计结果
    result["reminder_stats"] = reminder_count
    result["memo_create_stats"] = memo_create_count
    result["memo_query_stats"] = memo_query_count
    result["memo_update_stats"] = memo_update_count
    result["memo_delete_stats"] = memo_delete_count
    
    # 计算平均时间
    if first_replay_time_list:
        result["first_replay_time_avg"] = sum(first_replay_time_list) / len(first_replay_time_list)
    if finish_time_list:
        result["finish_time_avg"] = sum(finish_time_list) / len(finish_time_list)
    
    # 分类成功率
    if reminder_count["total"] > 0:
        result["reminder_success_rate"] = reminder_count["success"] / reminder_count["total"]
    if memo_create_count["total"] > 0:
        result["memo_create_success_rate"] = memo_create_count["success"] / memo_create_count["total"]
    if memo_query_count["total"] > 0:
        result["memo_query_success_rate"] = memo_query_count["success"] / memo_query_count["total"]
    if memo_update_count["total"] > 0:
        result["memo_update_success_rate"] = memo_update_count["success"] / memo_update_count["total"]
    if memo_delete_count["total"] > 0:
        result["memo_delete_success_rate"] = memo_delete_count["success"] / memo_delete_count["total"]
    
    # 保存结果
    json.dump(result, open(result_json, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    
    # 打印统计结果
    logging.info("\n========== 测试统计结果 ==========")
    logging.info(f"总测试数: {total_count}")
    logging.info(f"成功数: {success_count}")
    logging.info(f"失败数: {failed_count}")
    logging.info(f"总体成功率: {result['success_rate']:.2%}")
    logging.info(f"\n--- 提醒任务统计 ---")
    logging.info(f"总数: {reminder_count['total']}, 成功: {reminder_count['success']}, 失败: {reminder_count['failed']}")
    if reminder_count["total"] > 0:
        logging.info(f"成功率: {result.get('reminder_success_rate', 0):.2%}")
    logging.info(f"\n--- 备忘录创建统计 ---")
    logging.info(f"总数: {memo_create_count['total']}, 成功: {memo_create_count['success']}, 失败: {memo_create_count['failed']}")
    if memo_create_count["total"] > 0:
        logging.info(f"成功率: {result.get('memo_create_success_rate', 0):.2%}")
    logging.info(f"\n--- 备忘录查询统计 ---")
    logging.info(f"总数: {memo_query_count['total']}, 成功: {memo_query_count['success']}, 失败: {memo_query_count['failed']}")
    if memo_query_count["total"] > 0:
        logging.info(f"成功率: {result.get('memo_query_success_rate', 0):.2%}")
    logging.info(f"\n--- 备忘录更新统计 ---")
    logging.info(f"总数: {memo_update_count['total']}, 成功: {memo_update_count['success']}, 失败: {memo_update_count['failed']}")
    if memo_update_count["total"] > 0:
        logging.info(f"成功率: {result.get('memo_update_success_rate', 0):.2%}")
    logging.info(f"\n--- 备忘录删除统计 ---")
    logging.info(f"总数: {memo_delete_count['total']}, 成功: {memo_delete_count['success']}, 失败: {memo_delete_count['failed']}")
    if memo_delete_count["total"] > 0:
        logging.info(f"成功率: {result.get('memo_delete_success_rate', 0):.2%}")
    logging.info(f"\n平均首次响应时间: {result.get('first_replay_time_avg', 0):.3f}秒")
    logging.info(f"平均完成时间: {result.get('finish_time_avg', 0):.3f}秒")
    logging.info("==================================\n")
