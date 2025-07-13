import { ref, computed, watch, onMounted } from 'vue'

// 主题配置
const THEMES = {
  light: {
    id: 'light',
    name: '浅色模式',
    icon: '☀️',
    class: 'theme-light',
    colors: {
      primary: '#0A84FF',
      success: '#32D74B',
      warning: '#FF9F0A',
      danger: '#FF453A',
      info: '#64D2FF',
      textPrimary: '#000000',
      textSecondary: '#6B6B6B',
      textTertiary: '#8E8E93',
      backgroundPrimary: '#F5F5F7',
      backgroundSecondary: '#FFFFFF',
      backgroundTertiary: '#F2F2F7',
      borderColor: '#D2D2D7',
      borderColorLight: '#E5E5EA'
    }
  },
  orange: {
    id: 'orange',
    name: 'CNB鲜橙色',
    icon: '🔸',
    class: 'theme-orange',
    colors: {
      primary: '#FF8C00',
      success: '#32D74B',
      warning: '#FF9F0A',
      danger: '#FF453A',
      info: '#64D2FF',
      textPrimary: '#2C1810',
      textSecondary: '#8B5A3C',
      textTertiary: '#A0714D',
      backgroundPrimary: '#FFF8F0',
      backgroundSecondary: '#FFFFFF',
      backgroundTertiary: '#FFF3E6',
      borderColor: '#E6C7A3',
      borderColorLight: '#F0D9B8'
    }
  },
  dark: {
    id: 'dark',
    name: '夜间模式',
    icon: '🌙',
    class: 'theme-dark',
    colors: {
      primary: '#0A84FF',
      success: '#30D158',
      warning: '#FF9F0A',
      danger: '#FF453A',
      info: '#64D2FF',
      textPrimary: '#FFFFFF',
      textSecondary: '#98989D',
      textTertiary: '#68687A',
      backgroundPrimary: '#000000',
      backgroundSecondary: '#1C1C1E',
      backgroundTertiary: '#2C2C2E',
      borderColor: '#38383A',
      borderColorLight: '#48484A'
    }
  }
}

// 当前主题状态
const currentTheme = ref('light')
const isSystemTheme = ref(false)

// 检测系统主题偏好
const getSystemTheme = () => {
  if (typeof window !== 'undefined') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }
  return 'light'
}

// 计算属性
const theme = computed(() => THEMES[currentTheme.value])
const availableThemes = computed(() => Object.values(THEMES))

// 主题管理函数
const setTheme = (themeId) => {
  if (THEMES[themeId]) {
    currentTheme.value = themeId
    isSystemTheme.value = false
    applyTheme(themeId)
    saveThemePreference(themeId)
  }
}

const setSystemTheme = () => {
  isSystemTheme.value = true
  const systemTheme = getSystemTheme()
  currentTheme.value = systemTheme
  applyTheme(systemTheme)
  saveThemePreference('system')
}

const toggleTheme = () => {
  const themeKeys = Object.keys(THEMES)
  const currentIndex = themeKeys.indexOf(currentTheme.value)
  const nextIndex = (currentIndex + 1) % themeKeys.length
  setTheme(themeKeys[nextIndex])
}

// 应用主题
const applyTheme = (themeId) => {
  const themeConfig = THEMES[themeId]
  if (!themeConfig) return

  const root = document.documentElement
  
  // 移除所有主题类
  Object.values(THEMES).forEach(theme => {
    root.classList.remove(theme.class)
  })
  
  // 添加当前主题类
  root.classList.add(themeConfig.class)
  
  // 更新CSS变量
  Object.entries(themeConfig.colors).forEach(([key, value]) => {
    const cssVarName = key.replace(/([A-Z])/g, '-$1').toLowerCase()
    root.style.setProperty(`--${cssVarName}`, value)
  })
  
  // 更新主题特定的背景渐变
  updateBackgroundGradient(themeId)
}

// 更新背景渐变
const updateBackgroundGradient = (themeId) => {
  const root = document.documentElement
  
  const gradients = {
    light: {
      blur: `
        radial-gradient(circle at 30% 20%, rgba(121, 68, 154, 0.13), transparent 25%),
        radial-gradient(circle at 70% 65%, rgba(33, 150, 243, 0.13), transparent 25%),
        radial-gradient(circle at 20% 80%, rgba(234, 88, 12, 0.13), transparent 25%)
      `,
      main: `linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%)`
    },
    orange: {
      blur: `
        radial-gradient(circle at 30% 20%, rgba(255, 140, 0, 0.15), transparent 25%),
        radial-gradient(circle at 70% 65%, rgba(255, 165, 0, 0.15), transparent 25%),
        radial-gradient(circle at 20% 80%, rgba(255, 69, 0, 0.15), transparent 25%)
      `,
      main: `linear-gradient(135deg, rgba(255, 248, 240, 0.95) 0%, rgba(255, 243, 230, 0.85) 100%)`
    },
    dark: {
      blur: `
        radial-gradient(circle at 30% 20%, rgba(10, 132, 255, 0.15), transparent 25%),
        radial-gradient(circle at 70% 65%, rgba(48, 209, 88, 0.15), transparent 25%),
        radial-gradient(circle at 20% 80%, rgba(255, 69, 58, 0.15), transparent 25%)
      `,
      main: `linear-gradient(135deg, rgba(0, 0, 0, 0.95) 0%, rgba(28, 28, 30, 0.85) 100%)`
    }
  }
  
  const gradient = gradients[themeId]
  if (gradient) {
    root.style.setProperty('--bg-blur-gradient', gradient.blur)
    root.style.setProperty('--bg-main-gradient', gradient.main)
  }
}

// 保存主题偏好
const saveThemePreference = (themeId) => {
  try {
    localStorage.setItem('theme-preference', themeId)
  } catch (error) {
    console.warn('无法保存主题偏好:', error)
  }
}

// 加载主题偏好
const loadThemePreference = () => {
  try {
    const saved = localStorage.getItem('theme-preference')
    if (saved === 'system') {
      setSystemTheme()
    } else if (saved && THEMES[saved]) {
      setTheme(saved)
    } else {
      // 默认跟随系统
      setSystemTheme()
    }
  } catch (error) {
    console.warn('无法加载主题偏好:', error)
    setTheme('light')
  }
}

// 监听系统主题变化
const setupSystemThemeListener = () => {
  if (typeof window !== 'undefined') {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (e) => {
      if (isSystemTheme.value) {
        const systemTheme = e.matches ? 'dark' : 'light'
        currentTheme.value = systemTheme
        applyTheme(systemTheme)
      }
    }
    
    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }
}

// 使用主题 Hook
export function useTheme() {
  // 初始化
  onMounted(() => {
    loadThemePreference()
    setupSystemThemeListener()
  })
  
  return {
    // 状态
    currentTheme: computed(() => currentTheme.value),
    theme,
    availableThemes,
    isSystemTheme: computed(() => isSystemTheme.value),
    
    // 方法
    setTheme,
    setSystemTheme,
    toggleTheme,
    
    // 主题配置
    THEMES
  }
}