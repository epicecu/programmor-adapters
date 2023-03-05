<script setup lang="ts">
  import AdapterView from '@/views/AdapterView.vue'
  import DeviceView from '@/views/DeviceView.vue'
  import DetailedView from '@/views/DetailedView.vue'
  import ActionbarComponent from '@/views/ActionBarComponent.vue'
</script>

<template>
<actionbar-component>
<li class="nav-item">
    <span class="nav-link text-light">File</span>
</li>
<li class="nav-item">
    <span class="nav-link text-light">Undo</span>
</li>
<li class="nav-item">
    <span class="nav-link text-light">Redo</span>
</li>
<li class="nav-item">
    <span class="nav-link text-light">Help</span>
</li>
</actionbar-component>
<div class="row m-0 p-0 h-100 flex-grow-1 bg-light">
    <div class="col-2 border-end p-0">
        <AdapterView />
    </div>
    <div class="col-2 border-end p-0">
        <DeviceView />
    </div>
    <div class="col-8 p-0 h-100">
        <DetailedView />
    </div>
</div>
</template>

<style scoped>
</style>
