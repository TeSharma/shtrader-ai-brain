import { createFileRoute } from "@tanstack/react-router";
import {
  Activity,
  BarChart3,
  BookOpen,
  Bot,
  ChevronDown,
  CircleHelp,
  Clock3,
  Gauge,
  Menu,
  MessageSquare,
  Moon,
  PanelLeft,
  Plus,
  Send,
  Settings,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingDown,
  TrendingUp,
  User,
  Wallet,
  X,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  LocalAgentOfflineError,
  getHealth,
  sendMessage as sendToEngine,
} from "../lib/la/client";

export const Route = createFileRoute("/")({
  component: Index,
});

type Message = {
  role: "user" | "assistant";
  content: string;
};

function Index() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [engineError, setEngineError] = useState<string | null>(null);
  // "checking" | "online" | "offline"
  const [engineStatus, setEngineStatus] = useState<"checking" | "online" | "offline">(
    "checking",
  );

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then(() => {
        if (!cancelled) setEngineStatus("online");
      })
      .catch(() => {
        if (!cancelled) setEngineStatus("offline");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Welcome to Shtrader LA. I can analyse trade setups, calculate risk, size positions, build trading plans, and explain trading concepts using the local intelligence layer.",
    },
  ]);

  const sendMessage = async () => {
    const text = input.trim();

    if (!text || isThinking) return;

    setMessages((current) => [...current, { role: "user", content: text }]);
    setInput("");
    setIsThinking(true);
    setEngineError(null);

    try {
      const response = await sendToEngine(text, "web-console");
      const answer = response.disclaimer
        ? `${response.answer}\n\n${response.disclaimer}`
        : response.answer;
      setMessages((current) => [
        ...current,
        { role: "assistant", content: answer },
      ]);
    } catch (error) {
      const message =
        error instanceof LocalAgentOfflineError
          ? error.message
          : "Something went wrong while contacting the Shtrader LA engine.";
      setEngineError(message);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: message },
      ]);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#080a0f] text-[#f4f6f8]">
      <div className="flex min-h-screen">
        {/* SIDEBAR */}
        <aside
          className={`${
            sidebarOpen ? "w-[250px]" : "w-[72px]"
          } hidden shrink-0 border-r border-white/[0.07] bg-[#0b0e14] transition-all duration-200 lg:flex lg:flex-col`}
        >
          {/* Brand */}
          <div className="flex h-[72px] items-center border-b border-white/[0.07] px-5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04]">
                <Sparkles size={18} className="text-[#d7ff5f]" />
              </div>

              {sidebarOpen && (
                <div>
                  <div className="text-[15px] font-semibold tracking-tight">
                    Shtrader
                  </div>
                  <div className="text-[10px] font-medium uppercase tracking-[0.2em] text-[#7d8592]">
                    LA Console
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Navigation */}
          <div className="flex-1 px-3 py-5">
            {sidebarOpen && (
              <div className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#606875]">
                Workspace
              </div>
            )}

            <nav className="space-y-1">
              <NavItem
                icon={<MessageSquare size={17} />}
                label="AI Assistant"
                active
                collapsed={!sidebarOpen}
              />

              <NavItem
                icon={<BarChart3 size={17} />}
                label="Trade Analysis"
                collapsed={!sidebarOpen}
              />

              <NavItem
                icon={<Gauge size={17} />}
                label="Risk & Position"
                collapsed={!sidebarOpen}
              />

              <NavItem
                icon={<BookOpen size={17} />}
                label="Knowledge"
                collapsed={!sidebarOpen}
              />
            </nav>

            {sidebarOpen && (
              <div className="mb-3 mt-8 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-[#606875]">
                System
              </div>
            )}

            <nav className="space-y-1">
              <NavItem
                icon={<Activity size={17} />}
                label="System Status"
                collapsed={!sidebarOpen}
              />

              <NavItem
                icon={<Settings size={17} />}
                label="Settings"
                collapsed={!sidebarOpen}
              />
            </nav>
          </div>

          {/* Model status */}
          {sidebarOpen && (
            <div className="border-t border-white/[0.07] p-4">
              <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      engineStatus === "online"
                        ? "bg-[#d7ff5f] shadow-[0_0_10px_rgba(215,255,95,0.7)]"
                        : engineStatus === "checking"
                          ? "bg-[#8b929e]"
                          : "bg-[#d47a7a]"
                    }`}
                  />
                  <span className="text-xs font-medium">
                    {engineStatus === "online"
                      ? "Engine ready"
                      : engineStatus === "checking"
                        ? "Checking engine…"
                        : "Engine offline"}
                  </span>
                </div>

                <div className="mt-2 text-[11px] leading-relaxed text-[#717986]">
                  {engineStatus === "online" ? (
                    <>
                      Deterministic tools online
                      <br />
                      Local model awaiting weights
                    </>
                  ) : (
                    <>
                      Run <span className="text-[#a9c957]">npm run start:all</span>
                      <br />
                      to start the local API
                    </>
                  )}
                </div>
              </div>
            </div>
          )}
        </aside>

        {/* MAIN */}
        <main className="flex min-w-0 flex-1 flex-col">
          {/* TOP BAR */}
          <header className="flex h-[72px] shrink-0 items-center justify-between border-b border-white/[0.07] bg-[#0a0d12]/95 px-5 backdrop-blur">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setSidebarOpen((value) => !value)}
                className="hidden rounded-lg p-2 text-[#8b929e] transition hover:bg-white/[0.05] hover:text-white lg:block"
              >
                <PanelLeft size={18} />
              </button>

              <button className="rounded-lg p-2 text-[#8b929e] hover:bg-white/[0.05] lg:hidden">
                <Menu size={19} />
              </button>

              <div>
                <div className="text-sm font-medium">AI Trading Desk</div>
                <div className="mt-0.5 text-[11px] text-[#68707c]">
                  Local-first trading intelligence
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Engine badge */}
              <div className="hidden items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.025] px-3 py-1.5 sm:flex">
                <Bot size={13} className="text-[#d7ff5f]" />
                <span className="text-[11px] text-[#a7adb7]">
                  Shtrader Engine
                </span>
                <span className="h-1.5 w-1.5 rounded-full bg-[#d7ff5f]" />
              </div>

              <button className="rounded-lg p-2 text-[#7d8592] hover:bg-white/[0.05] hover:text-white">
                <Moon size={17} />
              </button>

              <button className="flex items-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.025] px-2.5 py-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#1b2029]">
                  <User size={13} />
                </div>

                <ChevronDown size={13} className="text-[#69717d]" />
              </button>
            </div>
          </header>

          {/* CONTENT */}
          <div className="flex min-h-0 flex-1 flex-col xl:flex-row">
            {/* CHAT WORKSPACE */}
            <section className="flex min-w-0 flex-1 flex-col">
              {/* Context bar */}
              <div className="flex items-center justify-between border-b border-white/[0.05] px-6 py-3">
                <div className="flex items-center gap-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#d7ff5f]/10">
                    <Zap size={14} className="text-[#d7ff5f]" />
                  </div>

                  <div>
                    <div className="text-xs font-medium">
                      Trading Intelligence
                    </div>
                    <div className="text-[10px] text-[#68707c]">
                      Risk-aware analysis
                    </div>
                  </div>
                </div>

                <button
                  onClick={() =>
                    setMessages([
                      {
                        role: "assistant",
                        content:
                          "New session started. What would you like to analyse?",
                      },
                    ])
                  }
                  className="flex items-center gap-1.5 rounded-lg border border-white/[0.08] px-2.5 py-1.5 text-[11px] text-[#8c94a0] transition hover:bg-white/[0.04] hover:text-white"
                >
                  <Plus size={13} />
                  New session
                </button>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-5 py-8 sm:px-8">
                <div className="mx-auto max-w-3xl">
                  <div className="mb-8">
                    <div className="mb-2 text-[11px] font-medium uppercase tracking-[0.16em] text-[#d7ff5f]">
                      Shtrader LA
                    </div>

                    <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                      What are we analysing today?
                    </h1>

                    <p className="mt-2 max-w-xl text-sm leading-relaxed text-[#737b87]">
                      Ask about a setup, calculate your risk, size a position,
                      build a trading plan, or learn a trading concept.
                    </p>

                    {engineStatus === "offline" && (
                      <div className="mt-5 rounded-lg border border-[#d47a7a]/25 bg-[#d47a7a]/[0.06] px-3 py-2.5 text-[11px] leading-relaxed text-[#e0a7a7]">
                        <span className="font-medium">Engine offline.</span>{" "}
                        Start the local agent with{" "}
                        <code className="rounded bg-black/20 px-1 py-0.5 font-mono text-[10px]">
                          npm run start:all
                        </code>{" "}
                        (boots the Python API + web console together), then
                        reload this page. No internet or model download is needed.
                      </div>
                    )}
                  </div>

                  <div className="space-y-5">
                    {messages.map((message, index) => (
                      <div
                        key={index}
                        className={`flex ${
                          message.role === "user"
                            ? "justify-end"
                            : "justify-start"
                        }`}
                      >
                        <div
                          className={`max-w-[85%] rounded-2xl px-4 py-3.5 text-sm leading-7 ${
                            message.role === "user"
                              ? "bg-[#d7ff5f] text-[#0b0e08]"
                              : "border border-white/[0.07] bg-[#10141b] text-[#c7ccd3]"
                          }`}
                        >
                          {message.content}
                        </div>
                      </div>
                    ))}

                    {isThinking && (
                      <div className="flex justify-start">
                        <div className="flex max-w-[85%] items-center gap-2 rounded-2xl border border-white/[0.07] bg-[#10141b] px-4 py-3.5 text-sm text-[#737b87]">
                          <span className="h-2 w-2 animate-pulse rounded-full bg-[#d7ff5f]" />
                          Analysing with the Shtrader LA engine…
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Suggested prompts */}
                  <div className="mt-8 grid gap-2 sm:grid-cols-2">
                    <PromptButton
                      icon={<Target size={15} />}
                      text="Analyse an XAUUSD setup"
                      onClick={() =>
                        setInput(
                          "Analyse this XAUUSD setup and explain the risk/reward."
                        )
                      }
                    />

                    <PromptButton
                      icon={<Gauge size={15} />}
                      text="Calculate position size"
                      onClick={() =>
                        setInput(
                          "Calculate my position size for EUR/USD with a $5,000 account, 2% risk and 50 pip stop."
                        )
                      }
                    />

                    <PromptButton
                      icon={<ShieldCheck size={15} />}
                      text="Calculate my risk"
                      onClick={() =>
                        setInput(
                          "How much am I risking with a $5,000 account and 2% risk?"
                        )
                      }
                    />

                    <PromptButton
                      icon={<BookOpen size={15} />}
                      text="Explain risk/reward"
                      onClick={() =>
                        setInput("What is risk reward and why does it matter?")
                      }
                    />
                  </div>
                </div>
              </div>

              {/* INPUT */}
              <div className="border-t border-white/[0.07] bg-[#0a0d12] p-4 sm:p-5">
                <div className="mx-auto max-w-3xl">
                  {engineError && (
                    <div className="mb-3 rounded-lg border border-[#d47a7a]/25 bg-[#d47a7a]/[0.06] px-3 py-2.5 text-[11px] leading-relaxed text-[#e0a7a7]">
                      <span className="font-medium">Local agent offline.</span>{" "}
                      {engineError}
                    </div>
                  )}

                  <div className="rounded-2xl border border-white/[0.09] bg-[#10141b] p-2 shadow-2xl shadow-black/20">
                    <textarea
                      value={input}
                      onChange={(event) => setInput(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" && !event.shiftKey) {
                          event.preventDefault();
                          sendMessage();
                        }
                      }}
                      placeholder="Ask Shtrader LA anything about your trade..."
                      rows={2}
                      className="w-full resize-none bg-transparent px-3 py-2 text-sm text-white outline-none placeholder:text-[#555d68]"
                    />

                    <div className="flex items-center justify-between px-2 pb-1">
                      <div className="flex items-center gap-3 text-[10px] text-[#5e6672]">
                        <span className="flex items-center gap-1.5">
                          <ShieldCheck size={12} />
                          Deterministic calculations
                        </span>

                        <span className="hidden sm:flex items-center gap-1.5">
                          <BookOpen size={12} />
                          Offline knowledge
                        </span>
                      </div>

                      <button
                        onClick={sendMessage}
                        className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#d7ff5f] text-[#0b0e08] transition hover:bg-[#e0ff7a]"
                      >
                        <Send size={14} />
                      </button>
                    </div>
                  </div>

                  <div className="mt-2 text-center text-[10px] text-[#505762]">
                    
                  </div>
                </div>
              </div>
            </section>

            {/* RIGHT INTELLIGENCE PANEL */}
            <aside className="hidden w-[340px] shrink-0 border-l border-white/[0.07] bg-[#0b0e14] xl:block">
              <div className="border-b border-white/[0.07] px-5 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium">Trade Intelligence</div>
                    <div className="mt-1 text-[10px] text-[#68707c]">
                      Live workspace context
                    </div>
                  </div>

                  <Activity size={16} className="text-[#68707c]" />
                </div>
              </div>

              <div className="space-y-4 p-5">
                <StatusCard />

                <div className="rounded-xl border border-white/[0.07] bg-[#10141b] p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <div className="text-[11px] font-medium uppercase tracking-[0.14em] text-[#737b87]">
                      Risk snapshot
                    </div>

                    <ShieldCheck size={14} className="text-[#68707c]" />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <Metric label="Account" value="$5,000" />
                    <Metric label="Risk" value="2.0%" />
                    <Metric label="Risk amount" value="$100" />
                    <Metric label="R:R target" value="1:3" />
                  </div>
                </div>

                <div className="rounded-xl border border-white/[0.07] bg-[#10141b] p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <div className="text-[11px] font-medium uppercase tracking-[0.14em] text-[#737b87]">
                      Market context
                    </div>

                    <Clock3 size={14} className="text-[#68707c]" />
                  </div>

                  <div className="space-y-3">
                    <MarketRow
                      symbol="EUR/USD"
                      price="1.1694"
                      change="+0.32%"
                      positive
                    />

                    <MarketRow
                      symbol="GBP/USD"
                      price="1.3518"
                      change="+0.18%"
                      positive
                    />

                    <MarketRow
                      symbol="XAU/USD"
                      price="3,389.40"
                      change="-0.21%"
                    />
                  </div>

                  <div className="mt-4 border-t border-white/[0.06] pt-3 text-[10px] text-[#565e69]">
                    Market prices shown here are UI placeholders until a market
                    data provider is connected.
                  </div>
                </div>

                <div className="rounded-xl border border-[#d7ff5f]/10 bg-[#d7ff5f]/[0.025] p-4">
                  <div className="flex gap-3">
                    <div className="mt-0.5">
                      <Sparkles size={15} className="text-[#d7ff5f]" />
                    </div>

                    <div>
                      <div className="text-xs font-medium">
                        Intelligence layer
                      </div>

                      <p className="mt-1.5 text-[11px] leading-relaxed text-[#747c88]">
                        Routes requests through deterministic trading tools,
                        offline knowledge retrieval and the local model when
                        available.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </main>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Components                                                                 */
/* -------------------------------------------------------------------------- */

function NavItem({
  icon,
  label,
  active = false,
  collapsed = false,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
  collapsed?: boolean;
}) {
  return (
    <button
      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-xs transition ${
        active
          ? "bg-white/[0.07] text-white"
          : "text-[#737b87] hover:bg-white/[0.04] hover:text-[#d6d9de]"
      } ${collapsed ? "justify-center" : ""}`}
    >
      <span className={active ? "text-[#d7ff5f]" : ""}>{icon}</span>

      {!collapsed && <span>{label}</span>}
    </button>
  );
}

