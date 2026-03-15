import React, { useState, useRef, useEffect } from "react";
import {
    Send,
    Bot,
    User,
    Database,
    Filter,
    AlertCircle,
    BarChart3,
    Package,
    ShoppingCart,
} from "lucide-react";

export default function App() {
    const [messages, setMessages] = useState([
        {
            role: "ai",
            type: "text",
            content:
                'Hello! I am your Governed Enterprise Data Assistant. Ask me a question about our sales orders, revenue, or quantities. For example: "What is our revenue for GB01?" or "Show me sales in GBP."',
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    // Auto-scroll to bottom of chat
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage = input.trim();
        setInput("");
        setMessages((prev) => [
            ...prev,
            { role: "user", type: "text", content: userMessage },
        ]);
        setIsLoading(true);

        try {
            // Connect to the local FastAPI Docker container
            const response = await fetch("http://localhost:8000/api/ask", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Accept: "application/json",
                },
                body: JSON.stringify({ question: userMessage }),
            });

            // Handle guardrail rejection (400) and other API errors gracefully
            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage =
                    errorData.detail ||
                    "Sorry, I encountered an error connecting to the Governed API. Please ensure the backend is running.";
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "ai",
                        type: "error",
                        content: errorMessage,
                    },
                ]);
                return;
            }

            const data = await response.json();

            // Add the structured AI response to the chat
            setMessages((prev) => [
                ...prev,
                {
                    role: "ai",
                    type: "data",
                    content: data,
                },
            ]);
        } catch (error) {
            // Network error - backend not reachable
            setMessages((prev) => [
                ...prev,
                {
                    role: "ai",
                    type: "error",
                    content:
                        "Sorry, I encountered an error connecting to the Governed API. Please ensure the backend is running.",
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    // Helper to format currency
    const formatCurrency = (amount, currencyCode) => {
        return new Intl.NumberFormat("en-GB", {
            style: "currency",
            currency: currencyCode || "GBP",
            maximumFractionDigits: 0,
        }).format(amount);
    };

    // Helper to format numbers
    const formatNumber = (num) => {
        return new Intl.NumberFormat("en-GB").format(num);
    };

    return (
        <div className="flex flex-col h-screen bg-slate-50 text-slate-800 font-sans">
            {/* Top Navigation Bar */}
            <header className="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between shadow-sm z-10">
                <div className="flex items-center gap-3">
                    <div className="bg-indigo-600 p-2 rounded-lg">
                        <Database className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-slate-900 leading-tight">
                            Governed AI Platform
                        </h1>
                        <p className="text-xs text-slate-500 font-medium">
                            Enterprise ERP Data securely routed via Vertex AI
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className="flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-emerald-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                    </span>
                    <span className="text-sm font-medium text-slate-600">
                        System Online
                    </span>
                </div>
            </header>

            {/* Chat Area */}
            <main className="flex-1 overflow-y-auto p-4 sm:p-6 w-full max-w-5xl mx-auto">
                <div className="flex flex-col gap-6">
                    {messages.map((msg, index) => (
                        <div
                            key={index}
                            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                        >
                            <div
                                className={`flex gap-4 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                            >
                                {/* Avatar */}
                                <div className="flex-shrink-0 mt-1">
                                    {msg.role === "user" ? (
                                        <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center border border-indigo-200">
                                            <User className="w-5 h-5 text-indigo-700" />
                                        </div>
                                    ) : (
                                        <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center border border-emerald-200 shadow-sm">
                                            <Bot className="w-5 h-5 text-emerald-700" />
                                        </div>
                                    )}
                                </div>

                                {/* Message Content */}
                                <div>
                                    {msg.type === "text" && (
                                        <div
                                            className={`p-4 rounded-2xl shadow-sm text-sm sm:text-base ${
                                                msg.role === "user"
                                                    ? "bg-indigo-600 text-white rounded-tr-none"
                                                    : "bg-white border border-slate-200 text-slate-700 rounded-tl-none"
                                            }`}
                                        >
                                            {msg.content}
                                        </div>
                                    )}

                                    {msg.type === "error" && (
                                        <div className="p-4 rounded-2xl bg-red-50 border border-red-100 text-red-700 rounded-tl-none shadow-sm flex items-start gap-3">
                                            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                                            <p className="text-sm">
                                                {msg.content}
                                            </p>
                                        </div>
                                    )}

                                    {/* Structured Data Dashboard Card */}
                                    {msg.type === "data" && (
                                        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none shadow-sm overflow-hidden w-full max-w-3xl">
                                            {/* AI Reasoning / Routing Header */}
                                            <div className="bg-slate-50 border-b border-slate-100 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                                <div className="flex items-center gap-2 text-sm text-slate-600">
                                                    <Bot className="w-4 h-4 text-emerald-600" />
                                                    <span className="font-medium text-slate-800">
                                                        Vertex AI Extracted
                                                        Intent
                                                    </span>
                                                </div>

                                                {/* Filter Badges */}
                                                <div className="flex flex-wrap gap-2">
                                                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-slate-200 text-xs font-medium text-slate-600 shadow-sm">
                                                        <Filter className="w-3 h-3 text-indigo-500" />
                                                        Org:{" "}
                                                        <span className="text-indigo-700">
                                                            {msg.content
                                                                .extracted_parameters
                                                                .sales_org ||
                                                                "ALL"}
                                                        </span>
                                                    </div>
                                                    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-white border border-slate-200 text-xs font-medium text-slate-600 shadow-sm">
                                                        <Filter className="w-3 h-3 text-indigo-500" />
                                                        Currency:{" "}
                                                        <span className="text-indigo-700">
                                                            {msg.content
                                                                .extracted_parameters
                                                                .currency ||
                                                                "ALL"}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>

                                            {/* KPI Dashboard Grid */}
                                            <div className="p-5 grid grid-cols-1 sm:grid-cols-3 gap-4">
                                                {/* Revenue Card */}
                                                <div className="bg-gradient-to-br from-indigo-50 to-white p-4 rounded-xl border border-indigo-100">
                                                    <div className="flex items-center gap-2 mb-2 text-indigo-800">
                                                        <BarChart3 className="w-4 h-4" />
                                                        <h3 className="text-sm font-semibold">
                                                            Total Revenue
                                                        </h3>
                                                    </div>
                                                    <p className="text-2xl font-bold text-slate-900">
                                                        {formatCurrency(
                                                            msg.content.data
                                                                .total_revenue,
                                                            msg.content
                                                                .extracted_parameters
                                                                .currency,
                                                        )}
                                                    </p>
                                                </div>

                                                {/* Orders Card */}
                                                <div className="bg-gradient-to-br from-emerald-50 to-white p-4 rounded-xl border border-emerald-100">
                                                    <div className="flex items-center gap-2 mb-2 text-emerald-800">
                                                        <ShoppingCart className="w-4 h-4" />
                                                        <h3 className="text-sm font-semibold">
                                                            Total Orders
                                                        </h3>
                                                    </div>
                                                    <p className="text-2xl font-bold text-slate-900">
                                                        {formatNumber(
                                                            msg.content.data
                                                                .total_orders,
                                                        )}
                                                    </p>
                                                </div>

                                                {/* Items Sold Card */}
                                                <div className="bg-gradient-to-br from-sky-50 to-white p-4 rounded-xl border border-sky-100">
                                                    <div className="flex items-center gap-2 mb-2 text-sky-800">
                                                        <Package className="w-4 h-4" />
                                                        <h3 className="text-sm font-semibold">
                                                            Items Sold
                                                        </h3>
                                                    </div>
                                                    <p className="text-2xl font-bold text-slate-900">
                                                        {formatNumber(
                                                            msg.content.data
                                                                .total_items_sold,
                                                        )}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Footer text */}
                                            <div className="bg-slate-50 p-3 text-xs text-slate-400 text-right border-t border-slate-100">
                                                Governed by dbt constraints •
                                                Direct BigQuery fetch
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Loading Indicator */}
                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="flex gap-4">
                                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center border border-emerald-200 mt-1">
                                    <Bot className="w-5 h-5 text-emerald-700" />
                                </div>
                                <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm rounded-tl-none flex items-center gap-2">
                                    <div className="flex space-x-1.5">
                                        <div
                                            className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"
                                            style={{ animationDelay: "0ms" }}
                                        ></div>
                                        <div
                                            className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"
                                            style={{ animationDelay: "150ms" }}
                                        ></div>
                                        <div
                                            className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"
                                            style={{ animationDelay: "300ms" }}
                                        ></div>
                                    </div>
                                    <span className="text-sm text-slate-500 ml-2 font-medium">
                                        Routing intent and querying ERP data...
                                    </span>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </main>

            {/* Input Area */}
            <footer className="bg-white border-t border-slate-200 p-4 w-full">
                <div className="max-w-4xl mx-auto relative">
                    <form
                        onSubmit={handleSubmit}
                        className="relative flex items-center"
                    >
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask about revenue, orders, or items (e.g., 'What is our revenue in GBP?')"
                            disabled={isLoading}
                            className="w-full pl-5 pr-14 py-4 bg-slate-50 border border-slate-300 rounded-full text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow disabled:opacity-60 shadow-inner"
                        />
                        <button
                            type="submit"
                            disabled={isLoading || !input.trim()}
                            className="absolute right-2 p-2.5 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors shadow-sm"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </form>
                    <div className="text-center mt-3">
                        <p className="text-xs text-slate-400">
                            AI answers are derived directly from governed
                            BigQuery models. No SQL generated.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
}
