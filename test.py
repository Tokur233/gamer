# IDEA: 动态更改temperature等值
# IDEA: json output
# IDEA: tool-subAI

# IDEA: 将故事生成器做成大世界探索，给玩家自由探索故事细节的选项(加入探索选项)
# IDEA: 选项加入概率机制，或根据情节会发生探索失败
# IDEA: 引入2个subAI，用于整合信息和确认生成的故事是否自洽，以确保故事的一致性 (AI 团队)
# IDEA: 增加人物塑造感和神秘感

# TODO: 测试当前的Gamer.py能生成故事且保持一致性到什么程度
# TODO: 读懂Gamer.py， 并尝试json output
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv() 


client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

def deepseek_chat(message, model="deepseek-chat", history=None):
    """
    使用 OpenAI 兼容库调用 DeepSeek API
    :param message: 用户的新消息
    :param model: 使用的模型 (默认: deepseek-chat)
    :param history: 对话历史记录 (可选)
    :return: 助手回复内容
    """

    messages = history or [
        {"role": "system", "content": "你是一位乐于助人的助手。"}
    ]
    messages.append({"role": "user", "content": message})
    
    try:

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            top_p=0.9,
            stream=False
        )
        
        assistant_reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_reply})
        
        return assistant_reply, messages
    
    except Exception as e:
        return f"API调用失败: {str(e)}", messages

if __name__ == "__main__":
    conversation_history = None
    
    while True:
        user_input = input("\n你: ")
        if user_input.lower() in ["exit", "quit"]:
            print("对话结束")
            break
            
        response, conversation_history = deepseek_chat(user_input, history=conversation_history)
        
        print(f"\nDeepSeek助手: {response}")