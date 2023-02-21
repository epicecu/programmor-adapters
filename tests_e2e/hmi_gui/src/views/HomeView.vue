<script setup lang="ts">
  import AdapterView from '@/views/AdapterListView.vue'
  import DeviceView from '@/views/DeviceListView.vue'
  import ActionbarComponent from '@/views/ActionBarComponent.vue'
</script>

<template>
<actionbar-component>
<li class="nav-item">
    <span class="nav-link text-light">Connect to Adapter</span>
</li>
</actionbar-component>
<div class="row no-margin no-padding flex-grow-1 bg-light">
    <div class="col-2 border-end no-padding">
        <AdapterView />
    </div>
    <div class="col-2 border-end no-padding">
        <DeviceView />
    </div>
    <div class="col-8 no-padding">
        <div class="no-margin">
        <main>
            <p>Common1</p>
            <div class="mb-3 row no-margin">
            <label for="common1_id" class="col-sm-3 col-form-label">Id</label>
            <div class="col-sm-9">
                <input type="text" class="form-control-plaintext" id="common1_id" value="123">
            </div>
            </div>
            <div class="mb-3 row no-margin">
            <label for="common1_registory_id" class="col-sm-3 col-form-label">Registory Id</label>
            <div class="col-sm-9">
                <input type="text" class="form-control-plaintext" id="common1_registory_id" value="123">
            </div>
            </div>
            <div class="mb-3 row no-margin">
            <label for="common1_serial_number" class="col-sm-3 col-form-label">Serial Number</label>
            <div class="col-sm-9">
                <input type="text" class="form-control-plaintext" id="common1_serial_number" value="87151548">
            </div>
            </div>
            <div class="mb-3 row no-margin">
            <label for="common1_shares_version" class="col-sm-3 col-form-label">Shares Version</label>
            <div class="col-sm-9">
                <input type="text" class="form-control-plaintext" id="common1_shares_version" value="1">
            </div>
            </div>
            <div class="mb-3 row no-margin">
            <label for="common1_firmware_version" class="col-sm-3 col-form-label">Firmware Version</label>
            <div class="col-sm-9">
                <input type="text" class="form-control-plaintext" id="common1_firmware_version" value="202301">
            </div>
            </div>
            <div class="mb-3 row no-margin">
            <label for="common1_device_name" class="col-sm-3 col-form-label">Device Name</label>
            <div class="col-sm-9">
                <input type="text" class="form-control-plaintext" id="common1_device_name" value="testdev_a_1">
            </div>
            </div>
        </main>
        </div>
    </div>
</div>
</template>

<style scoped>
</style>
