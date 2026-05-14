# weatherHelper.py 代码详解（Java开发者视角）

## 一、整体架构

这是一个 **Agent（智能代理）** 程序，核心思想是：
```
用户提问 → LLM思考 → 调用工具 → 获取结果 → 继续思考 → 给出答案
```

类似于Java中的：
```java
// 伪代码
while (步骤 < 最大步骤) {
    String llmResponse = llmClient.call(prompt);  // 调用LLM
    if (llmResponse.contains("Finish")) {
        return 提取答案(llmResponse);  // 完成
    }
    String toolResult = executeTool(llmResponse);  // 执行工具
    prompt += toolResult;  // 把结果加入上下文继续问
}
```

---

## 二、逐块解析

### 1. 导入模块

```python
import os          # 类似Java的 System.getenv()，读取环境变量
import re          # 正则表达式，和Java的 Pattern/Matcher 一样
import requests    # HTTP客户端，类似Java的 HttpClient 或 OkHttp
import httpx       # 另一个HTTP客户端，OpenAI SDK底层用的
from openai import OpenAI  # OpenAI官方SDK
from dotenv import load_dotenv  # 读取.env文件的工具
from tavily import TavilyClient  # Tavily搜索API客户端
```

**Java对比：**
```java
// Python的 import 既可以导入整个模块，也可以导入模块中的特定类
import java.util.*;           // 类似 import os
import java.util.regex.*;    // 类似 import re
```

**Python特有语法：**
- `from xxx import yyy` = 从xxx模块导入yyy（Java没有这种写法，都是import整个包）
- `as` 可以起别名，如 `import numpy as np`

---

### 2. 类定义

```python
class OpenAICompatibleClient:
    """用于调用任何兼容OpenAI接口的LLM服务的客户端"""
    
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
```

**Java对比：**
```java
public class OpenAICompatibleClient {
    private String model;
    private String apiKey;
    private String baseUrl;
    
    // Python的 __init__ 就是构造函数
    public OpenAICompatibleClient(String model, String apiKey, String baseUrl) {
        this.model = model;
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }
}
```

**Python特有语法：**
- `def __init__(self)` = 构造函数（`self` 类似Java的 `this`）
- `self.xxx` = 实例变量（Java用 `this.xxx`）
- 参数类型标注 `model: str` 是可选的，Python是动态类型语言
- 三引号 `"""..."""` = 多行字符串/文档注释

---

### 3. 方法定义

```python
def generate(self, prompt: str, system_prompt: str) -> str:
    """调用LLM API来生成回应"""
    # 清理无效的Unicode字符
    def clean_text(text):
        return text.encode('utf-8', errors='ignore').decode('utf-8')
    
    try:
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            http_client=httpx.Client(proxy="http://127.0.0.1:7890")
        )
        messages = [
            {'role': 'system', 'content': clean_text(system_prompt)},
            {'role': 'user', 'content': clean_text(prompt)}
        ]
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"调用LLM API时发生错误: {e}")
        return "错误:调用语言模型服务时出错。"
```

**Java对比：**
```java
public String generate(String prompt, String systemPrompt) {
    try {
        // Python的 OpenAI(...) = Java的 new OpenAI(...)
        OpenAIClient client = new OpenAIClient(apiKey, baseUrl);
        
        // Python的列表 [...] = Java的 List.of(...) 或 Arrays.asList(...)
        List<Message> messages = List.of(
            new Message("system", systemPrompt),
            new Message("user", prompt)
        );
        
        Response response = client.chatCompletions().create(model, messages);
        return response.getChoices().get(0).getMessage().getContent();
    } catch (Exception e) {
        System.out.println("调用LLM API时发生错误: " + e);
        return "错误:调用语言模型服务时出错。";
    }
}
```

**Python特有语法：**
- `def 函数名(参数) -> 返回类型:` （箭头 `->` 是类型标注，可选）
- `f"xxx {变量}"` = f-string格式化，类似Java的 `"xxx " + variable` 或 `String.format()`
- `try...except` = Java的 `try...catch`
- `response.choices[0]` = Java的 `response.getChoices().get(0)`（Python用 `[]` 访问）
- `httpx.Client(proxy=...)` = 命名参数，Java用 Builder 模式实现

---

### 4. 函数定义（工具函数）

```python
def get_weather(city: str) -> str:
    """通过调用 wttr.in API 查询真实的天气信息"""
    url = f"https://wttr.in/{city}?format=j1"
    proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
    
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']
        
        return f"{city}当前天气:{weather_desc}，气温{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        return f"错误:查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        return f"错误:解析天气数据失败 - {e}"
```

