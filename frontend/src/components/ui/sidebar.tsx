"use client";

import { cn } from "@/lib/utils";
import { ScrollArea } from "@/components/ui/scroll-area";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge"
import {
  HelpCircle,
  MessageSquare,
  Plus,
  Settings,
  UserCircle,
  LogOut,
  BookOpen,
  ChevronsUpDown,
} from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";

interface SidebarProps {
  onNewChat?: () => void;
  currentPage?: 'home' | 'help';
}

const sidebarVariants = {
  open: {
    width: "15rem",
  },
  closed: {
    width: "3.05rem",
  },
};

const contentVariants = {
  open: { display: "block", opacity: 1 },
  closed: { display: "block", opacity: 1 },
};

const variants = {
  open: {
    x: 0,
    opacity: 1,
    transition: {
      x: { stiffness: 1000, velocity: -100 },
    },
  },
  closed: {
    x: -20,
    opacity: 0,
    transition: {
      x: { stiffness: 100 },
    },
  },
};

const transitionProps = {
  type: "tween" as const,
  ease: "easeOut" as const,
  duration: 0.2,
  staggerChildren: 0.1,
};

const staggerVariants = {
  open: {
    transition: { staggerChildren: 0.03, delayChildren: 0.02 },
  },
};

export function Sidebar({ onNewChat, currentPage = 'home' }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const pathname = usePathname();

  return (
    <motion.div
      className={cn(
        "sidebar fixed left-0 z-40 h-full shrink-0 border-r fixed",
      )}
      initial={isCollapsed ? "closed" : "open"}
      animate={isCollapsed ? "closed" : "open"}
      variants={sidebarVariants}
      transition={transitionProps}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
    >
      <motion.div
        className={`relative z-40 flex text-muted-foreground h-full shrink-0 flex-col bg-white dark:bg-black transition-all`}
        variants={contentVariants}
      >
        <motion.ul variants={staggerVariants} className="flex h-full flex-col">
          <div className="flex grow flex-col items-center">
            <div className="flex h-[70px] w-full shrink-0 border-b p-3">
              <div className="flex w-full items-center justify-center">
                <motion.div
                  className="flex items-center justify-center"
                  animate={{
                    width: isCollapsed ? "28px" : "140px",
                    height: isCollapsed ? "28px" : "38px"
                  }}
                  transition={{
                    type: "tween",
                    ease: "easeOut",
                    duration: 0.2
                  }}
                >
                  <Image
                    src={isCollapsed ? "/bakery-logo.jpg" : "/bakery-logo.jpg"}
                    alt={isCollapsed ? "Bakery Logo" : "Bakery Quotation System"}
                    width={isCollapsed ? 28 : 140}
                    height={isCollapsed ? 28 : 38}
                    className="object-contain max-w-full max-h-full transition-opacity duration-200 rounded-full"
                    priority
                  />
                </motion.div>
              </div>
            </div>

            <div className="flex h-full w-full flex-col">
              <div className="flex grow flex-col gap-4">
                <ScrollArea className="h-16 grow p-2">
                  <div className={cn("flex w-full flex-col gap-1")}>
                    <Link
                      href="/"
                      className={cn(
                        "flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition hover:bg-muted hover:text-primary",
                        pathname === "/" && "bg-muted",
                      )}
                      style={pathname === "/" ? { color: "#23938c" } : {}}
                    >
                      <MessageSquare className="h-4 w-4" />
                      <motion.li variants={variants}>
                        {!isCollapsed && (
                          <div className="ml-2 flex items-center gap-2">
                            <div className="flex flex-col">
                              <p className="text-sm font-medium">Chat</p>
                            </div>
                            <Badge
                              className={cn(
                                "flex h-fit w-fit items-center gap-1.5 rounded border-none px-1.5",
                              )}
                              variant="outline"
                              style={{
                                backgroundColor: "#23938c20",
                                color: "#23938c"
                              }}
                            >
                              AI
                            </Badge>
                          </div>
                        )}
                      </motion.li>
                    </Link>
                    
                    <Separator className="w-full my-2" />
                    <button
                      onClick={onNewChat}
                      className="flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition hover:bg-muted hover:text-primary"
                    >
                      <Plus className="h-4 w-4" />
                      <motion.li variants={variants}>
                        {!isCollapsed && (
                          <div className="ml-2">
                            <p className="text-sm font-medium">New Chat</p>
                          </div>
                        )}
                      </motion.li>
                    </button>
                    <Link
                      href="/help"
                      className={cn(
                        "flex h-8 w-full flex-row items-center rounded-md px-2 py-1.5 transition hover:bg-muted hover:text-primary",
                        pathname?.includes("help") && "bg-muted",
                      )}
                      style={pathname?.includes("help") ? { color: "#23938c" } : {}}
                    >
                      <HelpCircle className="h-4 w-4" />
                      <motion.li variants={variants}>
                        {!isCollapsed && (
                          <div className="ml-2">
                            <p className="text-sm font-medium">Help</p>
                          </div>
                        )}
                      </motion.li>
                    </Link>
                  </div>
                </ScrollArea>
              </div>
              <div className="flex flex-col p-2">
                <div>
                  <DropdownMenu modal={false}>
                    <DropdownMenuTrigger className="w-full">
                      <div className="flex h-8 w-full flex-row items-center gap-2 rounded-md px-2 py-1.5 transition hover:bg-muted hover:text-primary">
                        <Avatar className="size-4">
                          <AvatarFallback>U</AvatarFallback>
                        </Avatar>
                        <motion.li
                          variants={variants}
                          className="flex w-full items-center gap-2"
                        >
                          {!isCollapsed && (
                            <>
                              <div className="flex flex-col">
                                <p className="text-sm font-medium">User</p>
                                <p className="text-xs text-muted-foreground" dir="rtl">المستخدم</p>
                              </div>
                              <ChevronsUpDown className="ml-auto h-4 w-4 text-muted-foreground/50" />
                            </>
                          )}
                        </motion.li>
                      </div>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent sideOffset={5}>
                      <div className="flex flex-row items-center gap-2 p-2">
                        <Avatar className="size-6">
                          <AvatarFallback>JD</AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col text-left">
                          <span className="text-sm font-medium">John Doe</span>
                          <span className="line-clamp-1 text-xs text-muted-foreground">
                            john@example.com
                          </span>
                        </div>
                      </div>
                      <DropdownMenuSeparator />
                                            <DropdownMenuItem>
                        <UserCircle className="h-4 w-4" />
                        <div className="flex flex-col">
                          <span>Profile</span>
                          <span className="text-xs text-muted-foreground" dir="rtl">الملف الشخصي</span>
                        </div>
                      </DropdownMenuItem>
                      <DropdownMenuItem className="flex items-center gap-2">
                        <LogOut className="h-4 w-4" />
                        <div className="flex flex-col">
                          <span>Sign out</span>
                          <span className="text-xs text-muted-foreground" dir="rtl">تسجيل الخروج</span>
                        </div>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            </div>
          </div>
        </motion.ul>
      </motion.div>
    </motion.div>
  );
} 