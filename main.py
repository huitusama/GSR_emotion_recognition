import os
import re
import generatevector
import getattr
import database
import time
import serial
from my_svm import MySvm
#from sklearn.externals import joblib
import joblib
import matplotlib.pyplot as plt

import numpy as np


def train_module():
    if os.path.isfile('model\\happy_model.m'):
        print('The model already exists, do you want to retrain it?')
        print('1:skip 2:retrain')

        choice = input()
        while (choice != '1') and (choice != '2'):
            print('error input, please retry')
            choice = input()
        if choice == '1':
            print('use last model')
            return
    print("training... please waiting")
    generatevector.generate_vector()
    mysvm = MySvm()
    mysvm.feature_selection()
    mysvm.svm_train()
    print('training finish, use last model')

def predict_result():
    # 全局中断标志
    global EXIT_FLAG
    EXIT_FLAG = False

    # 1. 预加载模型（提升性能）
    try:
        happy_clf = joblib.load('model\\happy_model.m')
        select = joblib.load('model\\vector_select.m')
        sad_clf = joblib.load('model\\sad_model.m')
        print("✅ 模型加载成功")
    except Exception as e:
        print(f"❌ 模型加载失败: {e}")
        return

    # 2. 初始化串口（非阻塞设置）
    try:
        ser = serial.Serial(
            port='COM3',
            baudrate=9600,
            timeout=0.1,  # 关键设置：防止阻塞
            inter_byte_timeout=0.1
        )
    except Exception as e:
        print(f"❌ 串口连接失败: {e}")
        return

    # 3. 初始化图表（可中断配置）
    plt.rcParams['keymap.quit'] = ['ctrl+c', 'q']  # 绑定退出快捷键
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.canvas.mpl_connect('close_event', lambda _: globals().update({'EXIT_FLAG': True}))

    # 可视化元素
    ax.set_title('GSR Monitoring (Press Ctrl+C OR Close Window to Stop)')
    line, = ax.plot([], [], 'b-', lw=1)
    emotion_label = ax.text(0.85, 0.95, 'EMOTION: WAITING...',
                            transform=ax.transAxes,
                            fontsize=12,
                            bbox=dict(facecolor='yellow', alpha=0.7))

    # 4. 数据缓冲区
    data_buffer = []
    max_samples = 200
    pred_interval = 50
    last_emotion = None

    try:
        while not EXIT_FLAG:
            # 5. 非阻塞数据读取
            try:
                raw_data = ser.read_all()
                if raw_data:
                    # 高效解析数据（兼容换行符和二进制）
                    values = [int(x) for x in re.findall(rb'(\d+)', raw_data)]
                    data_buffer.extend(values[-10:])  # 限制新增数据量
            except Exception as e:
                print(f"⚠️ 数据解析错误: {e}")
                continue

            # 6. 实时绘图
            if data_buffer:
                line.set_data(range(len(data_buffer)), data_buffer)
                ax.set_xlim(max(0, len(data_buffer) - max_samples), len(data_buffer))

                # 智能Y轴计算
                visible_data = data_buffer[-max_samples:]
                data_range = max(visible_data) - min(visible_data)

                # 核心参数（可调整）
                min_display_range = 30  # 最小显示跨度
                dynamic_margin = max(data_range * 0.3, min_display_range / 2)

                # 设置Y轴
                ax.set_ylim(
                    min(visible_data) - dynamic_margin,
                    max(visible_data) + dynamic_margin
                )
                # # 更新曲线
                # line.set_data(range(len(data_buffer)), data_buffer)
                # ax.set_xlim(max(0, len(data_buffer) - max_samples), len(data_buffer))
                #
                # # 动态Y轴
                # visible_data = data_buffer[-max_samples:]
                # y_margin = (max(visible_data) - min(visible_data)) * 0.2
                # ax.set_ylim(min(visible_data) - y_margin*1.2, max(visible_data) + y_margin*1.2)

                # 7. 情绪预测（每50个点）
                if len(data_buffer) % pred_interval == 0 and len(data_buffer) >= 50:
                    try:
                        # 特征提取
                        features = getattr.get_vector(data_buffer[-50:])
                        features = select.transform(np.array(features).reshape(1, -1))

                        # 两级预测（happy -> normal -> sad）
                        pred = happy_clf.predict(features)[0]
                        if pred == '2' and sad_clf:
                            pred = sad_clf.predict(features)[0]

                        emotion = {'1': '😊 HAPPY', '2': '😐 NORMAL', '3': '😢 SAD'}.get(pred, '❓ UNKNOWN')

                        # 更新标签（仅当情绪变化时）
                        if emotion != last_emotion:
                            emotion_label.set_text(f'EMOTION: {emotion}')
                            emotion_label.set_bbox(dict(
                                facecolor='green' if 'HAPPY' in emotion else
                                'red' if 'SAD' in emotion else 'yellow',
                                alpha=0.7
                            ))
                            last_emotion = emotion
                            print(f"🎭 情绪更新: {emotion}")

                    except Exception as e:
                        print(f"⚠️ 预测异常: {e}")

            # 8. 退出检查（双重保障）
            if not plt.fignum_exists(fig.number):
                EXIT_FLAG = True

            plt.pause(0.01)  # 控制刷新率

    except KeyboardInterrupt:
        print("\n🛑 用户中断...")
    finally:
        # 9. 强制资源释放
        try:
            ser.close()
            plt.close('all')
            print("✅ 资源已释放")
        except:
            pass

if __name__ == '__main__':
    train_module()
    predict_result()