**Java对比：**
```java
public static String getWeather(String city) {
    String url = "https://wttr.in/" + city + "?format=j1";
    
    try {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .build();
        HttpResponse<String> response = client.send(request, BodyHandlers.ofString());
        
        // Python的 response.json() = Java的 new Gson().fromJson(response.body(), Map.class)
        Map<String, Object> data = new Gson().fromJson(response.body(), Map.class);
        
        List<Map> currentCondition = (List<Map>) data.get("current_condition");
        Map first = currentCondition.get(0);
        // ...继续解析
        
        return city + "当前天气:" + weatherDesc + "，气温" + tempC + "摄氏度";
    } catch (IOException e) {
        return "错误:查询天气时遇到网络问题 - " + e;
    }
}
```

**Python特有语法：**
- `data['current_condition']` = Java的 `data.get("current_condition")`（Python字典用 `[]` 访问）
- `data['current_condition'][0]` = 链式访问，先取值再取列表第一个
- `except (KeyError, IndexError) as e` = 同时捕获多种异常，Java要写多个catch块
- `response.json()` = 自动解析JSON为Python字典（Java需要手动用Gson/Jackson）

---

### 5. 字典（工具映射）

```python
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}
```

**Java对比：**
```java
// Python的字典 {key: value} = Java的 Map.of() 或 HashMap
Map<String, Function<String, String>> availableTools = Map.of(
    "get_weather", WeatherHelper::getWeather,
    "get_attraction", WeatherHelper::getAttraction
);
```

**Python特有语法：**
- `{key: value, ...}` = 字典（类似Java的Map）
- 函数可以作为值存储在字典里（Python中函数是一等公民）

---

### 6. 系统提示词（多行字符串）

```python
AGENT_SYSTEM_PROMPT = """你是一个智能旅行助手，可以调用以下工具来回答用户问题：

工具列表：
1. get_weather(city: str) -> str   # 查询某城市的天气
...
"""
```

**Java对比：**
```java
// Java 13+ 的文本块
String AGENT_SYSTEM_PROMPT = """
    你是一个智能旅行助手，可以调用以下工具来回答用户问题：
    
    工具列表：
    1. get_weather(city: str) -> str   # 查询某城市的天气
    ...
    """;
```

---

### 7. 主循环（Agent核心逻辑）

```python
def run_agent(user_question: str, max_steps: int = 5):
    prompt_history = [f"用户请求: {user_question}"]
    
    for i in range(max_steps):  # range(5) = 0,1,2,3,4
        full_prompt = "\n".join(prompt_history)  # 把列表拼接成字符串
        llm_output = llm.generate(full_prompt, AGENT_SYSTEM_PROMPT)
        
        # 检查是否完成
        finish_match = re.search(r'Finish\("(.+?)"\)', llm_output, re.DOTALL)
        if finish_match:
            return finish_match.group(1)  # 返回捕获组1
        
        # 解析Action
        action_match = re.search(r"Action:\s*(\w+)\((.+?)\)", llm_output, re.DOTALL)
        if not action_match:
            prompt_history.append("Observation: 错误信息")
            continue
        
        tool_name = action_match.group(1)  # 如 "get_weather"
        args_str = action_match.group(2)   # 如 'city="北京"'
        
        # 解析参数：用正则提取 key="value" 对
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))
        # 结果：{'city': '北京'}
        
        # 执行工具
        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)  # **kwargs 解包字典为参数
        
        prompt_history.append(f"Observation: {observation}")
```

**Java对比：**
```java
public String runAgent(String userQuestion, int maxSteps) {
    List<String> promptHistory = new ArrayList<>();
    promptHistory.add("用户请求: " + userQuestion);
    
    for (int i = 0; i < maxSteps; i++) {
        String fullPrompt = String.join("\n", promptHistory);
        String llmOutput = llm.generate(fullPrompt, AGENT_SYSTEM_PROMPT);
        
        // 正则匹配
        Matcher finishMatcher = Pattern.compile("Finish\\(\"(.+?)\"\\)").matcher(llmOutput);
        if (finishMatcher.find()) {
            return finishMatcher.group(1);
        }
        
        Matcher actionMatcher = Pattern.compile("Action:\\s*(\\w+)\\((.+?)\\)").matcher(llmOutput);
        if (!actionMatcher.find()) {
            promptHistory.add("Observation: 错误信息");
            continue;
        }
        
        String toolName = actionMatcher.group(1);
        String argsStr = actionMatcher.group(2);
        
        // 解析参数
        Map<String, String> kwargs = new HashMap<>();
        Matcher argMatcher = Pattern.compile("(\\w+)=\"([^\"]*)\"").matcher(argsStr);
        while (argMatcher.find()) {
            kwargs.put(argMatcher.group(1), argMatcher.group(2));
        }
        
        // 执行工具
        String observation = availableTools.get(toolName).apply(kwargs.get("city"));
        promptHistory.add("Observation: " + observation);
    }
    return null;
}
```

