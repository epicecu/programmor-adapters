import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from '@/router/index'

import './assets/main.css'

const app = createApp(App)

app.use(router)
app.use(createPinia())

app.mount('#app')

// Import the default adapters
import { useHmiStore } from '@/stores/hmi'
import type { AdapterInfo } from '@/stores/hmi'
import defaults from '@/hmi.json'
const store = useHmiStore()
defaults.hmi.adapters.forEach((defaultAdapter) => {
    const adapter: AdapterInfo = {} as AdapterInfo;
    adapter.adapterId = defaultAdapter.adapterId;
    adapter.adapterName = defaultAdapter.adapterName;
    adapter.ipAddress = defaultAdapter.ipAddress;
    adapter.portNumber = defaultAdapter.portNumber;
    adapter.connected = defaultAdapter.connected;
    store.addAdapter(adapter);
});