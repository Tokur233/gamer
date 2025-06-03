# -*- coding: utf-8 -*-
import streamlit as st
import requests
import json

# ==================================================
# 后端交互部分：状态管理与DeepSeek API集成
# ==================================================

# 初始化session状态 - 后端状态管理
def init_session_state():
    if "story_path" not in st.session_state:
        st.session_state.story_path = []
    if "worldview" not in st.session_state:
        st.session_state.worldview = ""
    if "current_story" not in st.session_state:
        st.session_state.current_story = ""
    if "choices" not in st.session_state:
        st.session_state.choices = []

# DeepSeek API调用函数 - 核心后端交互
def call_deepseek_api(prompt, max_tokens=1024):
    """
    与DeepSeek API交互的后端函数
    返回格式：{"story": "文本", "choices": ["选项1", "选项2", "选项3"]}
    """
    # 检查API密钥是否存在
    if not st.session_state.get("api_key"):
        st.error("请先在侧边栏输入有效的DeepSeek API密钥")
        return {"story": "API密钥缺失", "choices": []}
    
    try:
        # 设置API请求参数
        api_url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {st.session_state.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的故事创作助手，擅长创建引人入胜的叙事和分支情节"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": max_tokens,
            "top_p": 0.9
        }
        
        # 修复：明确使用UTF-8编码
        response = requests.post(
            api_url, 
            headers=headers, 
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8')
        )
        response_data = response.json()
        
        # 检查API响应是否有效
        if response.status_code != 200:
            error_msg = response_data.get("error", {}).get("message", "未知错误")
            st.error(f"DeepSeek API错误 ({response.status_code}): {error_msg}")
            return {"story": "API请求失败", "choices": []}
        
        # 提取生成的文本内容
        content = response_data["choices"][0]["message"]["content"].strip()
        
        # 解析响应内容 - 将内容分为故事和选项
        story_segment = content
        choices = []
        
        # 尝试查找选项分隔符
        option_markers = ["选项:", "选择:", "可能的后续发展:"]
        for marker in option_markers:
            if marker in content:
                parts = content.split(marker, 1)
                story_segment = parts[0].strip()
                options_text = parts[1].strip()
                
                # 提取选项（假设每行一个选项）
                choices = [line.strip() for line in options_text.split("\n") if line.strip()]
                # 只取前三个选项
                choices = choices[:3]
                break
        
        # 如果没有找到明确选项，尝试生成默认选项
        if not choices:
            choices = ["继续故事", "探索新方向", "解决当前冲突"]
        
        return {"story": story_segment, "choices": choices}
    
    except Exception as e:
        st.error(f"与DeepSeek API交互时出错: {str(e)}")
        return {"story": "请求失败，请重试", "choices": []}
# ==================================================
# 前端部分：用户界面与交互
# ==================================================

# 页面配置 - 前端UI设置
st.set_page_config(
    page_title="AI故事生成器 - DeepSeek版",
    page_icon="📖",
    layout="centered"
)

# 初始化状态
init_session_state()

# 页面标题 - 前端UI
st.title("🎭 DeepSeek互动故事生成器")
st.caption("使用DeepSeek API创建你的专属故事世界，通过选择影响故事走向")

# 侧边栏配置 - 前端UI
with st.sidebar:
    st.header("⚙️ DeepSeek设置")
    
    # API密钥输入 - 前端UI
    api_key = st.text_input("DeepSeek API密钥", 
                           type="password", 
                           help="从DeepSeek平台获取您的API密钥")
    
    if api_key:
        st.session_state.api_key = api_key
    
    # 模型参数调整 - 前端UI
    st.subheader("高级设置")
    temperature = st.slider("创意度", 0.1, 1.0, 0.7, 
                           help="控制生成内容的随机性，值越高越有创意")
    max_tokens = st.slider("最大长度", 256, 2048, 1024, 
                          help="控制生成内容的最大长度")
    
    # 故事历史展示 - 前端UI
    if st.session_state.story_path:
        st.subheader("📜 故事路径")
        for i, segment in enumerate(st.session_state.story_path):
            if i > 0:
                st.caption(f"你的选择: {segment.get('choice', '')}")
            st.write(segment["segment"][:100] + "...")
            st.divider()

# ==================================================
# 世界观创建区域 - 前端UI+交互
# ==================================================
st.header("🌍 世界观创建")
worldview_option = st.radio("选择世界观生成方式:", 
                           ["手动输入", "AI生成"],
                           horizontal=True)

if worldview_option == "手动输入":
    # 文本输入框 - 前端UI
    st.session_state.worldview = st.text_area(
        "输入世界观背景:",
        height=200,
        value=st.session_state.worldview,
        placeholder="例如：赛博朋克未来世界，人类与AI共生...",
        help="详细描述故事发生的世界背景"
    )
