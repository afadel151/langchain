

// shared/types.ts - Updated to match your database schema

export interface Step {
    name: string;
    result: Record<string, any>;
}

export interface ToolUsed {
    name: string;
    args: Record<string, any>;
    output: string;
}

export interface ChatResponse {
    answer: string;
    tools_used: ToolUsed[];
    steps: Step[];
}

export interface QAPair {
    question: string;
    response: {
        answer: string;
        tools_used: Array<{
            name: string;
            args: Record<string, any>;
            output: string;
        }>;
        steps: Array<{
            name: string;
            result: Record<string, any>;
        }>;
    };
}

export interface Conversation {
    _id: string;
    title: string;
    messages: QAPair[];
    created_at: Date;
    updated_at: Date;
}

// If you want to keep backward compatibility, you can create an adapter
export interface ChatOutput {
    question: string;
    result?: {
        answer: string;
        tools_used: string[]; // Just tool names for display
    };
    steps: Step[];
}

// Utility function to convert QAPair to ChatOutput format
