# from flask import Flask, render_template, jsonify
# from flask_socketio import SocketIO
# import serial
# import re
# import numpy as np
# import joblib
# from threading import Lock
# import time
# import getattr
# from getattr import get_vector
# from pathlib import Path
# import sys
# import os
# from flask_socketio import SocketIO
# import eventlet  # 显式导入eventlet
#
# import sqlite3
# from datetime import datetime
# import atexit
#
# # 初始化全局变量
# current_emotion = None
# emotion_start_time = None
# emotion_lock = Lock()  # 情绪变量锁
#
# def init_db():
#     conn = sqlite3.connect('emotion_records.db')
#     c = conn.cursor()
#     c.execute('''CREATE TABLE IF NOT EXISTS records
#                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
#                   start_time TEXT NOT NULL,
#                   end_time TEXT NOT NULL,
#                   emotion TEXT NOT NULL)''')
#     conn.commit()
#     conn.close()
#
# # 启用eventlet的monkey patch（关键步骤）
# eventlet.monkey_patch()
#
# # 手动指定项目根目录路径
# project_root = r"C:\Users\mo\Desktop\emotion-recognition-master(2)"
# sys.path.append(project_root)
#
# app = Flask(__name__)
# app.config['SECRET_KEY'] = 'secret!'
#
# # 在程序启动时初始化数据库
# init_db()
#
# socketio = SocketIO(
#     app,
#     cors_allowed_origins="*",
#     async_mode='eventlet',
#     transports=['websocket']
# )
#
#
# # 全局变量
# serial_lock = Lock()
# data_buffer = []
# #last_emotion = None
#
#
#
# # 情绪映射
# EMOTION_MAP = {
#     '1': {'text': '开心', 'emoji': '😊', 'color': '#4CAF50'},
#     '2': {'text': '平静', 'emoji': '😐', 'color': '#FFC107'},
#     '3': {'text': '悲伤', 'emoji': '😢', 'color': '#F44336'},
#     'default': {'text': '等待数据', 'emoji': '⏳', 'color': '#9E9E9E'}
# }
#
# # ------------------- 数据库操作函数 -------------------
# def save_to_db(start, end, emotion):
#     try:
#         conn = sqlite3.connect('emotion_records.db')
#         c = conn.cursor()
#         c.execute("INSERT INTO records (start_time, end_time, emotion) VALUES (?,?,?)",
#                   (start, end, emotion))
#         conn.commit()
#         conn.close()
#         print(f"✅ 已保存记录：{start} -> {end} | 情绪：{emotion}")
#     except Exception as e:
#         print(f"❌ 数据库保存失败: {e}")
#
# @atexit.register
# def save_final_record():
#     global current_emotion, emotion_start_time
#     with emotion_lock:
#         if current_emotion and current_emotion != '等待数据':
#             end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             save_to_db(emotion_start_time, end_time, current_emotion)
#
# # ------------------- 实时处理器类 -------------------
# class RealTimeProcessor:
#     def __init__(self):
#         self.ser = None
#         self.models_loaded = False
#         self.load_models()
#
#     def connect_serial(self):
#         try:
#             self.ser = serial.Serial(
#                 port='COM3',
#                 baudrate=9600,
#                 timeout=0.1,
#                 inter_byte_timeout=0.1
#             )
#             print(f"✅ 串口已连接：{self.ser.port} | 波特率：{self.ser.baudrate}")
#             return True
#         except Exception as e:
#             print(f"❌ 串口连接失败：{str(e)}")
#             return False
#
#     def get_emotion(self, features):
#         try:
#             pred = self.happy_clf.predict(features)[0]
#             if pred == '2':
#                 pred = self.sad_clf.predict(features)[0]
#             return EMOTION_MAP.get(pred, EMOTION_MAP['default'])
#         except Exception as e:
#             print(f"预测异常: {e}")
#             return EMOTION_MAP['default']
#
#     def load_models(self):
#         try:
#             model_dir = Path(__file__).parent.parent / "model"
#             self.happy_clf = joblib.load(model_dir / "happy_model.m")
#             self.select = joblib.load(model_dir / "vector_select.m")
#             self.sad_clf = joblib.load(model_dir / "sad_model.m")
#             self.models_loaded = True
#             print("✅ 模型加载成功")
#         except Exception as e:
#             print(f"❌ 模型加载失败: {e}")
#             self.models_loaded = False
#
#     def process_data(self):
#         global data_buffer, current_emotion, emotion_start_time
#         raw_buffer = b''  # 原始字节缓冲区
#
#         while True:
#             if self.ser and self.models_loaded:
#                 try:
#                     # ================== 数据读取与解析 ==================
#                     # 1. 累积原始字节数据
#                     raw_buffer += self.ser.read_all()
#
#                     # 2. 使用正则表达式提取所有数字（兼容粘包/异常字符）
#                     numbers = re.findall(rb'\d+', raw_buffer)  # 提取所有连续数字
#                     if numbers:
#                         with serial_lock:
#                             # 转换并追加有效数据（限制每次最多添加20个新点）
#                             new_values = [int(num) for num in numbers[-20:]]  # 防止突发数据量过大
#                             data_buffer.extend(new_values)
#                             data_buffer = data_buffer[-200:]  # 保持缓冲区最大200点
#
#                     raw_buffer = b''  # 清空原始缓冲区（已处理所有数据）
#
#                     # ================== 特征处理与预测 ==================
#                     with serial_lock:
#                         window_size = 50
#                         emotion = EMOTION_MAP['default']
#
#                         if len(data_buffer) >= window_size:
#                             try:
#                                 # 1. 获取最近50个点的特征向量（返回numpy数组）
#                                 raw_features = get_vector(data_buffer[-window_size:])
#
#                                 # 2. 转换为二维数组（样本数 x 特征数）
#                                 features = np.array(raw_features).reshape(1, -1)
#
#                                 # 3. 特征选择（假设select是训练好的特征选择器）
#                                 selected_features = self.select.transform(features)
#
#                                 # 4. 预测情绪
#                                 #emotion = self.get_emotion(selected_features)
#                                 new_emotion = self.get_emotion(selected_features)
#
#                                 # 检测情绪变化
#                                 with emotion_lock:
#                                     if new_emotion['text'] != current_emotion:
#                                         # 保存旧情绪记录
#                                         if current_emotion is not None and current_emotion != '等待数据':
#                                             end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                                             save_to_db(emotion_start_time, end_time, current_emotion)
#                                         # 更新新情绪记录
#                                         current_emotion = new_emotion['text']
#                                         emotion_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                                     emotion = new_emotion
#
#                             except Exception as e:
#                                 print(f"🔥 特征处理失败: {e}")
#
#                         # ================== 实时数据推送 ==================
#                         # 无论是否满足窗口大小都发送数据（保持图表更新）
#                         socketio.emit('update', {
#                             'gsr': data_buffer[-1] if data_buffer else 0,
#                             'buffer': data_buffer[-200:],  # 发送全部可视数据
#                             'emotion': emotion,
#                             'progress': f"{min(len(data_buffer), window_size)}/{window_size}"
#                         })
#                         print(f"📡 已发送数据 | 缓冲区: {len(data_buffer)} | 情绪: {emotion['text']}")
#
#                 except Exception as e:
#                     print(f"⚠️ 主循环异常: {e}")
#                     # 重大错误时重置连接
#                     self.ser.close()
#                     self.ser = None
#                     break
#
#                 time.sleep(0.001)  # 防止CPU满载
#
# # 在程序退出时保存最后一条记录
# # @atexit.register
# # def save_final_record():
# #     if current_emotion and current_emotion != '等待数据':
# #         end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# #         save_to_db(emotion_start_time, end_time, current_emotion)
#
# # def save_to_db(start, end, emotion):
# #     conn = sqlite3.connect('emotion_records.db')
# #     c = conn.cursor()
# #     c.execute("INSERT INTO records (start_time, end_time, emotion) VALUES (?,?,?)",
# #               (start, end, emotion))
# #     conn.commit()
# #     conn.close()
#
# # 初始化处理器
# processor = RealTimeProcessor()
#
#
# @app.route('/')
# def index():
#     return render_template('index.html')
#
# # # 在app.py中添加新路由
# # @app.route('/get_records')
# # def get_records():
# #     conn = sqlite3.connect('emotion_records.db')
# #     c = conn.cursor()
# #     c.execute("SELECT * FROM records ORDER BY id DESC")
# #     records = [{'id': row[0],
# #                 'start': row[1],
# #                 'end': row[2],
# #                 'emotion': row[3]} for row in c.fetchall()]
# #     conn.close()
# #     return jsonify(records)
#
# # @app.route('/get_records')
# # def get_records():
# #     try:
# #         conn = sqlite3.connect('emotion_records.db')
# #         c = conn.cursor()
# #         c.execute("SELECT * FROM records ORDER BY id DESC")
# #         records = [{'id': row[0], 'start': row[1], 'end': row[2], 'emotion': row[3]} for row in c.fetchall()]
# #         conn.close()
# #         return jsonify(records)
# #     except Exception as e:
# #         print(f"❌ 获取记录失败: {e}")
# #         return jsonify([])
#
# @app.route('/get_records')
# def get_records():
#     try:
#         with sqlite3.connect('emotion_records.db') as conn:
#             c = conn.cursor()
#             # 使用别名直接映射字段名
#             c.execute("SELECT id, start_time AS start, end_time AS end, emotion FROM records ORDER BY id DESC")
#             records = [{'id': row[0], 'start': row[1], 'end': row[2], 'emotion': row[3]} for row in c.fetchall()]
#         return jsonify(records)
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         print(f"❌ 获取记录失败: {str(e)}")
#         return jsonify({'error': '数据库查询失败'}), 500
#
# @socketio.on('connect')
# def handle_connect():
#     if not processor.ser:
#         if processor.connect_serial():
#             socketio.start_background_task(processor.process_data)
#         else:
#             socketio.emit('error', {'message': '串口连接失败'})
#
# if __name__ == '__main__':
#     # 正确启动方式（必须使用 socketio.run()）
#     socketio.run(
#         app,
#         host='0.0.0.0',  # 允许所有IP访问
#         port=5001,
#         debug=True,
#         use_reloader=False  # 关闭自动重载（避免重复初始化）
#     )

