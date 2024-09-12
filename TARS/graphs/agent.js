const { loadTools, createToolCallingAgent, AgentExecutor } = require('langchain/agents');
const { ChatPromptTemplate, MessagesPlaceholder } = require('langchain/prompts');
const { AIMessage, HumanMessage } = require('langchain_core/messages');
const { YahooFinanceNewsTool, YouTubeSearchTool } = require('langchain/tools');
const { SlackToolkit } = require('langchain/agents/agent_toolkits');
const { getWordLength, handleAllUnreadGmail, fetchEmailsBySenderName, readImageTool, fetchDmsLastXHours, fetchCalendarEventsForXDays } = require('./custom_tools');
const { openaiLlm } = require('../models/generic_llms/openai');
const { googleLlm } = require('../models/generic_llms/google_ai');
const { anthropicLlm } = require('../models/generic_llms/anthropic');
const { llmSettings } = require('../config/config');

class AgentManager {
    constructor() {
        this.llm = this.initializeLlm();
        this.tools = this.loadAllTools();
        this.llmWithTools = this.llm.bindTools(this.tools);
        this.prompt = this.definePrompt();
        this.agent = createToolCallingAgent(this.llm, this.tools, this.prompt);
        this.agentExecutor = new AgentExecutor({ agent: this.agent, tools: this.tools, verbose: true });
    }

    initializeLlm() {
        const llmType = llmSettings.llmType;
        switch (llmType) {
            case 'openai':
                return openaiLlm;
            case 'google':
                return googleLlm;
            case 'anthropic':
                return anthropicLlm;
            default:
                throw new Error(`Unsupported LLM type: ${llmType}`);
        }
    }

    loadAllTools() {
        const customTools = [getWordLength, handleAllUnreadGmail, readImageTool, fetchDmsLastXHours, fetchCalendarEventsForXDays, fetchEmailsBySenderName];
        const requestTools = loadTools(["requests_all"]);
        const weatherTools = loadTools(["openweathermap-api"]);
        const financeTools = [new YahooFinanceNewsTool()];
        const slackTools = new SlackToolkit().getTools();
        const youtubeTools = [new YouTubeSearchTool()];
        return [...customTools, ...requestTools, ...weatherTools, ...financeTools, ...slackTools, ...youtubeTools];
    }

    definePrompt() {
        return new ChatPromptTemplate({
            messages: [
                { role: "system", content: "You are a helpful AI assistant named TARS. You have a geeky, clever, sarcastic, and edgy sense of humor. You were created by GP to help me be more efficient." },
                new MessagesPlaceholder({ variableName: "chat_history" }),
                { role: "user", content: "{input}" },
                new MessagesPlaceholder({ variableName: "agent_scratchpad" }),
            ]
        });
    }

    async processUserTask(userTask, chatHistory = []) {
        if (!userTask) {
            throw new Error("user_task cannot be None");
        }
        try {
            const invokeParams = { input: userTask, chat_history: chatHistory };
            const result = await this.agentExecutor.invoke(invokeParams);
            chatHistory.push(new HumanMessage({ content: userTask }), new AIMessage({ content: result.output }));
            return result.output;
        } catch (error) {
            console.error(`Error in processUserTask: ${error}`);
            return "An error occurred while processing the task.";
        }
    }
}

module.exports = AgentManager;
