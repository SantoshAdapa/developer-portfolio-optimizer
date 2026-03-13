"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Sparkles, Menu, X, Sun, Moon } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { siteConfig, navLinks } from "@/lib/constants";
import { useTheme } from "@/lib/theme-provider";

export function Navbar() {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-background/60 backdrop-blur-xl"
    >
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 shadow-lg shadow-blue-500/25 group-hover:shadow-blue-500/40 transition-shadow">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight">
            {siteConfig.name}
          </span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "relative px-4 py-2 text-sm font-medium rounded-lg transition-colors",
                pathname === link.href
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {pathname === link.href && (
                <motion.div
                  layoutId="navbar-active"
                  className="absolute inset-0 rounded-lg bg-foreground/[0.06]"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <span className="relative z-10">{link.label}</span>
            </Link>
          ))}
        </div>

        {/* Theme Toggle */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={toggleTheme}
            className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border/50 bg-muted/50 text-muted-foreground hover:text-foreground hover:bg-muted transition-all duration-200"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            <Sun className={cn("h-4 w-4 absolute transition-all duration-300", theme === "dark" ? "opacity-0 rotate-90 scale-0" : "opacity-100 rotate-0 scale-100")} />
            <Moon className={cn("h-4 w-4 absolute transition-all duration-300", theme === "dark" ? "opacity-100 rotate-0 scale-100" : "opacity-0 -rotate-90 scale-0")} />
          </button>
        </div>

        {/* Mobile Menu Toggle */}
        <div className="md:hidden flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg border border-border/50 bg-muted/50 text-muted-foreground hover:text-foreground transition-colors"
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
          <button
            className="p-2 rounded-lg hover:bg-muted/50 transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="md:hidden border-t border-border/50 bg-background/95 backdrop-blur-xl"
        >
          <div className="flex flex-col gap-1 p-4">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  "px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                  pathname === link.href
                    ? "text-foreground bg-foreground/[0.06]"
                    : "text-muted-foreground hover:text-foreground hover:bg-foreground/[0.04]"
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </motion.div>
      )}
    </motion.header>
  );
}
