    <script setup lang="ts">
    import type { ChatOutput } from "@/shared/types";
    const props = defineProps<{
        output: ChatOutput;
    }>();
    const detailsHidden = !!props.output.result?.answer;
    import Steps from "./Steps.vue";

    import MarkdownRenderer from "./MarkdownRenderer.vue";
    </script>

    <template>
        <div className="border-t border-gray-700 py-10 first-of-type:pt-0 first-of-type:border-t-0">
            <p className="text-3xl">{{ output.question }}</p>
            <Steps v-if="output.steps.length > 0" :steps="output.steps" :done="detailsHidden" />

            <div class="mt-5 prose dark:prose-invert min-w-full prose-pre:whitespace-pre-wrap">
                <MarkdownRenderer :source="output.result?.answer" />
            </div>
            <div v-if="output.result?.tools_used?.length > 0" class="flex items-baseline mt-5 gap-1"> 
                <p class="text-xs text-gray-500">Tools used:</p>
                <div class="flex flex-wrap items-center gap-1">
                    <p v-for="(tool, i) in output.result.tools_used" :key="i" class="text-xs px-1 py-[1px] bg-gray-800 rounded text-white">
                        {{ tool }}
                    </p>
                </div>
            </div>
        </div>
    </template>