else:
    # 关键词输入 - 前端UI
    keywords = st.text_input("输入关键词（用逗号分隔）",
                           placeholder="例如：剑与魔法、克苏鲁等等")
    
    # 生成按钮 - 前端交互
    if st.button("生成世界观", key="generate_worldview"):
        if keywords:
            with st.spinner("DeepSeek正在创作世界观..."):
                # 构建提示词 - 前端到后端的桥梁
                prompt = f"根据这些关键词创建一个详细且引人入胜的世界观：{keywords}"
                # 触发后端交互
                result = call_deepseek_api(prompt, max_tokens)
                st.session_state.worldview = result["story"]
        else:
            st.warning("请输入关键词")

# 世界观展示 - 前端UI
if st.session_state.worldview:
    st.subheader("当前世界观")
    st.info(st.session_state.worldview)

# ==================================================
# 故事生成区域 - 前端UI+交互
# ==================================================
st.header("📖 故事发展")

# 初始故事生成
if st.session_state.worldview and not st.session_state.current_story:
    # 开始按钮 - 前端交互
    if st.button("开始故事", type="primary", key="start_story"):
        with st.spinner("DeepSeek正在创作故事..."):
            # 构建提示词 - 前端到后端的桥梁
            prompt = f"""
            基于以下世界观生成一个引人入胜的故事开头：
            世界观：{st.session_state.worldview}
            要求：
            1. 故事开头约300字
            2. 在故事结尾处提供3个明确的后续发展选项
            3. 选项用"选项1："、"选项2："等明确标注
            """
            # 触发后端交互
            response = call_deepseek_api(prompt, max_tokens)
            st.session_state.current_story = response["story"]
            st.session_state.choices = response["choices"]
            st.session_state.story_path.append({
                "segment": st.session_state.current_story,
                "choices": st.session_state.choices
            })

# 当前故事展示 - 前端UI
if st.session_state.current_story:
    st.subheader("当前剧情")
    # 故事内容展示
    st.write(st.session_state.current_story)
    st.divider()

    # 选项按钮 - 前端交互
    if st.session_state.choices:
        st.subheader("接下来会发生什么？")
        
        # 使用列布局展示选项
        cols = st.columns(len(st.session_state.choices))
        for i, choice in enumerate(st.session_state.choices):
            with cols[i]:
                if st.button(choice, key=f"choice_{i}", use_container_width=True):
                    with st.spinner("DeepSeek正在推进故事..."):
                        # 构建提示词 - 前端到后端的桥梁
                        prompt = f"""
                        根据以下信息继续故事：
                        世界观：{st.session_state.worldview}
                        当前故事：{st.session_state.current_story}
                        用户选择：{choice}
                        
                        要求：
                        1. 续写200-300字的故事
                        2. 在结尾处提供3个明确的新选项
                        3. 保持故事连贯性和吸引力
                        """
                        # 触发后端交互
                        response = call_deepseek_api(prompt, max_tokens)
                        
                        # 更新状态 - 后端状态管理
                        st.session_state.current_story = response["story"]
                        st.session_state.choices = response["choices"]
                        st.session_state.story_path.append({
                            "segment": response["story"],
                            "choice": choice,
                            "choices": response["choices"]
                        })
                    st.rerun()

# ==================================================
# 控制按钮 - 前端交互
# ==================================================
if st.session_state.story_path:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("重新开始", type="secondary"):
            # 重置状态 - 后端状态管理
            st.session_state.story_path = []
            st.session_state.current_story = ""
            st.session_state.choices = []
            st.rerun()
    
    with col2:
        # 导出故事 - 前端功能
        story_text = "\n\n".join(
            [f"段落 {i+1}:\n{seg['segment']}\n" + 
             (f"你的选择: {seg.get('choice', '初始故事')}\n" if i > 0 else "")
             for i, seg in enumerate(st.session_state.story_path)]
        )
        
        st.download_button(
            "导出故事",
            data=story_text,
            file_name="DeepSeek故事.txt",
            mime="text/plain"
        )

# ==================================================
# 前端辅助UI元素
# ==================================================
st.divider()
st.caption("提示：每次选择后会生成新的故事段落和选项，可以无限延续故事线")

# 添加使用说明
with st.expander("使用说明"):
    st.markdown("""
    **使用指南:**
    1. 在侧边栏输入您的DeepSeek API密钥
    2. 创建世界观 - 手动输入或让AI生成
    3. 点击"开始故事"生成第一个故事段落
    4. 从提供的选项中选择故事发展方向
    5. 可以随时导出故事或重新开始
    
    **提示:**
    - 在高级设置中调整创意度和生成长度
    - 世界观描述越详细，生成的故事越连贯
    - 如果选项不理想，可以尝试重新生成
    """)