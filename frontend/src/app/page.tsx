'use client';

import React, { useState, useEffect, useRef } from 'react';
import { api } from '@/lib/api';
import { 
  Activity, 
  Send, 
  MessageSquare, 
  Settings, 
  Plus, 
  Zap, 
  Clock, 
  CheckCircle2, 
  AlertCircle,
  Package,
  Truck,
  CreditCard,
  User,
  Terminal,
  Play,
  XCircle,
  RefreshCw,
  Cpu,
  Pause,
  PlayCircle,
  ListFilter,
  BarChart3,
  Layers,
  ChevronRight,
  ShieldCheck,
  Command,
  Database,
  Globe,
  Lock,
  Search,
  ArrowRight,
  Maximize2,
  ExternalLink
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- Minimalist Components ---

const StatusPill = ({ status, pulse = false }: { status: string, pulse?: boolean }) => {
  const s = String(status).toLowerCase();
  const isRunning = s === 'running' || s === 'active' || s === '1';
  const isCompleted = s === 'completed' || s === 'resolved' || s === 'terminated' || s === '2';
  
  return (
    <div className={cn(
      "status-pill",
      isRunning ? "bg-indigo-50 text-indigo-700 border-indigo-100" : 
      isCompleted ? "bg-emerald-50 text-emerald-600 border-emerald-100" : 
      "bg-slate-50 text-slate-500 border-slate-100"
    )}>
      {pulse && <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />}
      {isRunning ? 'Operational' : (isCompleted ? 'Finalized' : s)}
    </div>
  );
};

const HeaderSmall = ({ title, icon: Icon, live = false }: { title: string, icon?: any, live?: boolean }) => (
  <div className="flex items-center justify-between mb-5">
    <div className="flex items-center gap-2.5 opacity-90">
      {Icon && <Icon size={14} className="text-slate-400" />}
      <h3 className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-800">
        {title}
      </h3>
    </div>
    {live && (
      <div className="flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
        </span>
        <span className="text-[9px] font-black uppercase tracking-widest text-indigo-500">Live Sync</span>
      </div>
    )}
  </div>
);

// --- Main Application ---

export default function Dashboard() {
  const [runs, setRuns] = useState<any[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<string | null>(null);
  const [orderDetails, setOrderDetails] = useState<any>(null);
  const [timeline, setTimeline] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [supervisors, setSupervisors] = useState<any>({});
  const [selectedTemplate, setSelectedTemplate] = useState('standard');
  const [instructionText, setInstructionText] = useState('');
  const [isSendingInstruction, setIsSendingInstruction] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchRuns();
    fetchSupervisors();
    const interval = setInterval(fetchRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedOrder) {
      fetchOrderDetails(selectedOrder);
      const interval = setInterval(() => fetchOrderDetails(selectedOrder), 3000);
      return () => clearInterval(interval);
    }
  }, [selectedOrder]);

  const fetchRuns = async () => {
    try {
      const res = await api.getRuns();
      setRuns(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSupervisors = async () => {
    try {
      const res = await api.getSupervisors();
      setSupervisors(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchOrderDetails = async (id: string) => {
    try {
      const [statusRes, timelineRes, actionsRes] = await Promise.all([
        api.getRunStatus(id),
        api.getTimeline(id),
        api.getActions(id)
      ]);
      setOrderDetails(statusRes.data);
      setTimeline(timelineRes.data);
      setActions(actionsRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleStartOrder = async () => {
    setIsStarting(true);
    try {
      const res = await api.startRun(undefined, selectedTemplate);
      await fetchRuns();
      setSelectedOrder(res.data.order_id);
      setShowConfig(false);
    } catch (e) {
      console.error(e);
    } finally {
      setIsStarting(false);
    }
  };

  const handleSendInstruction = async () => {
    if (!selectedOrder || !instructionText.trim()) return;
    setIsSendingInstruction(true);
    try {
      await api.sendInstruction(selectedOrder, instructionText);
      setInstructionText('');
      await fetchOrderDetails(selectedOrder);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSendingInstruction(false);
    }
  };

  const handleSendEvent = async (type: string, payload: any = {}) => {
    if (!selectedOrder) return;
    try {
      await api.sendEvent(selectedOrder, type, payload);
      await fetchOrderDetails(selectedOrder);
    } catch (e) {
      console.error(e);
    }
  };

  const handleAction = async (fn: Function) => {
    if (!selectedOrder) return;
    try {
      await fn(selectedOrder);
      await fetchRuns();
      await fetchOrderDetails(selectedOrder);
    } catch (e) {
      console.error(e);
    }
  };

  const filteredRuns = runs.filter(run => 
    run.workflow_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="flex h-screen bg-background text-foreground font-sans overflow-hidden">
      
      {/* High-Density Sidebar */}
      <div className="w-72 border-r border-slate-100 bg-white flex flex-col z-50">
        <div className="p-6 pb-4">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shadow-sm">
                <ShieldCheck size={18} className="text-white" />
              </div>
              <h1 className="text-sm font-display font-black tracking-tight text-slate-900">AEGIS</h1>
            </div>
            <button onClick={() => setShowConfig(!showConfig)} className="text-slate-400 hover:text-indigo-600 transition-colors">
               <Plus size={18} className={cn(showConfig && "rotate-45 transition-transform truncate")} />
            </button>
          </div>

          <div className="relative mb-6">
            <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300" />
            <input 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Operational Nodes..."
              className="w-full h-9 pl-9 pr-3 bg-slate-50 border border-slate-100 rounded-lg text-[10px] uppercase tracking-widest focus:outline-none focus:border-indigo-500/20 transition-all text-slate-700 placeholder:text-slate-300 font-bold"
            />
          </div>
        </div>

        <AnimatePresence>
          {showConfig && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="px-5 mb-6">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-3">
                <div className="grid gap-1">
                  {Object.entries(supervisors).map(([key, value]: [string, any]) => (
                    <button
                      key={key}
                      onClick={() => setSelectedTemplate(key)}
                      className={cn(
                        "w-full p-2.5 rounded-lg text-left transition-all border text-[10px] font-bold uppercase tracking-widest",
                        selectedTemplate === key ? "bg-white border-indigo-600 text-indigo-600 shadow-sm" : "bg-transparent border-transparent text-slate-400 hover:text-slate-600"
                      )}
                    >
                      {value.name}
                    </button>
                  ))}
                </div>
                <button onClick={handleStartOrder} disabled={isStarting} className="w-full btn-primary h-10">
                  {isStarting ? <RefreshCw size={12} className="animate-spin" /> : 'Launch Node'}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex-1 overflow-y-auto px-5 space-y-6 pt-2 pb-8 custom-scrollbar">
          <div className="space-y-1">
            {filteredRuns.map((run) => (
              <button
                key={run.workflow_id}
                onClick={() => setSelectedOrder(run.workflow_id)}
                className={cn(
                  "w-full group p-4 rounded-xl transition-all border text-left",
                  selectedOrder === run.workflow_id ? "bg-white border-indigo-600 shadow-sm" : "bg-transparent border-transparent hover:bg-slate-50"
                )}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className={cn(
                    "font-mono text-[10px] font-black",
                    selectedOrder === run.workflow_id ? "text-indigo-600" : "text-slate-400"
                  )}>
                    #{run.workflow_id.replace('order-', '').slice(0, 8).toUpperCase()}
                  </span>
                  <div className={cn("w-1.5 h-1.5 rounded-full", run.status === '1' ? "bg-emerald-500" : "bg-slate-200")} />
                </div>
                <div className="flex items-center justify-between opacity-50 text-[9px] font-black uppercase tracking-widest">
                   <div className="flex items-center gap-2">
                     <Clock size={10} />
                     {new Date(run.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                   </div>
                   {selectedOrder === run.workflow_id && <ChevronRight size={12} className="text-indigo-600" />}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="p-5 border-t border-slate-100">
           <button onClick={() => setShowSettings(!showSettings)} className="w-full flex items-center justify-between p-2 hover:bg-slate-50 rounded-lg group">
              <div className="flex items-center gap-3">
                 <div className="w-8 h-8 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400">
                    <User size={14} />
                 </div>
                 <div className="text-left">
                   <p className="text-[10px] font-black uppercase text-slate-900 tracking-widest">Root Auditor</p>
                   <p className="text-[9px] font-bold text-slate-400">AEGIS_04</p>
                 </div>
              </div>
              <Settings size={14} className={cn("text-slate-300 group-hover:rotate-90 transition-all", showSettings && "text-indigo-600")} />
           </button>
        </div>
      </div>

      {/* Primary Control Deck */}
      <div className="flex-1 flex flex-col relative overflow-hidden bg-[#fafafa]">
        {selectedOrder ? (
          <>
            <div className="h-20 border-b border-slate-100 flex items-center justify-between px-10 bg-white">
              <div className="flex items-center gap-6">
                 <h2 className="text-base font-black tracking-tight text-slate-900">
                   NODE <span className="text-indigo-600 uppercase">#{selectedOrder.replace('order-', '').slice(0, 10)}</span>
                 </h2>
                 <StatusPill status={orderDetails?.status || 'Active'} pulse={orderDetails?.status === 'Running'} />
                 <div className="w-px h-4 bg-slate-100" />
                 <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-400">
                   <span className="opacity-50">Next Evaluation:</span>
                   <span className="text-indigo-600">{orderDetails?.next_wake_up ? new Date(orderDetails.next_wake_up).toLocaleTimeString() : '...'}</span>
                 </div>
              </div>

              <div className="flex items-center gap-3">
                <button onClick={() => handleAction(api.pauseRun)} className="btn-secondary h-9">Suspend</button>
                <button onClick={() => handleAction(api.resumeRun)} className="btn-primary h-9">Resume</button>
                <button onClick={() => handleAction(api.terminateRun)} className="btn-danger h-9">Abort</button>
              </div>
            </div>

            <main className="flex-1 overflow-hidden flex flex-col p-8 gap-8">
              
              <div className="grid grid-cols-2 flex-1 gap-8 min-h-0">
                {/* Cognitive Stream (Half) */}
                <div className="flex flex-col min-h-0">
                   <HeaderSmall title="Autonomous Strategic Trace" icon={Zap} live={true} />
                   <div className="aeon-card flex-1 p-6 flex flex-col bg-white overflow-hidden shadow-sm">
                      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-6">
                         {orderDetails?.memory_summary ? (
                           <p className="text-[12px] text-slate-700 leading-relaxed font-medium italic border-l-2 border-indigo-500/20 pl-4">
                              {orderDetails.memory_summary}
                              <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity }} className="text-indigo-600 font-bold ml-1">|</motion.span>
                           </p>
                         ) : (
                           <div className="flex flex-col items-center justify-center h-full opacity-30 gap-4">
                              <RefreshCw size={24} className="animate-spin text-indigo-600" />
                              <span className="text-[10px] font-black uppercase tracking-widest">Synchronizing Trace...</span>
                           </div>
                         )}
                         
                         <div className="grid grid-cols-2 gap-4 pt-6 border-t border-slate-50">
                            <div>
                               <p className="text-[9px] font-black uppercase text-slate-400 tracking-widest mb-1.5">Model Confidence</p>
                               <p className="text-xl font-mono font-black text-emerald-600">{( (orderDetails?.confidence_score || 0.9) * 100).toFixed(0)}%</p>
                            </div>
                            <div>
                               <p className="text-[9px] font-black uppercase text-slate-400 tracking-widest mb-1.5">Operational Status</p>
                               <p className="text-xs font-black uppercase text-slate-900">{orderDetails?.status === '2' ? 'Node Concluded' : 'Active Feedback'}</p>
                            </div>
                         </div>
                      </div>
                   </div>
                </div>

                {/* Telemetry Thread (Half) */}
                <div className="flex flex-col min-h-0">
                   <HeaderSmall title="Operational Audit Log" icon={Layers} />
                   <div className="aeon-card flex-1 p-0 overflow-hidden bg-white shadow-sm flex flex-col">
                      <div className="flex-1 overflow-y-auto px-6 py-4 custom-scrollbar space-y-1">
                         {(() => {
                           const feed = [
                            ...timeline.map(t => ({ ...t, type: 'event' })),
                            ...actions.map(a => ({ ...a, type: 'action' }))
                           ].sort((a, b) => new Date(a.created_at || a.timestamp).getTime() - new Date(b.created_at || b.timestamp).getTime());
                           
                           return feed.map((item, idx) => {
                             const isAction = item.type === 'action';
                             const isLatest = idx === feed.length - 1;
                             return (
                              <div key={idx} className="flex gap-4 py-4 group first:pt-2 border-b border-slate-50 last:border-0 leading-tight">
                                <div className="flex flex-col items-center shrink-0">
                                  <div className={cn(
                                    "w-1.5 h-1.5 rounded-full mt-1.5",
                                    isAction ? "bg-indigo-600" : "bg-slate-300",
                                    isLatest && "relative"
                                  )}>
                                    {isLatest && <span className="absolute inset-0 rounded-full bg-indigo-400 animate-live" />}
                                  </div>
                                </div>
                                <div className="flex-1 space-y-2">
                                  <div className="flex items-center justify-between">
                                     <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-900">{item.event_type || item.action}</h4>
                                     <span className="text-[9px] font-mono font-bold text-slate-300">{new Date(item.created_at || item.timestamp).toLocaleTimeString()}</span>
                                  </div>
                                  <p className="text-[12px] text-slate-600 font-medium leading-normal">
                                     {(() => {
                                        try {
                                          const parsed = typeof item.payload === 'string' ? JSON.parse(item.payload) : item.payload;
                                          return parsed?.message || item.action_input || JSON.stringify(item.payload) || "-";
                                        } catch (e) {
                                          return item.action_input || String(item.payload) || "-";
                                        }
                                     })()}
                                  </p>
                                </div>
                              </div>
                             );
                           });
                         })()}
                      </div>
                   </div>
                </div>
              </div>

              {/* Functional Overrides Bottom Bar */}
              <div className="flex gap-8 items-end">
                <div className="flex-1 aeon-card p-4 bg-slate-950 text-white flex items-center justify-between gap-6">
                   <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center">
                        <Command size={16} className="text-white opacity-60" />
                      </div>
                      <input 
                        value={instructionText}
                        onChange={(e) => setInstructionText(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleSendInstruction()}
                        disabled={orderDetails?.status === '2'}
                        placeholder={orderDetails?.status === '2' ? "Node Concluded - Read Only" : "Mission Directive Override..."}
                        className="bg-transparent text-[12px] font-medium outline-none text-white placeholder:text-white/20 w-80 disabled:opacity-50" 
                      />
                      <button 
                         onClick={handleSendInstruction}
                         disabled={!instructionText.trim() || orderDetails?.status === '2' || isSendingInstruction}
                         className="p-1.5 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-20 text-indigo-400 hover:text-indigo-300"
                      >
                         <Send size={16} />
                      </button>
                   </div>
                   <div className="flex gap-2">
                      <button 
                        disabled={orderDetails?.status === '2'}
                        onClick={() => handleSendEvent("payment_confirmed")} 
                        className="btn-secondary h-8 px-4 disabled:opacity-20"
                      >
                        Validate Payment
                      </button>
                      <button 
                        disabled={orderDetails?.status === '2'}
                        onClick={() => handleSendEvent("shipment_created")} 
                        className="btn-secondary h-8 px-4 disabled:opacity-20"
                      >
                        Dispatch Order
                      </button>
                      <button 
                        disabled={isStarting}
                        onClick={handleStartOrder} 
                        className="btn-primary h-8 px-4"
                      >
                        {isStarting ? <RefreshCw size={12} className="animate-spin" /> : 'New Node'}
                      </button>
                   </div>
                </div>
              </div>

            </main>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-20 bg-white">
             <div className="w-16 h-16 rounded-[1.25rem] bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-300 mb-6">
                <ShieldCheck size={32} />
             </div>
             <h2 className="text-2xl font-display font-black text-slate-900 tracking-tighter mb-2">OPERATIONAL_CORE</h2>
             <p className="text-slate-400 text-[10px] uppercase tracking-[0.3em] font-black">Ready for engagement protocols</p>
             
             <div className="mt-16 grid grid-cols-3 gap-8 max-w-xl w-full">
                <div className="p-4 rounded-xl border border-slate-100 text-left">
                   <p className="text-[9px] font-black uppercase text-slate-300 tracking-widest mb-1">Status</p>
                   <p className="text-[10px] font-black text-emerald-600 uppercase">Synchronized</p>
                </div>
                <div className="p-4 rounded-xl border border-slate-100 text-left">
                   <p className="text-[9px] font-black uppercase text-slate-300 tracking-widest mb-1">Polling</p>
                   <p className="text-[10px] font-black text-slate-900 uppercase">1.2s Int</p>
                </div>
                <div className="p-4 rounded-xl border border-slate-100 text-left">
                   <p className="text-[9px] font-black uppercase text-slate-300 tracking-widest mb-1">Engine</p>
                   <p className="text-[10px] font-black text-slate-900 uppercase">Federated</p>
                </div>
             </div>
          </div>
        )}
      </div>
    </div>
  );
}
