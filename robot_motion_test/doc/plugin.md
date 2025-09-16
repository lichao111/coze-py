# plugin

| 函数名称           | 参数示例                                   | 返回值示例                        | 功能说明                                                                                  |
|--------------------|--------------------------------------------|-----------------------------------|-------------------------------------------------------------------------------------------|
| robot_report       | {"target": "建图任务"}                     | None    | 解析 JSON 字符串，获取 target 字段，进行语音播报                                          |
| robot_mapping      | None                     | {"response": "建图已开始"}        | 开启建图，返回成功失败状态，返回值会进行语音播报                                          |
| robot_rechargeing  | None                     | {"response": "回充已开始"}        | 开启回充，返回成功失败状态，返回值会进行语音播报                                          |
| robot_navigate     | {"target": "厨房"}                         | {"response": "已开始前往厨房"}    | 解析 JSON 字符串，获取 target 字段得到目标点名称，返回值会进行语音播报                    |
| robot_finding      | {"target": "张三"}                         | {"response": "已开始寻找张三"}    | 解析 JSON 字符串，获取 target 字段得到寻找目标，返回值会进行语音播报                      |
| robot_tracking     |                          | {"response": "已开始跟随建图"}    | 开启跟随建图，返回成功失败状态，返回值会进行语音播报   |
| robot_cancel       | {"target": 1}                              | {"response": "建图任务已取消"}    | 结束任务，target=1：建图任务；target=2：导航任务；target=3：寻人任务；target=4：跟随任务  |
| chat_cancel       | None                             | None    | 闲聊结束 |
> 说明：所有入参均为 JSON 字符串，key 为 `target`。所有返回值均为 JSON 字符串，key 为 `response`。