from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO
import serial
import re
import numpy as np
import joblib
from threading import Lock
import time
import getattr
from getattr import get_vector
from pathlib import Path
import sys
import os
from flask_socketio import SocketIO
import eventlet

import sqlite3
from datetime import datetime
import atexit

# ------------------- 全局变量初始化 -------------------
program_start_time = None  # 程序启动时间
current_emotion = "等待数据"  # 当前情绪状态
emotion_start_time = None  # 当前情绪开始时间
emotion_lock = Lock()  # 情绪变量锁
data_buffer = []  # 数据缓冲区
serial_lock = Lock()  # 串口数据锁


# ------------------- 数据库初始化 -------------------
def init_db():
    conn = sqlite3.connect('emotion_records.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  start_time TEXT NOT NULL,
                  end_time TEXT NOT NULL,
                  emotion TEXT NOT NULL)''')
    conn.commit()
    conn.close()


# ------------------- Eventlet配置 -------------------
eventlet.monkey_patch()

# ------------------- Flask应用初始化 -------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
init_db()  # 确保数据库表存在

# # 添加 Favicon 路由
# @app.route('/favicon.ico')
# def favicon():
#     return send_from_directory(os.path.join(app.root_path, 'static'),
#                                'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ------------------- SocketIO配置 -------------------
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    transports=['websocket']
)

# ------------------- 情绪映射 -------------------
EMOTION_MAP = {
    '1': {'text': '开心', 'emoji': '😊', 'color': '#4CAF50'},
    '2': {'text': '平静', 'emoji': '😐', 'color': '#FFC107'},
    '3': {'text': '悲伤', 'emoji': '😢', 'color': '#F44336'},
    'default': {'text': '等待数据', 'emoji': '⏳', 'color': '#9E9E9E'}
}


# ------------------- 数据库操作函数 -------------------
def save_to_db(start, end, emotion):
    try:
        conn = sqlite3.connect('emotion_records.db')
        c = conn.cursor()
        c.execute("INSERT INTO records (start_time, end_time, emotion) VALUES (?,?,?)",
                  (start, end, emotion))
        conn.commit()
        conn.close()
        print(f"✅ 已保存记录：{start} -> {end} | 情绪：{emotion}")
    except Exception as e:
        print(f"❌ 数据库保存失败: {e}")


# ------------------- 程序退出时保存最后一段情绪 -------------------
@atexit.register
def save_final_record():
    global current_emotion, emotion_start_time, program_start_time
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with emotion_lock:
        # 保存当前正在记录的情绪
        if current_emotion != "等待数据" and emotion_start_time:
            save_to_db(emotion_start_time, end_time, current_emotion)

        # 如果整个运行期间没有有效情绪，保存一条完整记录
        if program_start_time and current_emotion == "等待数据":
            save_to_db(program_start_time, end_time, "无有效情绪数据")


# ------------------- 实时处理器类 -------------------
class RealTimeProcessor:
    def __init__(self):
        self.ser = None
        self.models_loaded = False
        self.load_models()

    def connect_serial(self):
        try:
            self.ser = serial.Serial(
                port='COM3',
                baudrate=9600,
                timeout=0.1,
                inter_byte_timeout=0.1
            )
            print(f"✅ 串口已连接：{self.ser.port} | 波特率：{self.ser.baudrate}")
            return True
        except Exception as e:
            print(f"❌ 串口连接失败：{str(e)}")
            return False

    def get_emotion(self, features):
        try:
            pred = self.happy_clf.predict(features)[0]
            if pred == '2':
                pred = self.sad_clf.predict(features)[0]
            return EMOTION_MAP.get(pred, EMOTION_MAP['default'])
        except Exception as e:
            print(f"预测异常: {e}")
            return EMOTION_MAP['default']

    def load_models(self):
        try:
            model_dir = Path(__file__).parent.parent / "model"
            self.happy_clf = joblib.load(model_dir / "happy_model.m")
            self.select = joblib.load(model_dir / "vector_select.m")
            self.sad_clf = joblib.load(model_dir / "sad_model.m")
            self.models_loaded = True
            print("✅ 模型加载成功")
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            self.models_loaded = False

    def process_data(self):
        global data_buffer, current_emotion, emotion_start_time, program_start_time
        raw_buffer = b''

        # 记录程序启动时间
        program_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        while True:
            if self.ser and self.models_loaded:
                try:
                    # ================== 数据读取 ==================
                    raw_buffer += self.ser.read_all()
                    numbers = re.findall(rb'\d+', raw_buffer)
                    if numbers:
                        with serial_lock:
                            new_values = [int(num) for num in numbers[-20:]]
                            data_buffer.extend(new_values)
                            data_buffer = data_buffer[-200:]
                    raw_buffer = b''

                    # ================== 情绪预测 ==================
                    with serial_lock:
                        window_size = 50
                        emotion = EMOTION_MAP['default']

                        if len(data_buffer) >= window_size:
                            try:
                                raw_features = get_vector(data_buffer[-window_size:])
                                features = np.array(raw_features).reshape(1, -1)
                                selected_features = self.select.transform(features)
                                new_emotion = self.get_emotion(selected_features)

                                # 检测情绪变化
                                with emotion_lock:
                                    if new_emotion['text'] != current_emotion:
                                        # 保存旧情绪记录
                                        if current_emotion != "等待数据" and emotion_start_time:
                                            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                            save_to_db(emotion_start_time, end_time, current_emotion)

                                        # 更新新情绪记录
                                        current_emotion = new_emotion['text']
                                        emotion_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                    emotion = new_emotion

                            except Exception as e:
                                print(f"🔥 特征处理失败: {e}")

                    # ================== 实时推送 ==================
                    socketio.emit('update', {
                        'gsr': data_buffer[-1] if data_buffer else 0,
                        'buffer': data_buffer[-200:],
                        'emotion': emotion,
                        'progress': f"{min(len(data_buffer), window_size)}/{window_size}"
                    })
                    #print(f"📡 已发送数据 | 缓冲区: {len(data_buffer)} | 情绪: {emotion['text']}")

                except Exception as e:
                    print(f"⚠️ 主循环异常: {e}")
                    self.ser.close()
                    self.ser = None
                    break

                time.sleep(0.001)


# ------------------- Flask路由 -------------------
processor = RealTimeProcessor()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_records')
def get_records():
    try:
        with sqlite3.connect('emotion_records.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id, start_time AS start, end_time AS end, emotion FROM records ORDER BY id DESC")
            records = [{'id': row[0], 'start': row[1], 'end': row[2], 'emotion': row[3]} for row in c.fetchall()]
        return jsonify(records)
    except Exception as e:
        print(f"❌ 获取记录失败: {e}")
        return jsonify({'error': '数据库查询失败'}), 500


@socketio.on('connect')
def handle_connect():
    if not processor.ser:
        if processor.connect_serial():
            socketio.start_background_task(processor.process_data)
        else:
            socketio.emit('error', {'message': '串口连接失败'})


# ------------------- 主程序入口 -------------------
if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False
    )