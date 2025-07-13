import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './assets/styles/global.css'

const app = createApp(App)


app.use(router)
app.mount('#app')

// 添加全局路由错误处理
router.onError((error) => {
  console.error('路由错误:', error)
})
