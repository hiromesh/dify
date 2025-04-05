'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useRouter } from 'next/navigation'
import { useContext, useContextSelector } from 'use-context-selector'
import cn from '@/utils/classnames'
import Button from '@/app/components/base/button'
import AppIcon from '@/app/components/base/app-icon'
import Textarea from '@/app/components/base/textarea'
import Input from '@/app/components/base/input'
import AppIconPicker from '../../base/app-icon-picker'
import type { AppIconSelection } from '../../base/app-icon-picker'
import { ToastContext } from '@/app/components/base/toast'
import AppsContext from '@/context/app-context'
import { createApp } from '@/service/apps'
import { NEED_REFRESH_APP_LIST_KEY } from '@/config'
import { getRedirection } from '@/utils/app-redirection'
import FullScreenModal from '@/app/components/base/fullscreen-modal'
import { ChevronRight } from '@/app/components/base/icons/src/vender/line/arrows'
import { ChevronDown } from '@/app/components/base/icons/src/vender/solid/arrows'
import {
  RiApps2Line,
  RiCheckFill,
  RiFlowChart,
  RiLightbulbLine,
  RiRobot2Line,
  RiSettings4Line,
  RiUser3Line,
} from '@remixicon/react'

// 创建游戏需求处理状态类型
type ProcessStep = {
  key: string
  title: string
  description: string
  status: 'completed' | 'current' | 'pending'
  icon: React.ReactNode
}

type Message = {
  role: 'user' | 'assistant'
  content: string
  isLoading?: boolean
}

type CreateFromGameRequirementsProps = {
  onSuccess: () => void
  onClose: () => void
}

