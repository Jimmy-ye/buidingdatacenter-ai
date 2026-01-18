# 移动端/手机端开发开源库推荐清单

> 基于 `PLAN.md` 项目需求：**手机端现场采集图片 + 语音/文字说明，并上传到项目库**
>
> 整理时间：2026-01-17

---

## 📋 目录

- [一、跨平台移动开发框架](#一跨平台移动开发框架)
- [二、小程序开发框架（国内推荐）](#二小程序开发框架国内推荐)
- [三、相机与图片采集](#三相机与图片采集)
- [四、语音识别（ASR）](#四语音识别asr)
- [五、离线存储与数据库](#五离线存储与数据库)
- [六、地理位置与二维码](#六地理位置与二维码)
- [七、网络请求与API集成]( #七网络请求与api集成)
- [八、UI组件库]( #八ui组件库)
- [九、状态管理]( #九状态管理)
- [十、推荐技术栈组合]( #十推荐技术栈组合)

---

## 一、跨平台移动开发框架

### 🔹 React Native ⭐ 推荐（生态成熟）

**GitHub**: https://github.com/facebook/react-native

**适用场景**:
- ✅ 团队熟悉React/JavaScript
- ✅ 需要快速迭代，热更新
- ✅ 丰富的第三方库生态

**优势**:
- Meta（Facebook）维护，社区活跃
- 一套代码支持iOS + Android
- 使用React/JavaScript，学习曲线低
- 丰富的组件库和工具链

**核心库安装**:
```bash
# 创建项目
npx react-native@latest init BDCAIApp

# 或使用Expo（更简单）
npx create-expo-app BDCAIApp
```

**项目结构示例**:
```
BDCAIApp/
├── src/
│   ├── screens/          # 页面
│   │   ├── ProjectListScreen.tsx
│   │   ├── AssetUploadScreen.tsx
│   │   └── VoiceRecordScreen.tsx
│   ├── components/       # 组件
│   ├── services/         # API服务
│   ├── utils/            # 工具函数
│   └── navigation/       # 路由配置
├── android/
├── ios/
└── package.json
```

---

### 🔹 Flutter ⭐ 推荐（性能优异）

**GitHub**: https://github.com/flutter/flutter

**适用场景**:
- ✅ 追求高性能和流畅体验
- ✅ 团队熟悉Dart语言
- ✅ 需要自定义UI效果

**优势**:
- Google维护，性能接近原生
- 一套代码支持iOS + Android + Web + Desktop
- 丰富的Material Design和Cupertino组件
- 热重载开发体验好

**核心库安装**:
```bash
# 创建项目
flutter create bdc_ai_app

# 运行
cd bdc_ai_app
flutter run
```

---

### 🔹 技术选型对比

| 特性 | React Native | Flutter |
|-----|-------------|---------|
| **语言** | JavaScript/TypeScript | Dart |
| **性能** | 接近原生（Bridge桥接） | 接近原生（直接编译） |
| **包大小** | 较小（~20MB） | 较大（~50MB） |
| **学习曲线** | 低（React生态） | 中（需学习Dart） |
| **生态** | 成熟丰富 | 快速增长 |
| **热更新** | ✅ 支持（CodePush） | ⚠️ 有限支持 |
| **推荐场景** | Web技术栈团队 | 追求性能和UI |

**推荐决策**:
- 如果团队有React经验 → **React Native**
- 如果追求极致性能 → **Flutter**

---

## 二、小程序开发框架（国内推荐）

如果你的用户主要在中国，**小程序**可能是更好的选择（无需下载安装）。

### 🔹 uni-app ⭐ 强烈推荐（Vue技术栈）

**官网**: https://uniapp.dcloud.net.cn/
**GitHub**: https://github.com/dcloudio/uni-app

**适用场景**:
- ✅ 快速发布到多个平台（微信/支付宝/抖音/小程序 + App + H5）
- ✅ 团队熟悉Vue.js
- ✅ 中小型团队，快速开发

**优势**:
- 一套代码发布到iOS、Android、Web、各种小程序
- Vue.js语法，学习成本低
- 丰富的插件市场
- DCloud官方维护

**支持平台**:
- ✅ 微信小程序
- ✅ 支付宝小程序
- ✅ 抖音小程序
- ✅ QQ小程序
- ✅ 百度小程序
- ✅ 快手小程序
- ✅ App（iOS + Android）
- ✅ H5

**示例代码**:
```vue
<template>
  <view class="container">
    <button @click="takePhoto">拍照上传</button>
    <button @click="startRecord">语音记录</button>
  </view>
</template>

<script>
export default {
  data() {
    return {
      projectId: '',
      imageList: []
    }
  },
  methods: {
    async takePhoto() {
      const res = await uni.chooseImage({
        count: 1,
        sourceType: ['camera']
      })

      await this.uploadToServer(res.tempFilePaths[0])
    },

    async startRecord() {
      // 语音录制
      const recorderManager = uni.getRecorderManager()
      recorderManager.start()
    }
  }
}
</script>
```

---

### 🔹 Taro ⭐ 推荐（React技术栈）

**官网**: https://taro-docs.jd.com/
**GitHub**: https://github.com/NervJS/taro

**适用场景**:
- ✅ 团队熟悉React
- ✅ 需要深度定制
- ✅ 中大型项目

**优势**:
- React语法，与React Native共享逻辑
- 支持多端编译
- 京东开源，企业级应用

**对比**:
| 特性 | uni-app | Taro |
|-----|---------|------|
| **技术栈** | Vue.js | React |
| **上手难度** | 低 | 中 |
| **性能** | 优秀 | 优秀 |
| **生态** | 丰富（插件市场） | 丰富（React生态） |
| **推荐团队** | Vue技术栈 | React技术栈 |

---

## 三、相机与图片采集

### 🔹 React Native Vision Camera ⭐ 推荐

**GitHub**: https://github.com/mrousavy/react-native-vision-camera

**适用场景**:
- ✅ 自定义相机界面
- ✅ 实时预览和处理
- ✅ 高级功能（二维码、人脸检测）

**核心功能**:
- 照片和视频录制
- 实时预览
- QR/Barcode扫描
- 自定义UI
- 设备切换（前置/后置）

**安装**:
```bash
npm install react-native-vision-camera
```

**使用示例**:
```tsx
import { Camera } from 'react-native-vision-camera';

function AssetUploadScreen() {
  const camera = useRef<Camera>(null);

  const takePhoto = async () => {
    const photo = await camera.current?.takePhoto({
      qualityPrioritization: 'quality',
      flash: 'on'
    });

    // 上传到服务器
    await uploadPhotoToServer(photo.path);
  };

  return (
    <Camera
      ref={camera}
      style={styles.camera}
      photo={true}
    />
  );
}
```

---

### 🔹 React Native Image Picker ⭐ 简单方案

**GitHub**: https://github.com/react-native-image-picker/react-native-image-picker

**适用场景**:
- ✅ 快速集成（使用系统相机）
- ✅ 从相册选择

**安装**:
```bash
npm install react-native-image-picker
```

**使用示例**:
```tsx
import { launchCamera } from 'react-native-image-picker';

const takePhoto = () => {
  launchCamera({mediaType: 'photo'}, (response) => {
    if (response.assets) {
      // 上传图片
      uploadToServer(response.assets[0]);
    }
  });
};
```

---

### 🔹 Flutter 相机库

#### mobile_scanner（二维码扫描）
**GitHub**: https://github.com/juliansteenbakker/mobile_scanner

**功能**:
- QR码和条形码扫描
- 实时检测
- 多格式支持

**示例**:
```dart
import 'package:mobile_scanner/mobile_scanner';

MobileScannerController controller = MobileScannerController();

MobileScanner(
  controller: controller,
  onDetect: (capture) {
    final List<Barcode> barcodes = capture.barcodes;
    for (final barcode in barcodes) {
      // 处理扫描结果
      print('QR Code: ${barcode.rawValue}');
    }
  },
)
```

---

## 四、语音识别（ASR）

### 🔹 Whisper for React Native ⭐ 推荐（离线+多语言）

**GitHub**: https://github.com/israr002/rn-whisper-stt

**适用场景**:
- ✅ 离线语音转文字
- ✅ 多语言支持（99种语言）
- ✅ 隐私保护（本地处理）

**优势**:
- 使用OpenAI Whisper模型
- 完全离线运行
- 支持中文
- 实时转录

**安装**:
```bash
npm install rn-whisper-stt
```

**使用示例**:
```tsx
import WhisperSTT from 'rn-whisper-stt';

const startTranscription = async () => {
  const whisper = new WhisperSTT({
    model: 'tiny', // 或 'base', 'small'
    language: 'zh'
  });

  const transcript = await whisper.transcribe(audioFile);
  console.log('识别结果:', transcript);
};
```

---

### 🔹 whisper_kit（Flutter）

**GitHub**: https://pub.dev/packages/whisper_kit

**适用场景**:
- ✅ Flutter应用
- ✅ 离线语音识别
- ✅ 实时转录

**安装**:
```bash
flutter pub add whisper_kit
```

**示例**:
```dart
import 'package:whisper_kit/whisper_kit';

final whisper = WhisperKit();
await whisper.loadModel();

final transcript = await whisper.transcribe(
  audioFilePath,
  language: 'zh'
);
```

---

### 🔹 在线ASR备选方案

如果允许联网，可以使用云服务API：

#### 百度语音识别（中文优秀）
- 支持中文方言识别
- 提供REST API
- 免费额度：每日50000次

#### 阿里云智能语音
- 实时语音识别
- 支持中文+英文
- 提供SDK

**示例（集成百度ASR）**:
```typescript
import { Audio } from 'expo-av';

async function recordAndTranscribe() {
  // 1. 录音
  const recording = new Audio.Recording();
  await recording.prepareToRecordAsync(Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY);
  await recording.startAsync();

  // 2. 停止录音
  await recording.stopAsync();
  const uri = recording.getURI();

  // 3. 上传到百度ASR API
  const formData = new FormData();
  formData.append('audio', {
    uri: uri,
    type: 'audio/wav',
    name: 'audio.wav'
  });

  const response = await fetch('https://vop.baidu.com/server_api', {
    method: 'POST',
    body: formData,
    headers: {
      'Content-Type': 'audio/wav; rate=16000'
    }
  });

  const result = await response.json();
  return result.result[0]; // 返回识别的文字
}
```

---

## 五、离线存储与数据库

### 🔹 AsyncStorage（简单KV存储）⭐ MVP首选

**GitHub**: https://github.com/react-native-async-storage/async-storage

**适用场景**:
- ✅ 简单键值对存储
- ✅ 用户设置、Token缓存
- ✅ 轻量级离线数据

**安装**:
```bash
npm install @react-native-async-storage/async-storage
```

**使用示例**:
```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

// 保存项目列表
await AsyncStorage.setItem('projects', JSON.stringify(projects));

// 读取
const projectsJson = await AsyncStorage.getItem('projects');
const projects = JSON.parse(projectsJson);

// 离线缓存上传队列
const uploadQueue = await AsyncStorage.getItem('uploadQueue');
const queue = uploadQueue ? JSON.parse(uploadQueue) : [];
queue.push({ assetId, localPath });
await AsyncStorage.setItem('uploadQueue', JSON.stringify(queue));
```

---

### 🔹 SQLite（关系数据库）⭐ 推荐

**GitHub**: https://github.com/Townk/react-native-quick-sqlite

**适用场景**:
- ✅ 结构化数据存储
- ✅ 离线缓存Assets、Projects
- ✅ 复杂查询需求

**安装**:
```bash
npm install react-native-quick-sqlite
```

**使用示例**:
```typescript
import SQLite from 'react-native-quick-sqlite';

// 打开数据库
const db = SQLite.open('bdc_ai.db');

// 创建表
db.execute(`
  CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    modality TEXT,
    local_path TEXT,
    upload_status TEXT,
    created_at INTEGER
  )
`);

// 插入数据
db.execute(`
  INSERT INTO assets (id, project_id, modality, local_path, upload_status, created_at)
  VALUES (?, ?, ?, ?, ?, ?)
`, ['asset-123', 'proj-001', 'image', '/path/to/image.jpg', 'pending', Date.now()]);

// 查询待上传的资产
const pendingAssets = db.executeQuery(`
  SELECT * FROM assets WHERE upload_status = 'pending'
`);
```

---

### 🔹 Realm（对象数据库）

**GitHub**: https://github.com/realm/realm-js

**适用场景**:
- ✅ 对象模型存储
- ✅ 自动同步到云端
- ✅ 复杂数据模型

---

### 🔹 WatermelonDB（高性能+React优化）

**GitHub**: https://github.com/Nozbe/WatermelonDB

**适用场景**:
- ✅ 大量离线数据
- ✅ 需要高性能
- ✅ React Native优化

---

## 六、地理位置与二维码

### 🔹 React Native Geolocation Service

**GitHub**: https://github.com/michalchudziak/react-native-geolocation-service

**适用场景**:
- ✅ GPS定位
- ✅ 记录现场采集位置
- ✅ 对应你的 `Asset.location_meta`

**安装**:
```bash
npm install react-native-geolocation-service
```

**使用示例**:
```typescript
import Geolocation from 'react-native-geolocation-service';

const getLocation = () => {
  Geolocation.getCurrentPosition(
    (position) => {
      const locationMeta = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        timestamp: position.timestamp
      };

      // 关联到Asset
      uploadAssetWithLocation(assetData, locationMeta);
    },
    (error) => {
      console.error(error);
    },
    { enableHighAccuracy: true, timeout: 15000 }
  );
};
```

---

### 🔹 QR/条形码扫描

#### React Native（已包含在Vision Camera中）

```tsx
import { Camera, useCodeScanner } from 'react-native-vision-camera';

const codeScanner = useCodeScanner({
  codeTypes: ['qr', 'ean-13'],
  onCodeScanned: (codes) => {
    // 扫描设备二维码
    const deviceId = codes[0].value;
    console.log('Device ID:', deviceId);
  }
});

<Camera
  codeScanner={codeScanner}
  style={styles.camera}
/>
```

#### Flutter（mobile_scanner）

```dart
MobileScanner(
  onDetect: (capture) {
    final code = capture.barcodes.first;
    if (code.type == BarcodeType.qr) {
      // 设备二维码识别
      navigateToDevice(code.rawValue);
    }
  },
)
```

---

## 七、网络请求与API集成

### 🔹 Axios（HTTP客户端）⭐ 推荐

**GitHub**: https://github.com/axios/axios

**适用场景**:
- ✅ RESTful API调用
- ✅ 文件上传
- ✅ 拦截器（Token、错误处理）

**安装**:
```bash
npm install axios
```

**配置示例**:
```typescript
import axios from 'axios';

// 创建API实例
const api = axios.create({
  baseURL: 'http://your-server:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器（添加Token）
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器（错误处理）
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Token过期，重新登录
      navigateToLogin();
    }
    return Promise.reject(error);
  }
);

// API服务
export const assetService = {
  // 上传Asset
  uploadAsset: async (projectId: string, file: any, metadata: any) => {
    const formData = new FormData();
    formData.append('file', {
      uri: file.uri,
      type: file.type,
      name: file.fileName
    });
    formData.append('project_id', projectId);
    formData.append('modality', metadata.modality);
    formData.append('location_meta', JSON.stringify(metadata.location));

    const response = await api.post('/assets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // 获取项目列表
  getProjects: async () => {
    const response = await api.get('/projects');
    return response.data;
  }
};
```

---

### 🔹 React Query（数据同步）⭐ 强烈推荐

**GitHub**: https://github.com/TanStack/query

**适用场景**:
- ✅ 自动缓存、重试
- ✅ 离线优先体验
- ✅ 后台数据同步

**安装**:
```bash
npm install @tanstack/react-query
```

**使用示例**:
```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function ProjectListScreen() {
  const queryClient = useQueryClient();

  // 获取项目列表（自动缓存）
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.get('/projects').then(res => res.data),
    staleTime: 5 * 60 * 1000, // 5分钟内不重新请求
  });

  // 上传Asset（乐观更新）
  const uploadMutation = useMutation({
    mutationFn: (data) => assetService.uploadAsset(data),
    onSuccess: () => {
      // 刷新相关数据
      queryClient.invalidateQueries(['projects']);
    }
  });

  return (
    <FlatList
      data={projects}
      renderItem={({ item }) => <ProjectCard project={item} />}
    />
  );
}
```

---

## 八、UI组件库

### 🔹 React Native Paper ⭐ 推荐（Material Design）

**GitHub**: https://github.com/callstack/react-native-paper

**官网**: https://reactnativepaper.com/

**适用场景**:
- ✅ 快速构建UI
- ✅ Material Design风格
- ✅ 丰富的组件

**安装**:
```bash
npm install react-native-paper react-native-safe-area-context
```

**核心组件**:
```tsx
import { Button, TextInput, Card, Title, Paragraph } from 'react-native-paper';

function AssetUploadScreen() {
  return (
    <Card>
      <Card.Title title="上传资料" />
      <Card.Content>
        <TextInput
          label="项目名称"
          value={projectName}
          onChangeText={text => setProjectName(text)}
        />
        <Button mode="contained" onPress={handleUpload}>
          上传图片
        </Button>
        <Button mode="outlined" onPress={handleVoiceRecord}>
          语音记录
        </Button>
      </Card.Content>
    </Card>
  );
}
```

---

### 🔹 NativeBase

**GitHub**: https://github.com/GeekyAnts/NativeBase

**适用场景**:
- ✅ 组件丰富
- ✅ 可定制主题

---

### 🔹 Flutter Material

**Flutter内置组件**，无需额外安装：
```dart
import 'package:flutter/material.dart';

Scaffold(
  appBar: AppBar(title: Text('上传资料')),
  body: Column(
    children: [
      TextField(
        decoration: InputDecoration(labelText: '项目名称'),
      ),
      ElevatedButton(
        onPressed: _handleUpload,
        child: Text('上传图片'),
      ),
    ],
  ),
)
```

---

## 九、状态管理

### 🔹 Redux Toolkit ⭐ 大型项目推荐

**GitHub**: https://github.com/reduxjs/redux-toolkit

**适用场景**:
- ✅ 复杂状态管理
- ✅ 多页面共享状态
- ✅ 需要时间旅行调试

---

### 🔹 Zustand ⭐ 轻量级推荐

**GitHub**: https://github.com/pmndrs/zustand

**适用场景**:
- ✅ 简单状态管理
- ✅ 小型项目
- ✅ 学习曲线低

**示例**:
```typescript
import create from 'zustand';

const useStore = create((set) => ({
  currentProject: null,
  setCurrentProject: (project) => set({ currentProject: project }),
  uploadQueue: [],
  addToQueue: (asset) => set((state) => ({
    uploadQueue: [...state.uploadQueue, asset]
  }))
}));

// 使用
function AssetUploadScreen() {
  const { currentProject, addToQueue } = useStore();
  // ...
}
```

---

### 🔹 MobX（响应式）

**GitHub**: https://github.com/mobxjs/mobx

---

## 十、推荐技术栈组合

### 方案1：React Native + TypeScript ⭐ MVP推荐

```yaml
框架: React Native + Expo
语言: TypeScript
UI: React Native Paper
状态管理: Zustand
网络请求: Axios + React Query
本地存储: AsyncStorage + SQLite
相机: react-native-vision-camera
语音识别: rn-whisper-stt
二维码: Vision Camera (内置)
定位: react-native-geolocation-service
```

**优势**:
- ✅ 快速开发
- ✅ 热更新（CodePush）
- ✅ 丰富的生态

**项目初始化**:
```bash
# 使用Expo（最简单）
npx create-expo-app bdc-ai-app

# 安装依赖
cd bdc-ai-app
npm install @react-native-async-storage/async-storage
npm install react-native-paper
npm install @tanstack/react-query
npm install axios
```

---

### 方案2：Flutter + Dart

```yaml
框架: Flutter
语言: Dart
UI: Material Design (内置)
状态管理: Provider / Riverpod
网络请求: dio
本地存储: sqflite + shared_preferences
相机: camera
语音识别: whisper_kit
二维码: mobile_scanner
定位: geolocator
```

**优势**:
- ✅ 性能更好
- ✅ UI更流畅
- ✅ 自定义能力强

**项目初始化**:
```bash
flutter create bdc_ai_app
cd bdc_ai_app
flutter pub add dio provider sqflite camera
```

---

### 方案3：uni-app（小程序优先）⭐ 国内推荐

```yaml
框架: uni-app
语言: Vue.js + TypeScript
UI: uni-ui (官方组件库)
状态管理: Vuex / Pinia
网络请求: uni.request封装
本地存储: uni.storage
相机: uni.chooseImage
语音识别: uni.getRecorderManager + 云API
二维码: uni.scanCode
定位: uni.getLocation
```

**优势**:
- ✅ 一套代码多端运行
- ✅ 支持小程序
- ✅ 学习成本低

**项目初始化**:
```bash
# 使用HBuilderX可视化创建
# 或使用CLI
npx @dcloudio/uvm create bdc-ai-miniprogram
```

---

## 十一、核心功能实现示例

### 📸 图片上传 + 关联项目

```typescript
// services/AssetService.ts
import Geolocation from 'react-native-geolocation-service';
import axios from 'axios';

export class AssetService {
  // 上传图片并关联项目
  static async uploadImageWithMetadata(
    projectId: string,
    imageUri: string,
    tags: string[]
  ) {
    // 1. 获取GPS位置
    const location = await this.getCurrentLocation();

    // 2. 构造FormData
    const formData = new FormData();
    formData.append('file', {
      uri: imageUri,
      type: 'image/jpeg',
      name: `${Date.now()}.jpg`
    });
    formData.append('project_id', projectId);
    formData.append('modality', 'image');
    formData.append('location_meta', JSON.stringify({
      latitude: location.latitude,
      longitude: location.longitude,
      accuracy: location.accuracy
    }));
    formData.append('tags', JSON.stringify(tags));
    formData.append('source', 'mobile_app');

    // 3. 上传到服务器
    const response = await axios.post(
      'http://your-server:8000/api/v1/assets/upload',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );

    return response.data;
  }

  static getCurrentLocation(): Promise<any> {
    return new Promise((resolve, reject) => {
      Geolocation.getCurrentPosition(
        (position) => resolve(position.coords),
        (error) => reject(error),
        { enableHighAccuracy: true, timeout: 15000 }
      );
    });
  }
}
```

---

### 🎤 语音录制 + 转文字

```typescript
// services/VoiceService.ts
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

export class VoiceService {
  private recording: Audio.Recording | null = null;

  // 开始录音
  async startRecording() {
    try {
      this.recording = new Audio.Recording();
      await this.recording.prepareToRecordAsync(
        Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY
      );
      await this.recording.startAsync();
    } catch (error) {
      console.error('录音失败:', error);
    }
  }

  // 停止录音并转文字
  async stopAndTranscribe(): Promise<string> {
    if (!this.recording) return '';

    await this.recording.stopAsync();
    const uri = this.recording.getURI();
    this.recording = null;

    // 方案1: 使用本地Whisper（离线）
    // const transcript = await this.transcribeWithWhisper(uri);

    // 方案2: 使用百度ASR（在线，中文更好）
    const transcript = await this.transcribeWithBaidu(uri);

    return transcript;
  }

  // 本地Whisper识别
  async transcribeWithWhisper(uri: string): Promise<string> {
    // 使用 rn-whisper-stt
    const WhisperSTT = require('rn-whisper-stt').default;
    const whisper = new WhisperSTT({
      model: 'tiny',
      language: 'zh'
    });

    const transcript = await whisper.transcribe(uri);
    return transcript;
  }

  // 百度ASR识别
  async transcribeWithBaidu(uri: string): Promise<string> {
    const base64Audio = await FileSystem.readAsStringAsync(uri, {
      encoding: FileSystem.EncodingType.Base64
    });

    const response = await fetch('https://vop.baidu.com/server_api', {
      method: 'POST',
      headers: {
        'Content-Type': 'audio/wav; rate=16000'
      },
      body: JSON.stringify({
        format: 'wav',
        rate: 16000,
        channel: 1,
        cuid: 'unique_device_id',
        token: 'your_baidu_api_token',
        speech: base64Audio,
        len: base64Audio.length
      })
    });

    const result = await response.json();
    return result.result[0];
  }
}
```

---

### 📱 扫描设备二维码

```typescript
import { useCodeScanner } from 'react-native-vision-camera';

function DeviceScannerScreen({ navigation }) {
  const codeScanner = useCodeScanner({
    codeTypes: ['qr', 'ean-13'],
    onCodeScanned: (codes) => {
      const deviceId = codes[0].value;

      // 跳转到设备详情页
      navigation.navigate('DeviceDetail', { deviceId });
    }
  });

  return (
    <Camera
      codeScanner={codeScanner}
      style={StyleSheet.absoluteFill}
    />
  );
}
```

---

## 十二、离线优先架构

### 离线上传队列

```typescript
// services/OfflineQueue.ts
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

export class OfflineQueue {
  private static QUEUE_KEY = 'upload_queue';

  // 添加到队列
  static async add(assetData: any) {
    const queue = await this.getQueue();
    queue.push({
      ...assetData,
      id: `${Date.now()}`,
      timestamp: Date.now(),
      status: 'pending'
    });

    await AsyncStorage.setItem(this.QUEUE_KEY, JSON.stringify(queue));
  }

  // 获取队列
  static async getQueue(): Promise<any[]> {
    const queueJson = await AsyncStorage.getItem(this.QUEUE_KEY);
    return queueJson ? JSON.parse(queueJson) : [];
  }

  // 同步到服务器
  static async sync() {
    // 1. 检查网络
    const netInfo = await NetInfo.fetch();
    if (!netInfo.isConnected) return;

    // 2. 获取待上传队列
    const queue = await this.getQueue();
    const pendingItems = queue.filter(item => item.status === 'pending');

    // 3. 逐个上传
    for (const item of pendingItems) {
      try {
        await uploadToServer(item);

        // 4. 更新状态为已上传
        await this.updateStatus(item.id, 'uploaded');
      } catch (error) {
        console.error('上传失败:', error);
        await this.updateStatus(item.id, 'failed');
      }
    }

    // 5. 清理已上传的项目
    await this.cleanup();
  }

  // 更新状态
  static async updateStatus(id: string, status: string) {
    const queue = await this.getQueue();
    const index = queue.findIndex(item => item.id === id);
    if (index !== -1) {
      queue[index].status = status;
      await AsyncStorage.setItem(this.QUEUE_KEY, JSON.stringify(queue));
    }
  }

  // 清理已上传的项目（保留最近7天）
  static async cleanup() {
    const queue = await this.getQueue();
    const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;

    const cleanedQueue = queue.filter(item => {
      if (item.status === 'uploaded' && item.timestamp < sevenDaysAgo) {
        return false;
      }
      return true;
    });

    await AsyncStorage.setItem(this.QUEUE_KEY, JSON.stringify(cleanedQueue));
  }
}

// App启动时自动同步
NetInfo.addEventListener(state => {
  if (state.isConnected) {
    OfflineQueue.sync();
  }
});
```

---

## 十三、移动端与后端API对接

### API接口设计（对应你的PLAN.md）

```typescript
// api/types.ts
export interface AssetUploadRequest {
  project_id: string;
  building_id?: string;
  zone_id?: string;
  system_id?: string;
  device_id?: string;
  modality: 'image' | 'table' | 'text' | 'audio';
  file: File;
  location_meta?: {
    latitude: number;
    longitude: number;
    accuracy: number;
  };
  tags: string[];
  source: 'mobile_app';
}

export interface AssetUploadResponse {
  asset_id: string;
  status: 'parsed' | 'pending';
  upload_url: string;
}
```

```typescript
// api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: 'http://your-server:8000/api/v1',
  timeout: 30000
});

// 拦截器
apiClient.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## 十四、性能优化建议

### 图片压缩

```typescript
import ImageResizer from 'react-native-image-resizer';

async function compressImage(uri: string): Promise<string> {
  const resizedImage = await ImageResizer.createResizedImage(
    uri,
    1024,  // 宽度
    1024,  // 高度
    'JPEG',
    80,    // 质量
    0,     // 旋转
    null   // 输出路径
  );

  return resizedImage.uri;
}

// 使用
const compressedUri = await compressImage(originalUri);
await AssetService.uploadImageWithMetadata(projectId, compressedUri, tags);
```

---

## 十五、关键仓库快速链接

### 跨平台框架
- https://github.com/facebook/react-native
- https://github.com/flutter/flutter
- https://github.com/dcloudio/uni-app
- https://github.com/NervJS/taro

### React Native核心库
- https://github.com/mrousavy/react-native-vision-camera (相机)
- https://github.com/react-native-image-picker/react-native-image-picker (图片选择)
- https://github.com/TanStack/query (React Query)
- https://github.com/axios/axios (HTTP客户端)
- https://github.com/react-native-async-storage/async-storage (本地存储)
- https://github.com/michalchudziak/react-native-geolocation-service (定位)

### Flutter核心库
- https://pub.dev/packages/camera (相机)
- https://pub.dev/packages/mobile_scanner (二维码)
- https://pub.dev/packages/whisper_kit (语音识别)
- https://pub.dev/packages/sqflite (数据库)
- https://pub.dev/packages/dio (HTTP客户端)

### 语音识别
- https://github.com/israr002/rn-whisper-stt (React Native Whisper)
- https://pub.dev/packages/whisper_kit (Flutter Whisper)

### UI组件库
- https://github.com/callstack/react-native-paper (RN Material Design)
- https://github.com/GeekyAnts/NativeBase (RN组件库)

### 状态管理
- https://github.com/pmndrs/zustand (轻量级)
- https://github.com/reduxjs/redux-toolkit (Redux)

---

## 十六、技术选型决策树

```
团队有React经验？
├─ 是 → React Native
│   ├─ 需要小程序？
│   │   ├─ 是 → Taro
│   │   └─ 否 → React Native + Expo
│   └─ 追求快速开发？
│       ├─ 是 → Expo
│       └─ 否 → React Native CLI
└─ 否 → 团队熟悉Vue？
    ├─ 是 → uni-app（多端）
    └─ 否 → Flutter（性能优先）
```

---

## 十七、快速开始命令

### React Native (Expo)
```bash
npx create-expo-app bdc-ai-app
cd bdc-ai-app
npm install react-native-paper @tanstack/react-query axios
npm install expo-camera expo-location expo-av
npx expo start
```

### Flutter
```bash
flutter create bdc_ai_app
cd bdc_ai_app
flutter pub add dio provider camera geolocator
flutter pub add whisper_kit mobile_scanner
flutter run
```

### uni-app
```bash
# 使用HBuilderX创建项目
# 或CLI
npx @dcloudio/uvm create bdc-ai-miniprogram
cd bdc-ai-miniprogram
npm install
npm run dev:mp-weixin
```

---

**文档版本**: v1.0
**最后更新**: 2026-01-17
**维护者**: BDC-AI项目组

---

## 下一步建议

1. **Week 1**: 选择技术栈并搭建项目框架
2. **Week 2**: 实现图片上传 + 项目关联
3. **Week 3**: 集成语音识别（ASR）
4. **Week 4**: 实现离线队列 + 自动同步
5. **Week 5**: GPS定位 + 二维码扫描
6. **Week 6**: UI优化 + 测试

需要我提供某个具体功能的完整代码示例吗？
