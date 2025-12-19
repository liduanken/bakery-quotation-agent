"use client";

import { Sidebar } from "@/components/ui/sidebar"

export function SidebarDemo() {
  return (
    <div className="flex h-screen w-screen flex-row">
      <Sidebar />
      <main className="flex h-screen grow flex-col overflow-auto ml-[3.05rem]">
        <div className="flex items-center justify-center flex-1">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Animated Sidebar Demo</h1>
            <p className="text-muted-foreground">Hover over the sidebar to see the animation!</p>
          </div>
        </div>
      </main>
    </div>
  );
} 