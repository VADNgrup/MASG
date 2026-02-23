<template>
  <div class="slidev-layout h-full flex flex-col">
    <!-- Title -->
    <div class="mb-6">
      <slot name="title" />
    </div>

    <!-- Content -->
    <div class="flex-1 grid grid-cols-2 gap-10">
      <!-- Left -->
      <div>
        <slot name="left" />
      </div>
      <!-- Right -->
      <div class="grid grid-rows-2 gap-2">
        <div class="mx-auto" style="width: 70%; height: 60%;">
          <div class="table-container flex items-center justify-center h-full">
            <slot name="right-top" />
          </div>
        </div>
        <div class="mx-auto" style="width: 70%; height: 60%;">
          <div class="table-container flex items-center justify-center h-full">
            <slot name="right-bottom" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.table-container {
  container-type: inline-size;
}

/* Auto-scale tables to fit container */
.table-container :deep(table) {
  width: 100%;
  max-width: 100%;
  font-size: clamp(0.5rem, 2.5cqw, 1rem);
  border-collapse: collapse;
}

.table-container :deep(th),
.table-container :deep(td) {
  padding: clamp(0.2rem, 1cqw, 0.5rem);
  text-align: left;
  border: 1px solid #ddd;
}

.table-container :deep(th) {
  font-weight: 600;
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
