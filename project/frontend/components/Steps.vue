<script setup lang="ts">
import type { Step } from '~/shared/types';
const props = defineProps<{
  steps: Step[];
  done: boolean;
}>();

const hidden = ref(false);
const done = ref(props.done);
watch(done,async (newValue) => {
    if(newValue) {
        hidden.value = true;
    }
});
import { ChevronDown, ChevronUp } from 'lucide-vue-next';
</script>

<template>
    <div class="border border-gray-700 rounded mt-5 p-3 flex flex-col">
        <Button class="w-full text-left flex items-center justify-between" onclick="hidden = !hidden">
           Steps  
           <ChevronDown v-if="hidden" />
            <ChevronUp v-else />
        </Button>
        <div v-if="!hidden" class="flex gap-2 mt-2">
            
        </div>
    </div>
</template>