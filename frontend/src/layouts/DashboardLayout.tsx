import { useEffect, useState } from "react";
import { Outlet, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  ShoppingCart,
  Users,
  Package,
  Warehouse,
  BarChart3,
  Bot,
  FileText,
  ScrollText,
  LogOut,
  ChevronLeft,
  Activity,
  Boxes,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Toaster } from "@/components/ui/toaster";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
  group: "Workspace" | "Operations" | "Intelligence";
}

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard, group: "Workspace" },
  { label: "Orders", href: "/orders", icon: ShoppingCart, group: "Workspace" },
  { label: "Customers", href: "/customers", icon: Users, group: "Workspace" },
  { label: "Products", href: "/products", icon: Package, group: "Operations" },
  { label: "Inventory", href: "/inventory", icon: Warehouse, group: "Operations" },
  { label: "Analytics", href: "/analytics", icon: BarChart3, group: "Intelligence" },
  { label: "AI Assistant", href: "/ai-assistant", icon: Bot, group: "Intelligence" },
  { label: "Reports", href: "/reports", icon: FileText, group: "Intelligence" },
  {
    label: "Audit Logs",
    href: "/audit-logs",
    icon: ScrollText,
    adminOnly: true,
    group: "Intelligence",
  },
];

export default function DashboardLayout() {
  const { user, logout, fetchUser } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isAdmin = user?.role?.name === "admin" || user?.role?.name === "manager";

  const filteredNavItems = navItems.filter(
    (item) => !item.adminOnly || isAdmin,
  );
  const groups: NavItem["group"][] = ["Workspace", "Operations", "Intelligence"];
  const currentPage = navItems.find((item) => location.pathname.startsWith(item.href));

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="flex h-screen min-w-[1180px] overflow-hidden bg-background">
      <aside
        className={cn(
          "relative z-20 flex shrink-0 flex-col border-r border-white/5 bg-[#10131d] text-sidebar-foreground shadow-2xl shadow-slate-950/10 transition-all duration-300",
          collapsed ? "w-[72px]" : "w-[248px]",
        )}
      >
        <div className="flex h-[72px] items-center justify-between px-4">
          {!collapsed && (
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 shadow-lg shadow-cyan-950/20">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-[15px] font-semibold tracking-[-0.02em] text-white">InsightFlow</h1>
                <p className="text-[10px] font-medium uppercase tracking-[0.16em] text-slate-500">Operations OS</p>
              </div>
            </div>
          )}
          {collapsed && (
            <div className="mx-auto flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400 text-slate-950">
              <Activity className="h-5 w-5" />
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            className={cn("h-8 w-8 text-slate-500 hover:bg-white/10 hover:text-white", collapsed && "absolute -right-4 top-[82px] z-30 rounded-full border border-slate-700 bg-[#171b28]")}
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
          >
            <ChevronLeft
              className={cn(
                "h-4 w-4 transition-transform",
                collapsed && "rotate-180",
              )}
            />
          </Button>
        </div>

        <Separator className="bg-sidebar-border" />

        <nav className="flex-1 overflow-y-auto px-3 py-4">
          {groups.map((group) => (
            <div key={group} className="mb-5">
              {!collapsed && (
                <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600">{group}</p>
              )}
              <div className="space-y-1">
                {filteredNavItems.filter((item) => item.group === group).map((item) => (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    title={collapsed ? item.label : undefined}
                    className={({ isActive }) =>
                      cn(
                        "group relative flex h-10 items-center gap-3 rounded-lg px-3 text-[13px] font-medium transition-all",
                        "hover:bg-white/[0.055] hover:text-white",
                        isActive ? "bg-white/[0.075] text-white" : "text-slate-400",
                        collapsed && "justify-center px-2",
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && <span className="absolute -left-3 h-5 w-[3px] rounded-r-full bg-cyan-400" />}
                        <item.icon className={cn("h-[18px] w-[18px] shrink-0 transition-colors", isActive ? "text-cyan-300" : "text-slate-500 group-hover:text-slate-300")} />
                        {!collapsed && <span>{item.label}</span>}
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>

        <Separator className="bg-sidebar-border" />

        <div className="p-3">
          <div
            className={cn(
              "flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.035] p-2",
              collapsed && "justify-center",
            )}
          >
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-sidebar-accent text-xs text-white">
                {user ? getInitials(user.full_name || user.email) : "U"}
              </AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="min-w-0 flex-1 overflow-hidden">
                <p className="truncate text-sm font-medium text-white">
                  {user?.full_name || user?.email || "User"}
                </p>
                <p className="truncate text-xs text-sidebar-foreground/60">
                  {user?.role?.name || "viewer"} workspace
                </p>
              </div>
            )}
            {!collapsed && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0 text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-white"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex h-[72px] shrink-0 items-center gap-4 border-b border-slate-200/80 bg-white/95 px-7 backdrop-blur">
          <div className="flex flex-1 items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-slate-50 text-slate-500">
              {currentPage ? <currentPage.icon className="h-[18px] w-[18px]" /> : <Boxes className="h-[18px] w-[18px]" />}
            </div>
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">InsightFlow / Workspace</p>
              <p className="text-sm font-semibold text-slate-800">{currentPage?.label || "Operations"}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-[11px] font-semibold text-emerald-700">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-[0_0_0_3px_rgb(16_185_129/0.12)]" />
              Live data
            </div>
            <span className="max-w-[220px] truncate text-sm text-muted-foreground">
              {user?.email}
            </span>
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary text-xs text-primary-foreground">
                {user ? getInitials(user.full_name || user.email) : "U"}
              </AvatarFallback>
            </Avatar>
          </div>
        </header>

        <main className="surface-grid flex-1 overflow-y-auto p-7">
          <div className="mx-auto w-full max-w-[1600px]"><Outlet /></div>
        </main>
      </div>

      <Toaster />
    </div>
  );
}
