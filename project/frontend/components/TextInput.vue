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
  console.log("Submitting message:", text.value);

  if (messages.value?.length == 0) {
    let generated_title: string | undefined = ""
    try {
      console.log('Generating title ....');

      const result = await model.generateContent(`Return one conversation title (maximum of 4 words) from the following text: "${text.value}" . don't use markdown return in txt format`);
      const response = result.response;

      generated_title = response.text();
      console.log('Generated Title : ', generated_title);
      try {
        const res = await fetch("http://127.0.0.1:8000/create_conversation", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ title: generated_title || "New Conversation" }),
        });
        const data = await res.json();  // ⬅️ THIS reads the body
        conversation_id.value = data.conversation_id;
        emit("send_message",text.value,conversation_id)
        text.value = "";
      } catch (error) {
        console.log("Error creating conversation:", error);
      }
    } catch (error) {
      console.log("Error creating conversation:", error);
    }

  } else {
    emit("send_message",text.value)
  }
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

// When component is mounted
onMounted(() => {
  window.addEventListener("resize", handleResize);
  adjustHeight(); // Optionally call once on mount
});

// Clean up when component is destroyed
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
