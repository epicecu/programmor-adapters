import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import AddAdapterView from '@/views/AddAdapterView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
    {
        path: '',
        component: HomeView,
    },
    {
        path: '/adapter/add',
        component: AddAdapterView
    }
    ]
})

export default router
