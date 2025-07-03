<script setup lang="ts">
import type { Conversation } from "@/shared/types";
const isGenerating = ref(false);
const text = ref("");
import { GoogleGenerativeAI } from "@google/generative-ai";
const config = useRuntimeConfig();
const apiKey = config.public.GOOGLE_API_KEY;
if (!apiKey) {
  throw new Error("GOOGLE_API_KEY environment variable is not defined");
}
const configuration = new GoogleGenerativeAI(apiKey);
const model = configuration.getGenerativeModel({ model: "gemini-2.0-flash" });
const textAreaRef = ref<HTMLTextAreaElement | null>(null);


const conversation_id = ref<string>("");
const props = defineProps<{
  conversation: Conversation | null
}>()

const messages = ref(props.conversation?.messages)
const emit = defineEmits(["send_message"]);
async function submit(e: any) {
  e.preventDefault();
  emit("send_message",text.value)
  text.value = ''
}
function submitOnEnter(event: any) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    submit(event);
  }
}
const adjustHeight = () => {
  nextTick(() => {
    const textArea = textAreaRef.value;
    if (textArea) {
      textArea.style.height = "auto";
      textArea.style.height = `${textArea.scrollHeight}px`;
    }
  });
};

watch(text, (newValue) => {
  if (textAreaRef.value) {
    adjustHeight();
  }
});
function handleResize() {
  adjustHeight();
}
onMounted(() => {
  window.addEventListener("resize", handleResize);
  adjustHeight(); 
});
// Clean up 
onBeforeUnmount(() => {
  window.removeEventListener("resize", handleResize);
});
import { ArrowRight } from "lucide-vue-next";
</script>

<template>
  <form @submit.prevent="submit" class="flex gap-3 z-0" :class="(messages ?? []).length > 0
    ? 'fixed bottom-0 left-0 right-0 bg-white p-4 shadow-lg'
    : ''
    ">
    <div class="w-full relative flex z-0 p-3 items-center  bg-gray-100 rounded-4xl  border border-gray-200">
      <textarea v-model="text" ref="textAreaRef" @keydown.enter.prevent="submitOnEnter" @input="adjustHeight"
        class="w-full text-gray-800 z-0  p-3 bg-transparent min-h-24 focus:outline-none focus-visible:ring-0 focus-visible:ring-ring/50 resize-none"
        placeholder="Type your message here...">
      </textarea>
      <Button type="submit" :disabled="isGenerating || !text"
        class="  absolute right-5 w-fit p-5  rounded-full hover:translate-x-1 hover:bg-gray-500 z-10">
        <ArrowRight />
      </Button>
    </div>
  </form>
</template>
