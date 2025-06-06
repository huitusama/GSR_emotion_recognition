# GSR_emotion_recognition
## 本项目参考并基于以下开源项目开发：
https://github.com/yinxiaojian/emotion-recognition

---

## 模型训练
训练模型的数据为个人收集，收集方法如下：

---

### 1.被试者样本管理
样本量：12人（男女各半，年龄18-23岁，无重大健康问题，且通过口头问卷排除如失眠、压力过大等的近期情绪异常者）
分组：快乐、平静、悲伤各4人（每人采集多次）

---

### 2.采集环境
场地：安静教室。
设备：GSR传感器（Arduino），采样频率20Hz

---

### 3. 情绪诱发
- 刺激材料：
-- 快乐：短视频平台搞笑片段（如脱口秀）
-- 悲伤：影视经典悲剧片段（如《忠犬八公》结局）
-- 平静：自然风光纪录片（无剧情波动）

- 流程：被试静坐5分钟适应环境→播放情绪视频，同步记录GSR信号（共250秒，5000个数据点）→结束后立即填写情绪自评表（悲伤、平静or快乐）→仅保留自评分与目标情绪匹配的数据

---

### 4. 数据存储：每个数据文件长度为5000个数据点，以CSV格式存储，命名为：情绪_序号.csv，按情绪类别分类存放

---

## 使用方法
下载数据集，将data文件文件夹放在根目录下：
-链接: https://pan.baidu.com/s/19k8ubbGBfIk33-3sATjSXg?pwd=cufg 提取码: cufg

