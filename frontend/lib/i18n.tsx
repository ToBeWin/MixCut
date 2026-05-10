'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'

export type Locale = 'zh-CN' | 'en-US'

type Messages = Record<string, string>

const STORAGE_KEY = 'mixcut.locale'

const messages: Record<Locale, Messages> = {
  'zh-CN': {
    'common.export': '导出',
    'common.save': '保存',
    'common.loading': '加载中...',
    'common.default': '默认',
    'topbar.file': '文件',
    'topbar.edit': '编辑',
    'topbar.sequence': '序列',
    'topbar.view': '视图',
    'topbar.help': '帮助',
    'topbar.search': '搜索工作台...',
    'topbar.language': '语言',
    'topbar.locale.zh': '中文',
    'topbar.locale.en': 'English',
    'dashboard.title': '最近项目',
    'dashboard.subtitle': '管理当前编辑、渲染队列和待审核草稿。',
    'dashboard.newProject': '新建项目',
    'dashboard.loading': '正在加载项目...',
    'dashboard.emptyTitle': '还没有项目',
    'dashboard.emptyDescription': '创建你的第一个项目以开始使用。',
    'chat.title': '纠错',
    'chat.emptyTitle': '描述你的修改需求',
    'chat.emptyDescription': '例如“让开场更快一些”或“把第 2 段替换成室外镜头”',
    'chat.quick.replan.label': '重做规划',
    'chat.quick.replan.prompt': '请重新规划整条剪辑结构',
    'chat.quick.subtitle.label': '添加字幕',
    'chat.quick.subtitle.prompt': '请为这条视频添加字幕',
    'chat.quick.voiceover.label': '添加配音',
    'chat.quick.voiceover.prompt': '请为这条视频添加一段配音解说',
    'chat.quick.refine.label': '优化节奏',
    'chat.quick.refine.prompt': '请把当前剪辑优化得更有吸引力',
    'chat.input.placeholder': '描述一个修改...',
    'chat.send': '发送',
    'chat.voice.start': '语音输入',
    'chat.voice.stop': '停止录音',
    'chat.voice.unsupported': '当前浏览器不支持语音输入',
    'chat.voice.listening': '正在听你说...',
    'chat.voice.idle': '点击麦克风开始语音输入',
    'chat.agent.success': '已收到修改指令，正在重新处理受影响的片段...',
    'chat.agent.error': '修改处理失败，请稍后再试。',
    'settings.badge': '配置',
    'settings.title': '模型路由与 AI 推理',
    'settings.save': '保存路由',
    'settings.fleet': '当前模型集群',
    'settings.onlineCount': '{online}/{total} 在线',
    'settings.loadingModels': '正在加载模型...',
    'settings.online': '在线',
    'settings.offline': '离线',
    'settings.vision': '多模态',
    'settings.context': '上下文',
    'settings.routes': '任务路由',
    'settings.primaryProvider': '主模型提供方',
    'settings.primaryModel': '主模型',
    'settings.fallbacks': '回退链路',
    'settings.noFallbacks': '无',
    'settings.saved': '已保存',
    'settings.route.multimodal_understanding': '图像/视频理解',
    'settings.route.edit_planning': '剪辑规划',
    'settings.route.correction_intent': '纠错理解',
    'settings.route.tts_script_writing': '配音脚本',
    'settings.modality.multimodal': '多模态',
    'settings.modality.text': '文本',
    'modelSelector.title': '模型覆盖',
    'assets.title': '素材',
    'assets.import': '导入素材',
    'assets.all': '全部',
    'assets.ready': '就绪',
    'assets.empty': '还没有素材，上传视频或图片开始使用。',
    'upload.title': '素材导入',
    'upload.subtitle': '上传原始视频或图片素材，并定义生成目标。',
    'upload.workspace': '工作区已激活',
    'upload.dropTitle': '拖拽媒体到这里',
    'upload.dropDescription': '支持 MP4、MOV、JPG、PNG、WebP 和 4K 源素材。',
    'upload.queue': '处理队列',
    'upload.item.uploading': '上传中...',
    'upload.item.ready': '已就绪',
    'upload.item.error': '失败',
    'upload.item.queued': '排队中',
    'upload.item.imageReady': '图片已就绪',
  },
  'en-US': {
    'common.export': 'Export',
    'common.save': 'Save',
    'common.loading': 'Loading...',
    'common.default': 'Default',
    'topbar.file': 'File',
    'topbar.edit': 'Edit',
    'topbar.sequence': 'Sequence',
    'topbar.view': 'View',
    'topbar.help': 'Help',
    'topbar.search': 'Search studio...',
    'topbar.language': 'Language',
    'topbar.locale.zh': '中文',
    'topbar.locale.en': 'English',
    'dashboard.title': 'Recent Projects',
    'dashboard.subtitle': 'Manage active edits, render queues, and review drafts.',
    'dashboard.newProject': 'New Project',
    'dashboard.loading': 'Loading projects...',
    'dashboard.emptyTitle': 'No projects yet',
    'dashboard.emptyDescription': 'Create your first project to get started.',
    'chat.title': 'Corrections',
    'chat.emptyTitle': 'Describe your changes',
    'chat.emptyDescription': 'Try requests like "Make the opening faster" or "Swap clip 2 for outdoor footage"',
    'chat.quick.replan.label': 'Re-plan',
    'chat.quick.replan.prompt': 'Please re-plan the edit sequence from scratch',
    'chat.quick.subtitle.label': 'Add subtitles',
    'chat.quick.subtitle.prompt': 'Add subtitles to this video',
    'chat.quick.voiceover.label': 'Add voiceover',
    'chat.quick.voiceover.prompt': 'Add a voiceover narration',
    'chat.quick.refine.label': 'Refine',
    'chat.quick.refine.prompt': 'Refine the current edit to be more engaging',
    'chat.input.placeholder': 'Describe a correction...',
    'chat.send': 'Send',
    'chat.voice.start': 'Voice Input',
    'chat.voice.stop': 'Stop Recording',
    'chat.voice.unsupported': 'Voice input is not supported in this browser',
    'chat.voice.listening': 'Listening...',
    'chat.voice.idle': 'Click the mic to start dictation',
    'chat.agent.success': 'Correction received. Re-processing the affected segments...',
    'chat.agent.error': 'Sorry, the correction could not be processed. Please try again.',
    'settings.badge': 'Configuration',
    'settings.title': 'Model Routing & AI Inference',
    'settings.save': 'Save Routing',
    'settings.fleet': 'Active Model Fleet',
    'settings.onlineCount': '{online}/{total} online',
    'settings.loadingModels': 'Loading models...',
    'settings.online': 'Online',
    'settings.offline': 'Offline',
    'settings.vision': 'Vision',
    'settings.context': 'Context',
    'settings.routes': 'Task Routing',
    'settings.primaryProvider': 'Primary Provider',
    'settings.primaryModel': 'Primary Model',
    'settings.fallbacks': 'Fallback Chain',
    'settings.noFallbacks': 'None',
    'settings.saved': 'Saved',
    'settings.route.multimodal_understanding': 'Image / Video Understanding',
    'settings.route.edit_planning': 'Edit Planning',
    'settings.route.correction_intent': 'Correction Intent',
    'settings.route.tts_script_writing': 'TTS Script',
    'settings.modality.multimodal': 'Multimodal',
    'settings.modality.text': 'Text',
    'modelSelector.title': 'Model Overrides',
    'assets.title': 'Assets',
    'assets.import': 'Import Media',
    'assets.all': 'All',
    'assets.ready': 'Ready',
    'assets.empty': 'No assets yet. Upload videos or images to get started.',
    'upload.title': 'Media Ingest',
    'upload.subtitle': 'Upload raw video or image assets and define the generation target.',
    'upload.workspace': 'Workspace Active',
    'upload.dropTitle': 'Drag and drop media here',
    'upload.dropDescription': 'Supports MP4, MOV, JPG, PNG, WebP, and 4K source media.',
    'upload.queue': 'Processing Queue',
    'upload.item.uploading': 'Uploading...',
    'upload.item.ready': 'Ready',
    'upload.item.error': 'Error',
    'upload.item.queued': 'Queued',
    'upload.item.imageReady': 'Image Ready',
  },
}

interface I18nContextValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: string, vars?: Record<string, string | number>) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

function getInitialLocale(): Locale {
  if (typeof window === 'undefined') return 'en-US'
  const stored = window.localStorage.getItem(STORAGE_KEY)
  if (stored === 'zh-CN' || stored === 'en-US') return stored
  return window.navigator.language.toLowerCase().startsWith('zh') ? 'zh-CN' : 'en-US'
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(getInitialLocale)

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, locale)
    document.documentElement.lang = locale
  }, [locale])

  const value = useMemo<I18nContextValue>(() => {
    const setLocale = (nextLocale: Locale) => setLocaleState(nextLocale)
    const t = (key: string, vars?: Record<string, string | number>) => {
      const template = messages[locale][key] ?? messages['en-US'][key] ?? key
      if (!vars) return template
      return Object.entries(vars).reduce((result, [name, value]) => {
        return result.replaceAll(`{${name}}`, String(value))
      }, template)
    }
    return { locale, setLocale, t }
  }, [locale])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider')
  }
  return context
}
