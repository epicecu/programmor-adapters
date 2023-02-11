<script setup lang="ts">
  import AdapterView from './views/AdapterListView.vue'
  import DeviceView from './views/DeviceListView.vue'
</script>

<template>
  <div class="app-inner container-fluid min-100 d-flex flex-column">
    <nav class="navbar navbar-expand bg-light flex-shrink-0 app-header">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">
          <img alt="Programmor Adapter HMI Test App"  src="@/assets/epicecu-programmor-logo.png" height="55">
        </a>

        <div class="collapse navbar-collapse">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <a class="nav-link disabled" href="https://epicecu.com">EpicECU</a>
            </li>
            <li class="nav-item">
              <a class="nav-link disabled" href="https://programmor.com">Programmor</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <nav class="navbar navbar-expand bg-dark flex-shrink-0">
      <div class="collapse navbar-collapse">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <a class="nav-link text-light" href="#">Connect</a>
          </li>
        </ul>
      </div>
    </nav>

    <div class="row no-margin flex-grow-1">
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

  </div>
</template>

<style scoped>
  .app-inner{
    padding-left: 0;
    padding-right: 0;
  }
  .app-body{
    /* background-color: rgb(231, 231, 231); */
  }
  .min-100 {
    min-height: 100%;
  }
  .no-padding{
    padding: 0;
  }
  .no-margin{
    margin: 0;
  }
</style>
