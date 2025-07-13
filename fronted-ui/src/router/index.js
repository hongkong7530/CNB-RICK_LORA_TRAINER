import { createRouter, createWebHistory } from 'vue-router'
import Assets from '../views/Assets.vue'
import Tasks from '../views/Tasks.vue'
import TaskDetail from '../views/TaskDetail.vue'
import Settings from '../views/Settings.vue'
import Guide from '../views/Guide.vue'

/**
 * @typedef {Object} RouteConfig
 * @property {string} path - 路由路径
 * @property {string} name - 路由名称
 * @property {Object} meta - 路由元信息
 * @property {string} meta.title - 页面标题
 * @property {boolean} meta.requiresAuth - 是否需要认证
 * @property {import('vue').Component} component - 路由组件
 */

/** @type {RouteConfig[]} */
export const routes = [
  {
    path: '/',
    redirect: '/assets'
  },
  {
    path: '/assets',
    name: 'Assets',
    component: Assets,
    meta: {
      title: '资产管理',
      requiresAuth: true
    }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: Tasks,
    meta: {
      title: '任务管理',
      requiresAuth: true
    },
    children: [
      {
        path: ':id',
        name: 'TaskDetail',
        component: TaskDetail,
        meta: {
          title: '任务详情',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: {
      title: '系统设置',
      requiresAuth: true
    },
    children: [
      {
        path: '',
        redirect: '/settings/system'
      },
      {
        path: 'system',
        name: 'SystemSettings',
        meta: {
          title: '系统配置',
          tab: 'system',
          requiresAuth: true
        }
      },
      {
        path: 'mark',
        name: 'MarkSettings',
        meta: {
          title: '标记配置',
          tab: 'mark',
          requiresAuth: true
        }
      },
      {
        path: 'ai',
        name: 'AISettings',
        meta: {
          title: 'AI引擎配置',
          tab: 'ai',
          requiresAuth: true
        }
      },
      {
        path: 'translate',
        name: 'TranslateSettings',
        meta: {
          title: '翻译配置',
          tab: 'translate',
          requiresAuth: true
        }
      },
      {
        path: 'lora',
        name: 'LoraSettings',
        meta: {
          title: 'Lora训练配置',
          tab: 'lora',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/guide',
    name: 'Guide',
    component: Guide,
    meta: {
      title: '使用指南与常见问题',
      requiresAuth: true
    }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - RLT`
  }
  
  // TODO: 添加实际的权限验证逻辑
  if (to.meta.requiresAuth) {
    // const isAuthenticated = checkAuth()
    // if (!isAuthenticated) {
    //   next('/login')
    //   return
    // }
  }
  
  next()
})

export default router 