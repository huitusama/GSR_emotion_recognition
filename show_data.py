import os
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
from db_connector import get_connection
from datetime import datetime
from collections import defaultdict


def get_data_from_db():
    """从数据库获取所有情绪记录数据"""
    conn = get_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute("SELECT ID, start_time, end_time, emotional_state FROM gsr_records")
    data = cursor.fetchall()
    conn.close()
    return data


def analyze_emotion_data(data):
    """分析情绪数据，返回统计结果和主要情绪"""
    emotion_counts = defaultdict(int)

    for row in data:
        emotion = row[3]  # 情绪状态字段
        emotion_counts[emotion] += 1

    # 计算情绪占比
    total = len(data)
    emotion_percent = {k: round(v / total * 100, 1) for k, v in emotion_counts.items()}

    # 找出主要情绪（出现次数最多的）
    main_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if data else None

    return {
        'counts': emotion_counts,
        'percent': emotion_percent,
        'main_emotion': main_emotion
    }


def get_health_advice(emotion):
    """根据情绪提供健康建议（简化版）"""
    advice_dict = {
        "开心": "继续保持好心情！可以记录下让你开心的事情，与朋友分享快乐。",
        "平静": "平静是很好的状态，适合进行冥想或专注工作。",
        "伤心": "给自己一些时间处理情绪，听听音乐或与信任的人聊聊。"
    }
    return advice_dict.get(emotion, "注意调节情绪，保持规律作息。")


def plot_emotion_distribution(data):
    """绘制情绪分布饼图"""
    if not data:
        return None

    # 统计情绪数量
    emotion_counts = defaultdict(int)
    for row in data:
        emotion = row[3]  # 情绪状态字段
        if emotion in ["开心", "平静", "伤心"]:  # 只统计这三种情绪
            emotion_counts[emotion] += 1

    # 如果没有有效数据，返回None
    if not emotion_counts:
        return None

    # 准备图表数据
    labels = ['开心', '平静', '伤心']
    sizes = [emotion_counts.get(label, 0) for label in labels]

    # 如果所有值都是0，则不绘制图表
    if sum(sizes) == 0:
        return None

    # 设置颜色
    colors = ['#4CAF50', '#2196F3', '#F44336']  # 绿色、蓝色、红色

    # 创建饼图
    plt.figure(figsize=(6, 6))
    patches, texts, autotexts = plt.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 12}
    )

    # 设置中文显示
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']
    matplotlib.rcParams['axes.unicode_minus'] = False

    # 设置样式
    plt.axis('equal')  # 正圆形
    plt.title('情绪状态分布', pad=20, fontsize=14)

    # 转换为base64编码
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return image_base64


def generate_html(data):
    """生成完整的HTML报告"""
    # 分析情绪数据
    analysis = analyze_emotion_data(data)

    # 生成情绪概览部分
    # 生成情绪概览部分
    if analysis['main_emotion']:
        # 将英文情绪状态转换为中文
        emotion_mapping = {
            'Happy': '开心',
            'Normal': '平静',
            'Sad': '伤心'
        }
        chinese_emotion = emotion_mapping.get(analysis['main_emotion'], analysis['main_emotion'])

        advice = get_health_advice(chinese_emotion)
        emotion_display = f"""
        <div style="margin: 20px auto; padding: 15px; background-color: #E6E6FA; border-radius: 5px; width: 80%; text-align: center;">
            <h3>主要情绪状态: <span style="color: #dc3545;">{chinese_emotion}</span></h3>
            <p><strong>健康建议:</strong> {advice}</p>
        </div>
        """
    else:
        emotion_display = """
        <div style="margin: 20px 0; padding: 15px; background-color: #E6E6FA; border-radius: 5px; width: 80%; text-align: center;">
            <p>没有情绪数据记录</p>
        </div>
        """

    # 生成情绪分布图
    chart_html = ""
    image_base64 = plot_emotion_distribution(data)
    if image_base64:
        chart_html = f"""
        <div style="margin: 30px auto; width: 85%; text-align: center;">
            <h3 style="margin-bottom: 15px;">情绪状态分布</h3>
            <img src="data:image/png;base64,{image_base64}" style="max-width: 100%;">
        </div>
        """

    # 生成完整HTML
    html_content = f"""
    <html>
    <head>
        <title>情绪状态报告</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ text-align: center; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            table, th, td {{ border: 1px solid #ddd; }}
            th, td {{ padding: 10px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .emotion-display {{ 
                margin: 20px auto; 
                padding: 15px; 
                background-color: #f8f9fa; 
                border-radius: 8px; 
                width: 80%; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .positive {{ color: #28a745; }}
            .neutral {{ color: #17a2b8; }}
            .negative {{ color: #dc3545; }}
        </style>
    </head>
    <body>
        <h1>皮肤电信号情绪状态分析报告</h1>
        {emotion_display}
        {chart_html}
        <h3 style="margin-top: 30px;">详细记录</h3>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>开始时间</th>
                    <th>结束时间</th>
                    <th>情绪状态</th>
                </tr>
            </thead>
            <tbody>
    """

    # 填充表格数据
    for row in data:
        emotion = row[3]
        # 根据情绪类型设置CSS类
        emotion_class = ""
        if emotion == "Happy":
            emotion_class = "开心"
        elif emotion == "Normal":
            emotion_class = "平静"
        elif emotion == "Sad":
            emotion_class = "伤心"

        html_content += f"""
        <tr>
            <td>{row[0]}</td>
            <td>{row[1].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[1], datetime) else row[1]}</td>
            <td>{row[2].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[2], datetime) else row[2]}</td>
            <td class="{emotion}">{emotion_class}</td>
        </tr>
        """

    # HTML结尾
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    # 保存HTML文件
    with open("emotion_report.html", "w", encoding="utf-8") as file:
        file.write(html_content)

    print("情绪报告已生成: emotion_report.html")


if __name__ == "__main__":
    data = get_data_from_db()
    generate_html(data)