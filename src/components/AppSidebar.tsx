/**
 * AppSidebar - الشريط الجانبي الرئيسي
 * يظهر على الجانب الأيمن (RTL) مع التنقل والتاريخ
 */
import { useLocation, useNavigate } from "react-router-dom";
import { useHistory } from "@/contexts/HistoryContext";
import {
  Heart,
  PenLine,
  Clock,
  BookOpen,
  MessageSquareText,
  Home,
  Trash2,
  Settings,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";

const navItems = [
  { title: "الرئيسية", url: "/", icon: Home },
  { title: "مزاج اليوم", url: "/mood", icon: Heart },
  { title: "رحلة عبر الزمن", url: "/journey", icon: Clock },
  { title: "تفسير الأبيات", url: "/interpret", icon: MessageSquareText },
  { title: "ساعدني أكتب", url: "/write", icon: PenLine },
  { title: "كنوز الكلمات", url: "/treasures", icon: BookOpen },
];

const pageNameMap: Record<string, string> = {
  mood: "مزاج اليوم",
  write: "ساعدني أكتب",
  journey: "رحلة عبر الزمن",
  treasures: "كنوز الكلمات",
  interpret: "تفسير الأبيات",
};

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const location = useLocation();
  const navigate = useNavigate();
  const { history, clearHistory } = useHistory();

  const isActive = (path: string) =>
    path === "/" ? location.pathname === "/" : location.pathname.startsWith(path);

  return (
    <Sidebar side="right" collapsible="icon" className="border-r-0 border-l border-sidebar-border">
      <SidebarContent className="scrollbar-thin">
        {/* قسم التنقل */}
        <SidebarGroup>
          <SidebarGroupLabel className="font-display text-sidebar-primary text-base tracking-wide">
            {!collapsed && "لَــسِــنْ"}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton
                    onClick={() => navigate(item.url)}
                    isActive={isActive(item.url)}
                    className="font-ui"
                    tooltip={item.title}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {!collapsed && <span>{item.title}</span>}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {/* قسم التاريخ */}
        {!collapsed && (
          <>
            <Separator className="bg-sidebar-border mx-2" />
            <SidebarGroup>
              <div className="flex items-center justify-between px-2">
                <SidebarGroupLabel className="font-ui text-sidebar-primary p-0">
                  السجل
                </SidebarGroupLabel>
                {history.length > 0 && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 text-sidebar-foreground/50 hover:text-destructive"
                    onClick={clearHistory}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
              </div>
              <SidebarGroupContent>
                <ScrollArea className="h-[300px]">
                  {history.length === 0 ? (
                    <p className="text-sidebar-foreground/40 text-xs font-ui px-3 py-4 text-center">
                      لا يوجد سجل بعد
                    </p>
                  ) : (
                    <div className="space-y-1 px-1">
                      {history.map((item) => (
                        <button
                          key={item.id}
                          className="w-full text-right px-3 py-2 rounded-md hover:bg-sidebar-accent transition-colors group"
                          onClick={() => navigate(`/${item.pageId}`)}
                        >
                          <p className="text-xs font-ui text-sidebar-foreground truncate">
                            {item.preview}
                          </p>
                          <p className="text-[10px] font-ui text-sidebar-foreground/40 mt-0.5">
                            {pageNameMap[item.pageId] || item.pageName}
                          </p>
                        </button>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </SidebarGroupContent>
            </SidebarGroup>
          </>
        )}
      </SidebarContent>

      <SidebarFooter>
        {!collapsed && (
          <div className="flex items-center gap-2 px-2 py-2">
            <Settings className="h-4 w-4 text-sidebar-foreground/40" />
            <span className="text-xs font-ui text-sidebar-foreground/40">الإعدادات</span>
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  );
}
