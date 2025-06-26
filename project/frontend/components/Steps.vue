<script setup lang="ts">
import type { Step } from '~/shared/types';
const props = defineProps<{
    steps: Step[];
    done: boolean;
}>();

const hidden = ref(false);
const done = ref(props.done);
watch(done, async (newValue) => {
    if (newValue) {
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
            <div class="pt-2 flex flex-col items-center shrink-0">
                <span class="inline-block w-3 h-3 transition-colors rounded-full"
                    :class="!done ? 'animate-pulse bg-emerald-400' : 'bg-gray-500'"></span>

                <div class="w-[1px] grow border-l border-gray-700"></div>

            </div>
        </div>
        <div class="space-y-2.5">
            <div v-for="(step, i) in steps" :key="i">
                <p>{{ step.name }}</p>
                <div class="flex flex-wrap items-center gap-1 mt-1">
                    <p v-for="(result, j) in Object.entries(step.result)" :key="j"
                        class="text-xs px-1.5 py-0.5 bg-gray-800 rounded text-white">

                        {{ j }} : {{ result }}
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>