function PromptButton({
  icon,
  text,
  onClick,
}: {
  icon: React.ReactNode;
  text: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 rounded-xl border border-white/[0.07] bg-[#0f1319] px-4 py-3 text-left text-xs text-[#9da4ae] transition hover:border-white/[0.13] hover:bg-white/[0.04] hover:text-white"
    >
      <span className="text-[#727b87]">{icon}</span>
      {text}
    </button>
  );
}

function StatusCard() {
  return (
    <div className="rounded-xl border border-white/[0.07] bg-[#10141b] p-4">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#d7ff5f]/10">
          <Bot size={15} className="text-[#d7ff5f]" />
        </div>

        <div>
          <div className="text-xs font-medium">Agent status</div>
          <div className="mt-0.5 flex items-center gap-1.5 text-[10px] text-[#6e7682]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#d7ff5f]" />
            Deterministic mode
          </div>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        <StatusRow label="Router" />
        <StatusRow label="Risk tools" />
        <StatusRow label="Position sizing" />
        <StatusRow label="Knowledge base" />
      </div>
    </div>
  );
}

function StatusRow({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-between text-[11px]">
      <span className="text-[#737b87]">{label}</span>
      <span className="flex items-center gap-1.5 text-[#aab1bb]">
        <span className="h-1.5 w-1.5 rounded-full bg-[#d7ff5f]" />
        Ready
      </span>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/[0.05] bg-white/[0.02] p-3">
      <div className="text-[10px] text-[#626a76]">{label}</div>
      <div className="mt-1 text-sm font-medium text-[#e0e3e7]">{value}</div>
    </div>
  );
}

function MarketRow({
  symbol,
  price,
  change,
  positive = false,
}: {
  symbol: string;
  price: string;
  change: string;
  positive?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <div className="text-xs font-medium">{symbol}</div>
        <div className="mt-0.5 text-[10px] text-[#626a76]">Spot</div>
      </div>

      <div className="text-right">
        <div className="text-xs font-medium">{price}</div>

        <div
          className={`mt-0.5 flex items-center justify-end gap-1 text-[10px] ${
            positive ? "text-[#a9c957]" : "text-[#d47a7a]"
          }`}
        >
          {positive ? (
            <TrendingUp size={10} />
          ) : (
            <TrendingDown size={10} />
          )}
          {change}
        </div>
      </div>
    </div>
  );
}