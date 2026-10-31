import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuth } from './stores/auth'
import './styles.css'

const app = createApp(App)
app.use(createPinia())
const auth = useAuth()
auth.init().finally(() => {
  app.use(router)
  app.mount('#app')
})
