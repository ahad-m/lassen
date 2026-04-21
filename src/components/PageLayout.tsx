/**
 * PageLayout — تخطيط الصفحات الداخلية مع شريط جانبي وخلفية موحّدة دافئة
 */
import React from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";

interface PageLayoutProps {
  children: React.ReactNode;
  title?: string;
}

const PageLayout: React.FC<PageLayoutProps> = ({ children, title }) => {
  return (
    <SidebarProvider defaultOpen={false}>
      <div className="min-h-screen flex w-full bg-warm-page">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-h-screen">
          <header className="h-14 flex items-center border-b border-brown-200/50 px-4 bg-background/70 backdrop-blur-md sticky top-0 z-40">
            <SidebarTrigger className="text-brown-600 hover:text-brown-700" />
            <div className="flex items-baseline gap-3 mr-4">
              <span className="font-display text-xl text-gradient-brown leading-none">
                لَسِنْ
              </span>
              {title && (
                <>
                  <span className="text-brown-300">•</span>
                  <h1 className="font-kufi text-sm text-brown-600/80">{title}</h1>
                </>
              )}
            </div>
          </header>
          <main className="flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default PageLayout;