**Python特有语法：**
- `for i in range(max_steps)` = Java的 `for (int i = 0; i < maxSteps; i++)`
- `"\n".join(list)` = 把列表用换行符连接成字符串（Java用 `String.join()`）
- `re.search(pattern, string)` = 返回匹配结果（类似Java的 `Pattern.matcher(string).find()`）
- `match.group(1)` = 获取正则捕获组（和Java一样）
- `dict(re.findall(...))` = 把元组列表转为字典
- `**kwargs` = 解包字典作为函数参数（Java没有这种语法）
- `func(**kwargs)` 等价于 `func(city="北京")`

---

### 8. 主入口

```python
if __name__ == "__main__":
    question = input("请输入你的旅行问题：")
    run_agent(question)
```

**Java对比：**
```java
public static void main(String[] args) {
    Scanner scanner = new Scanner(System.in);
    System.out.print("请输入你的旅行问题：");
    String question = scanner.nextLine();
    runAgent(question);
}
```

**Python特有语法：**
- `if __name__ == "__main__":` = 只在直接运行此文件时执行（Java的main方法天然如此）
- `input()` = 读取用户输入（Java用 `Scanner.nextLine()`）

---

## 三、Python vs Java 速查表

| Python | Java | 说明 |
|--------|------|------|
| `def func(a, b):` | `void func(Type a, Type b)` | 函数定义 |
| `self` | `this` | 实例引用 |
| `__init__` | 构造函数 | 初始化 |
| `list = [1, 2, 3]` | `List.of(1, 2, 3)` | 列表 |
| `dict = {"a": 1}` | `Map.of("a", 1)` | 字典 |
| `for x in list:` | `for (Type x : list)` | 增强for循环 |
| `try...except` | `try...catch` | 异常处理 |
| `f"hello {name}"` | `"hello " + name` | 字符串拼接 |
| `x if condition else y` | `condition ? x : y` | 三元表达式 |
| `None` | `null` | 空值 |
| `True / False` | `true / false` | 布尔值 |
| `len(list)` | `list.size()` | 获取长度 |
| `x = a or b` | `x = (a != null) ? a : b` | 空值合并 |
| `**kwargs` | 无直接对应 | 解包字典为参数 |

---

## 四、程序执行流程图

```
用户输入: "广州天气如何，推荐怎么出行"
         ↓
    ┌─ 步骤1 ─────────────────────────────────────┐
    │  发送给LLM: "用户请求: 广州天气如何..."        │
    │  LLM返回:                                      │
    │    Thought: 需要先查天气                        │
    │    Action: get_weather(city="广州")             │
    │                                                │
    │  解析出: tool_name="get_weather", city="广州"   │
    │  执行: get_weather("广州") → "广州晴朗，28°C"   │
    │  加入历史: Observation: 广州晴朗，28°C          │
    └──────────────────────────────────────────────┘
         ↓
    ┌─ 步骤2 ─────────────────────────────────────┐
    │  发送给LLM: (包含之前的对话历史)               │
    │  LLM返回:                                      │
    │    Thought: 天气晴朗，推荐户外景点              │
    │    Action: get_attraction(city="广州", weather="晴朗") │
    │                                                │
    │  执行: get_attraction("广州", "晴朗") → "..."   │
    │  加入历史: Observation: 推荐白云山...           │
    └──────────────────────────────────────────────┘
         ↓
    ┌─ 步骤3 ─────────────────────────────────────┐
    │  发送给LLM: (包含所有历史)                     │
    │  LLM返回:                                      │
    │    Thought: 已有足够信息，给出答案              │
    │    Finish("广州天气晴朗，28°C，推荐去白云山")    │
    │                                                │
    │  检测到Finish → 提取答案 → 返回结果             │
    └──────────────────────────────────────────────┘
         ↓
    输出最终答案
```

---

## 五、关键概念解释

### 1. 为什么用 `self`？
Python要求实例方法必须显式声明 `self` 作为第一个参数，这样方法才知道是操作哪个对象。Java的 `this` 是隐式的。

### 2. 为什么函数可以存在字典里？
Python中函数是"一等公民"，可以像变量一样传递、存储。Java 8+ 也可以用 Lambda 或方法引用实现类似功能。

### 3. `**kwargs` 是什么？
这是"关键字参数解包"。当你有一个字典 `{"city": "北京"}`，用 `**` 解包后等价于 `city="北京"`。Java没有这种语法，需要手动取值传参。

### 4. 正则表达式
Python和Java的正则语法基本一样，区别是：
- Python: `re.search(pattern, string)` 返回 Match 对象或 None
- Java: `Pattern.compile(pattern).matcher(string).find()` 返回 boolean

### 5. f-string
Python 3.6+ 的字符串格式化方式，比Java的字符串拼接更优雅：
```python
f"hello {name}"  # Python
"hello " + name  # Java
```
