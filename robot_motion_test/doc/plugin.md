# plugin
|函数名称|参数|返回值|功能说明|
|--|--|--|--|
|robot_report|report_info: string|None|解析 JSON 字符串，获取 target 字段，进行语音播报|
|robot_mapping|None|string|开启建图，返回成功失败状态，返回值会进行语音播报|
|robot_rechargeing|None|string|开启回充，返回成功失败状态，返回值会进行语音播报|
|robot_navigate|task: string|string|解析 JSON 字符串，获取 target 字段得到目标点名称，返回值会进行语音播报|
|robot_finding|task: string|string|解析 JSON 字符串，获取 target 字段得到寻找目标，返回值会进行语音播报|
|robot_tracking|task: string|string|解析 JSON 字符串，获取 target 字段得到跟随目标，返回值会进行语音播报|
|robot_cancel|task: string|string|结束任务 target=1：建图任务；target=2：导航任务；target=3：寻人任务；target=4：跟随任务|