function CreateFromGameRequirements({ onClose, onSuccess }: CreateFromGameRequirementsProps) {
  const { t } = useTranslation()
  const { push } = useRouter()
  const { notify } = useContext(ToastContext)
  const mutateApps = useContextSelector(AppsContext, state => state.mutateApps)

  // 应用信息相关状态
  const [isCreating, setIsCreating] = useState(false)
  const [appIcon, setAppIcon] = useState<AppIconSelection>({ type: 'emoji', icon: '🎮', background: '#FFEAD5' })
  const [showAppIconPicker, setShowAppIconPicker] = useState(false)
  const [name, setName] = useState('')
  const [gameRequirements, setGameRequirements] = useState('')
  const [showAppInfo, setShowAppInfo] = useState(true)

  // 聊天和处理相关状态
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '你好！请描述你想要创建的游戏需求，我将帮助你分析并生成相应的工作流。' },
  ])
  const [userInput, setUserInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 处理步骤状态
  const [steps, setSteps] = useState<ProcessStep[]>([
    {
      key: 'requirements',
      title: '需求内容分析',
      description: '分析游戏类型和核心需求',
      status: 'pending',
      icon: <RiLightbulbLine size={16} />,
    },
    {
      key: 'design',
      title: '策划文档分析',
      description: '生成游戏设计框架',
      status: 'pending',
      icon: <RiSettings4Line size={16} />,
    },
    {
      key: 'features',
      title: '功能分解',
      description: '拆分游戏系统功能模块',
      status: 'pending',
      icon: <RiApps2Line size={16} />,
    },
    {
      key: 'workflow',
      title: '工作流完善',
      description: '优化工作流节点和连接',
      status: 'pending',
      icon: <RiFlowChart size={16} />,
    },
  ])

  // 滚动到最新消息
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 根据应用名自动填充游戏需求简述
  const handleAutoFillDescription = useCallback(() => {
    if (!name.trim() || gameRequirements) return

    // 如果有名称但没有简述，自动生成简单描述
    setGameRequirements(`一个名为"${name}"的游戏`)
  }, [name, gameRequirements])

  // 添加确认应用信息的函数
  const confirmAppInfo = useCallback(() => {
    if (name && gameRequirements)
      setShowAppInfo(false)
    else
      notify({ type: 'error', message: t('app.newApp.infoRequired', '请填写应用名称和游戏需求') })
  }, [name, gameRequirements, notify, t])

  // 模拟Agent处理消息
  const handleSendMessage = useCallback(() => {
    if (!userInput.trim()) return

    // 确保游戏需求已填写
    if (!gameRequirements)
      handleAutoFillDescription()

    // 添加用户消息
    const newUserMessage: Message = { role: 'user', content: userInput }
    setMessages(prev => [...prev, newUserMessage])

    // 添加加载中的Agent消息
    const loadingMessage: Message = { role: 'assistant', content: '', isLoading: true }
    setMessages(prev => [...prev, loadingMessage])

    setUserInput('')
    setIsProcessing(true)

    // 模拟处理步骤
    let currentStepIndex = steps.findIndex(step => step.status === 'current')
    if (currentStepIndex === -1) {
      // 开始第一个步骤
      const newSteps = [...steps]
      newSteps[0].status = 'current'
      setSteps(newSteps)
      currentStepIndex = 0
    }

    // 延迟显示Agent回复，模拟思考时间
    setTimeout(() => {
      let agentResponse = ''

      // 根据当前步骤生成不同的回复
      switch (steps[currentStepIndex].key) {
        case 'requirements':
          agentResponse = `我已分析了你的游戏需求，看起来你想创建的是一个${userInput.includes('RPG') ? 'RPG类型的游戏' : '游戏'}。\n\n让我继续分析游戏的核心机制和目标受众。请告诉我更多关于你期望的游戏体验是怎样的？`
          break
        case 'design':
          agentResponse = '我已经完成了策划文档分析，基于你的需求，我推荐以下游戏设计框架：\n\n1. 核心玩法循环：探索 → 战斗 → 收集资源 → 升级装备 → 探索更高难度区域\n2. 玩家进度系统：基于技能树和装备升级\n3. 游戏难度曲线：随玩家进度动态调整\n\n你认为这个框架是否符合你的预期？'
          break
        case 'features':
          agentResponse = '我已将游戏功能分解为以下模块：\n\n1. 角色成长系统\n2. 战斗机制\n3. 物品与装备系统\n4. 任务系统\n5. 动态难度调节系统\n\n我们可以优先实现哪个模块？'
          break
        case 'workflow':
          agentResponse = '工作流已经完善，包含以下主要节点：\n\n1. 玩家输入/行为分析\n2. 游戏状态评估\n3. 难度参数调整\n4. 资源分配优化\n5. 反馈系统\n\n这个工作流程将使游戏体验既有挑战性又保持平衡。我们已经准备好将这个设计转换为实际的应用了！'
          break
        default:
          agentResponse = '我理解了你的需求，让我们继续讨论下一步。'
          break
      }

      // 替换正在载入的消息
      setMessages((prev) => {
        const lastIndex = prev.length - 1
        if (lastIndex >= 0 && prev[lastIndex].isLoading) {
          const updatedMessages = [...prev]
          updatedMessages[lastIndex] = { role: 'assistant', content: agentResponse }
          return updatedMessages
        }
        return [...prev, { role: 'assistant', content: agentResponse }]
      })

      setIsProcessing(false)

      // 更新步骤状态
      if (currentStepIndex < steps.length - 1) {
        const newSteps = [...steps]
        newSteps[currentStepIndex].status = 'completed'
        newSteps[currentStepIndex + 1].status = 'current'
        setSteps(newSteps)
      }
      else {
        // 所有步骤完成
        const newSteps = [...steps]
        newSteps[currentStepIndex].status = 'completed'
        setSteps(newSteps)
      }
    }, 1500)
  }, [userInput, steps, gameRequirements, handleAutoFillDescription])

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // 切换应用信息区域显示/隐藏
  const toggleAppInfo = useCallback(() => {
    setShowAppInfo(prev => !prev)
  }, [])

  // 渲染消息气泡
  const renderMessage = useCallback((message: Message, index: number) => {
    const isUser = message.role === 'user'

    return (
      <div
        key={index}
        className={cn(
          'mb-4 flex items-start',
          isUser ? 'justify-end' : 'justify-start',
        )}
      >
        {!isUser && (
          <div className="mr-2 mt-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-white">
              <RiRobot2Line size={16} />
            </div>
          </div>
        )}

        <div
          className={cn(
            'max-w-[85%] rounded-lg px-3 py-2',
            isUser
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100',
          )}
        >
          {message.isLoading ? (
            <div className="flex items-center space-x-1">
              <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 dark:bg-gray-500" style={{ animationDelay: '0ms' }}></div>
              <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 dark:bg-gray-500" style={{ animationDelay: '150ms' }}></div>
              <div className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 dark:bg-gray-500" style={{ animationDelay: '300ms' }}></div>
            </div>
          ) : (
            <div className="whitespace-pre-line break-words">{message.content}</div>
          )}
        </div>

        {isUser && (
          <div className="ml-2 mt-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-400 text-white">
              <RiUser3Line size={16} />
            </div>
          </div>
        )}
      </div>
    )
  }, [])

  // 创建应用
  const handleConfirm = useCallback(async () => {
    if (!name.trim()) {
      notify({ type: 'error', message: t('app.newApp.nameError', '请输入应用名称') })
      return
    }

    if (!gameRequirements.trim()) {
      notify({ type: 'error', message: t('app.newApp.gameRequirementsError', '请输入游戏需求') })
      return
    }

    try {
      setIsCreating(true)
      const res = await createApp({
        name,
        icon_type: appIcon.type,
        icon: appIcon.type === 'emoji' ? appIcon.icon : '',
        icon_background: appIcon.type === 'emoji' ? appIcon.background : '',
        description: `基于游戏需求创建: ${gameRequirements.slice(0, 100)}${gameRequirements.length > 100 ? '...' : ''}`,
        mode: 'chat',
      })

      localStorage.setItem(NEED_REFRESH_APP_LIST_KEY, '1')
      mutateApps()
      onSuccess()
      onClose()

      setTimeout(() => {
        push(getRedirection(res.id, '/app/metadata'))
      }, 300)
    }
    catch (e) {
      console.error(e)
      notify({ type: 'error', message: t('app.newApp.createFailed', '创建应用失败') })
    }
    finally {
      setIsCreating(false)
    }
  }, [name, gameRequirements, appIcon, notify, t, push, onSuccess, onClose, mutateApps])

  return (
    <div className='flex h-[90vh] flex-col rounded-xl bg-white dark:bg-gray-900'>
      {/* 应用信息部分 - 可折叠 */}
      <div className='border-b border-gray-200 px-6 py-4 dark:border-gray-700'>
        <div className='flex items-center justify-between'>
          <div className="text-xl font-semibold text-gray-900 dark:text-white">
            {t('app.fromGameRequirements', '从游戏需求创建')}
          </div>
          <button
            onClick={toggleAppInfo}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            {showAppInfo ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
          </button>
        </div>

        {showAppInfo && (
          <div className='animate-fadeIn mt-4'>
            <div className='mb-3 grid grid-cols-6 gap-4'>
              <div className='col-span-5'>
                <Input
                  autoFocus
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder={t('app.appNamePlaceholder', '输入应用名称')}
                  className='mb-2'
                />
                <Input
                  value={gameRequirements}
                  onChange={e => setGameRequirements(e.target.value)}
                  placeholder={t('app.gameRequirementsPlaceholder', '游戏需求简述（可选）')}
                  disabled={messages.length > 1}
                />
              </div>
              <div className='col-span-1 text-center'>
                <div
                  className='inline-flex cursor-pointer flex-col items-center'
                  onClick={() => setShowAppIconPicker(true)}
                >
                  {appIcon.type === 'emoji' ? (
                    <AppIcon
                      size='large'
                      rounded
                      icon={appIcon.icon}
                      background={appIcon.background}
                    />
                  ) : (
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100">
                      <span className="text-gray-500">图标</span>
                    </div>
                  )}
                  <div className='mt-1 text-xs font-medium text-primary-600'>{t('common.operation.edit', '编辑图标')}</div>
                </div>
              </div>
            </div>
            <div className='flex justify-end'>
              <Button className='bg-primary-600 text-white hover:bg-primary-700' size='small' onClick={confirmAppInfo}>
                {t('common.operation.confirm', '确认')}
              </Button>
            </div>
          </div>
        )}

        {!showAppInfo && (
          <div className="mt-2 flex items-center text-sm text-gray-500 dark:text-gray-400">
            <div className="mr-3 shrink-0">
              {appIcon.type === 'emoji' ? (
                <AppIcon
                  size='small'
                  rounded
                  icon={appIcon.icon}
                  background={appIcon.background}
                />
              ) : (
                <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-gray-100">
                  <span className="text-xs text-gray-500">图</span>
                </div>
              )}
            </div>
            <div className="truncate font-medium">
              {name || t('app.newApp.untitled', '未命名应用')}
              {gameRequirements && <span className="ml-2 text-xs opacity-60">{gameRequirements}</span>}
            </div>
          </div>
        )}
      </div>

      {/* 进度步骤 */}
      <div className='border-b border-gray-200 bg-gray-50 px-6 py-3 dark:border-gray-700 dark:bg-gray-800'>
        <div className='flex items-center justify-between space-x-2'>
          {steps.map((step, index) => (
            <div key={step.key} className='flex flex-1 items-center'>
              {/* 步骤指示器 */}
              <div className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
                step.status === 'completed' ? 'bg-green-500 text-white'
                  : step.status === 'current' ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400',
              )}>
                {step.status === 'completed' ? (
                  <RiCheckFill size={16} />
                ) : (
                  step.icon
                )}
              </div>

              {/* 步骤文本 */}
              <div className='ml-2'>
                <div className={cn(
                  'text-sm font-medium',
                  step.status === 'completed' ? 'text-green-600 dark:text-green-400'
                    : step.status === 'current' ? 'text-primary-600 dark:text-primary-400'
                      : 'text-gray-500 dark:text-gray-400',
                )}>
                  {step.title}
                </div>
                <div className='text-xs text-gray-500 dark:text-gray-400'>
                  {step.description}
                </div>
              </div>

              {/* 连接线 */}
              {index < steps.length - 1 && (
                <div className={cn(
                  'mx-2 h-0.5 flex-1',
                  step.status === 'completed' ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-700',
                )} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 聊天区域 */}
      <div className='flex-1 overflow-y-auto p-4'>
        {messages.map(renderMessage)}
        <div ref={messagesEndRef} />
      </div>

      {/* 底部输入区域 */}
      <div className='border-t border-gray-200 p-4 dark:border-gray-700'>
        <div className='relative'>
          <Textarea
            value={userInput}
            onChange={e => setUserInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={t('common.chat.placeholder', '输入您的需求...')}
            className='min-h-[80px] resize-none pr-24'
            autoSize
          />
          <div className='absolute bottom-2 right-2 flex items-center'>
            <Button
              className='flex items-center bg-primary-600 text-white hover:bg-primary-700'
              onClick={handleSendMessage}
              disabled={isProcessing || !userInput.trim()}
            >
              {t('common.chat.send', '发送')}
            </Button>
          </div>
        </div>
      </div>

      {/* 底部操作栏 */}
      <div className='flex items-center justify-between border-t border-gray-200 px-6 py-4 dark:border-gray-700'>
        <Button onClick={onClose}>
          {t('common.operation.cancel', '取消')}
        </Button>
        <Button
          className='bg-primary-600 text-white hover:bg-primary-700'
          onClick={handleConfirm}
          disabled={isCreating || !name.trim() || !gameRequirements.trim()}
        >
          {isCreating ? t('app.newApp.creating', '创建中...') : t('common.operation.confirm', '确认')}
        </Button>
      </div>

      {showAppIconPicker && (
        <AppIconPicker
          onSelect={(icon) => {
            setAppIcon(icon)
            setShowAppIconPicker(false)
          }}
          onClose={() => setShowAppIconPicker(false)}
        />
      )}
    </div>
  )
}

type CreateFromGameRequirementsModalProps = {
  show: boolean
  onClose: () => void
  onSuccess: () => void
}

function CreateFromGameRequirementsModal({
  show,
  onClose,
  onSuccess,
}: CreateFromGameRequirementsModalProps) {
  return (
    <FullScreenModal
      open={show}
      onClose={onClose}
      className='overflow-hidden p-0 sm:!max-h-[90vh] sm:!max-w-[900px]'
      overflowVisible={false}
    >
      <CreateFromGameRequirements
        onClose={onClose}
        onSuccess={onSuccess}
      />
    </FullScreenModal>
  )
}

export default CreateFromGameRequirementsModal
