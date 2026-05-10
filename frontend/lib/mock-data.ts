import type { LucideIcon } from "lucide-react";
import {
  Bot,
  Cloud,
  Folder,
  History,
  ImageUp,
  LayoutDashboard,
  Settings,
  WandSparkles,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  match: string;
};

export const navItems: NavItem[] = [
  { label: "Projects", href: "/dashboard", icon: Folder, match: "/dashboard" },
  { label: "Assets", href: "/project/spring-launch", icon: ImageUp, match: "/project" },
  { label: "AI Agents", href: "/project/spring-launch", icon: Bot, match: "/agents" },
  { label: "History", href: "/dashboard", icon: History, match: "/history" },
  { label: "Cloud", href: "/dashboard", icon: Cloud, match: "/cloud" },
  { label: "Settings", href: "/settings", icon: Settings, match: "/settings" },
];

export type Project = {
  id: string;
  title: string;
  platform: string;
  duration: string;
  status: "Editing" | "Review" | "Rendering" | "Archived";
  updated: string;
  progress: number;
  accent: "cyan" | "amber" | "neutral";
  image: string;
  tags: string[];
};

export const projects: Project[] = [
  {
    id: "spring-launch",
    title: "Spring Launch Product Cut",
    platform: "Douyin",
    duration: "0:45",
    status: "Editing",
    updated: "14 min ago",
    progress: 76,
    accent: "cyan",
    image:
      "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=960&q=80",
    tags: ["9:16", "TTS", "Subtitles"],
  },
  {
    id: "summer-collection",
    title: "Summer Collection Ad",
    platform: "TikTok",
    duration: "0:30",
    status: "Review",
    updated: "2h ago",
    progress: 91,
    accent: "neutral",
    image:
      "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=960&q=80",
    tags: ["Fashion", "1:1", "Color"],
  },
  {
    id: "phone-launch",
    title: "Tech Product Launch",
    platform: "YouTube",
    duration: "1:10",
    status: "Rendering",
    updated: "5h ago",
    progress: 43,
    accent: "cyan",
    image:
      "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=960&q=80",
    tags: ["16:9", "AI Processed"],
  },
  {
    id: "warehouse-demo",
    title: "Warehouse Demo Reel",
    platform: "Bilibili",
    duration: "2:05",
    status: "Archived",
    updated: "Yesterday",
    progress: 100,
    accent: "amber",
    image:
      "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=960&q=80",
    tags: ["Corporate", "VO"],
  },
];

export type Asset = {
  name: string;
  duration: string;
  score: number;
  used: boolean;
  tags: string[];
  gradient: string;
};

export const assets: Asset[] = [
  {
    name: "Hero_Spin_01.mp4",
    duration: "0:15",
    score: 92,
    used: true,
    tags: ["Close-up", "Product"],
    gradient: "from-cyan-500/40 via-blue-900/70 to-black",
  },
  {
    name: "Lifestyle_Cafe.mp4",
    duration: "0:08",
    score: 88,
    used: false,
    tags: ["Lifestyle", "Smooth"],
    gradient: "from-fuchsia-600/40 via-purple-950/70 to-black",
  },
  {
    name: "Macro_Texture.mov",
    duration: "0:12",
    score: 79,
    used: true,
    tags: ["Macro", "Detail"],
    gradient: "from-amber-400/35 via-stone-900/80 to-black",
  },
  {
    name: "Creator_Talk_A.mp4",
    duration: "0:22",
    score: 73,
    used: false,
    tags: ["Human", "Speech"],
    gradient: "from-emerald-500/35 via-slate-950/80 to-black",
  },
];

export type TimelineSegment = {
  label: string;
  track: "V1" | "V2" | "A1";
  start: string;
  width: string;
  color: "cyan" | "amber" | "gray";
};

export const timelineSegments: TimelineSegment[] = [
  { label: "Hook / device spin", track: "V1", start: "2%", width: "18%", color: "cyan" },
  { label: "Lifestyle cutaway", track: "V1", start: "21%", width: "15%", color: "gray" },
  { label: "Overlay: 1.2x faster", track: "V2", start: "34%", width: "21%", color: "cyan" },
  { label: "Creator proof", track: "V1", start: "55%", width: "18%", color: "gray" },
  { label: "CTA end frame", track: "V1", start: "74%", width: "15%", color: "amber" },
  { label: "VO ducked mix", track: "A1", start: "3%", width: "86%", color: "cyan" },
];

export type TraceEvent = {
  title: string;
  detail: string;
  time: string;
  state: "done" | "active" | "queued";
};

export const traceEvents: TraceEvent[] = [
  {
    title: "Understand Agent",
    detail: "4 clips analyzed, 18 highlight spans cached",
    time: "00:12",
    state: "done",
  },
  {
    title: "Plan Agent",
    detail: "Built 45s Douyin script around close-up proof shots",
    time: "00:18",
    state: "done",
  },
  {
    title: "Execute Agent",
    detail: "Rendering segment 4/6 with scale + crop filters",
    time: "00:31",
    state: "active",
  },
  {
    title: "Subtitle Agent",
    detail: "Queued after draft preview completes",
    time: "--:--",
    state: "queued",
  },
];

export type ModelRoute = {
  task: string;
  primary: string;
  fallback: string;
  latency: string;
  health: "online" | "degraded" | "offline";
  icon: LucideIcon;
};

export const modelRoutes: ModelRoute[] = [
  {
    task: "Video Understanding",
    primary: "qwen3-vl",
    fallback: "gemini-2.5-flash",
    latency: "840ms",
    health: "online",
    icon: WandSparkles,
  },
  {
    task: "Edit Planning",
    primary: "claude-sonnet-4",
    fallback: "gpt-4o",
    latency: "1.2s",
    health: "online",
    icon: LayoutDashboard,
  },
  {
    task: "Correction Intent",
    primary: "claude-sonnet-4",
    fallback: "gpt-4o-mini",
    latency: "390ms",
    health: "online",
    icon: Bot,
  },
  {
    task: "TTS Script",
    primary: "qwen3",
    fallback: "claude-sonnet-4",
    latency: "620ms",
    health: "degraded",
    icon: WandSparkles,
  },
];
