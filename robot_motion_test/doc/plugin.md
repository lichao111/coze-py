# plugin

| 函数名称           | 参数示例                                   | 返回值示例                        | 功能说明                                                                                  |
|--------------------|--------------------------------------------|-----------------------------------|-------------------------------------------------------------------------------------------|
| robot_report       | {"target": "建图任务"}                     | None    | 解析 JSON 字符串，获取 target 字段，进行语音播报                                          |
| robot_mapping      | None                     | {"response": "建图已开始"}        | 开启建图，返回成功失败状态，返回值会进行语音播报                                          |
| robot_rechargeing  | None                     | {"response": "回充已开始"}        | 开启回充，返回成功失败状态，返回值会进行语音播报                                          |
| robot_navigate     | {"target": "厨房"}                         | {"response": "已开始前往厨房"}    | 解析 JSON 字符串，获取 target 字段得到目标点名称，返回值会进行语音播报                    |
| robot_finding      | {"target": "张三"}                         | {"response": "已开始寻找张三"}    | 解析 JSON 字符串，获取 target 字段得到寻找目标，返回值会进行语音播报                      |
| robot_tracking     |       None                   | {"response": "已开始跟随建图"}    | 开启跟随建图，返回成功失败状态，返回值会进行语音播报   |
| robot_tracking_navigation    |       {"report_info": "正在跟随您"}                   | {"response": "已开始跟随导航"}    | 跟随导航 |
| robot_cancel       | {"target": 1}                              | {"response": "建图任务已取消"}    | 结束任务，target=1：建图任务；target=2：导航任务；target=3：寻人任务；target=4：跟随建图任务； target = 5: 跟随导航任务  |
| chat_cancel       | None                             | None    | 闲聊结束 |
| open_app|{"target": 1 } | None | 打开应用，target=1：音乐；target=2：评书 |
| create_reminder|{"cron_expression": "0 0 15 * * ? *", "task_content": "吃降压药" } |  {"response": "已成功创建提醒任务"}   | 创建提醒任务 |
> 说明：所有入参均为 JSON 字符串，key 为 `target`。所有返回值均为 JSON 字符串，key 为 `response`。


