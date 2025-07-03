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
    <div
        class="border border-gray-300 dark:border-gray-700 rounded-xl mt-5 p-4 flex flex-col bg-white dark:bg-[#1E1E1E] shadow-sm">
        <Button
            class="w-full text-left flex items-center justify-between font-medium text-sm    rounded-lg px-2 py-2 "
            @click="hidden = !hidden">
            Steps
            <ChevronDown v-if="hidden" />
            <ChevronUp v-else />
        </Button>
        <transition name="fade">
            <div v-if="!hidden" class="flex gap-2 mt-4">
                <div class="pt-2 flex flex-col items-center shrink-0">
                    <span class="inline-block w-3 h-3 transition-colors rounded-full"
                        :class="!done ? 'animate-pulse bg-emerald-400' : 'bg-gray-500'"></span>
                    <div class="w-[1px] grow border-l border-gray-300 dark:border-gray-700"></div>
                </div>
                <div class="space-y-3 w-full">
                    <div v-for="(step, i) in steps" :key="i" class="bg-gray-50 dark:bg-gray-900 p-3 rounded-lg">
                        <p class="text-sm font-semibold text-gray-800 dark:text-gray-100">{{ step.name }}</p>
                        <div class="flex flex-wrap items-center gap-2 mt-2">
                            
                            <p v-for="(result, j) in Object.entries(step.result)" :key="j"
                                class="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-800 text-gray-900 dark:text-white rounded-md">
                                {{ result[0] }} : {{ result[1] }}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    </div>

</template>