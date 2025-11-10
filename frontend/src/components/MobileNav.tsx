/**
 * Mobile Navigation Component
 *
 * Provides a responsive mobile navigation with:
 * - Hamburger menu button (44x44px touch target)
 * - Slide-out drawer with overlay
 * - Smooth animations
 * - Keyboard and screen reader accessibility
 * - Auto-close on navigation or overlay click
 */

import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { Button } from './ui/Button'

interface NavItem {
  label: string
  path: string
  icon: React.ReactNode
}

interface MobileNavProps {
  navItems: NavItem[]
}

export const MobileNav: React.FC<MobileNavProps> = ({ navItems }) => {
  const [isOpen, setIsOpen] = useState(false)
  const location = useLocation()

  // Close drawer when route changes
  useEffect(() => {
    setIsOpen(false)
  }, [location.pathname])

  // Close drawer on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      // Prevent body scroll when drawer is open
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = ''
    }
  }, [isOpen])

  return (
    <>
      {/* Hamburger Menu Button - 44x44px touch target */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(true)}
        className="sm:hidden min-w-[44px] min-h-[44px] p-2"
        aria-label="Open navigation menu"
        aria-expanded={isOpen}
      >
        <Menu className="w-6 h-6" />
      </Button>

      {/* Overlay Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-50 sm:hidden transition-opacity duration-300 ease-in-out"
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Slide-out Drawer */}
      <div
        className={`fixed top-0 left-0 h-full w-80 max-w-[85vw] bg-card border-r border-border z-50 sm:hidden transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation"
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-vividly-blue to-vividly-purple flex items-center justify-center">
              <span className="text-white font-bold text-sm">V</span>
            </div>
            <span className="font-display font-bold text-lg">Vividly</span>
          </div>

          {/* Close Button - 44x44px touch target */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(false)}
            className="min-w-[44px] min-h-[44px] p-2"
            aria-label="Close navigation menu"
          >
            <X className="w-6 h-6" />
          </Button>
        </div>

        {/* Navigation Items */}
        <nav className="px-4 py-6 space-y-2" aria-label="Primary navigation">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium transition-colors min-h-[44px] ${
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-foreground hover:bg-muted hover:text-foreground'
                }`}
                aria-current={isActive ? 'page' : undefined}
              >
                <span className="flex-shrink-0">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </div>
    </>
  )
}

export default MobileNav
