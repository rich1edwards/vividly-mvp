import React from 'react'
import DashboardLayout from '../components/DashboardLayout'
import { Card, CardHeader, CardTitle, CardDescription } from '../components/ui/Card'
import { useAuthStore } from '../store/authStore'

export const SuperAdminDashboard: React.FC = () => {
  const { user } = useAuthStore()

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-display font-bold">
            Vividly Platform Administration
          </h1>
          <p className="text-muted-foreground mt-2">
            Welcome, {user?.first_name}! Full system access and control
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>All Organizations</CardTitle>
              <CardDescription>Manage all organizations and schools across the platform</CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System Analytics</CardTitle>
              <CardDescription>Platform-wide usage and performance metrics</CardDescription>
            </CardHeader>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System Settings</CardTitle>
              <CardDescription>Configure platform-wide settings and features</CardDescription>
            </CardHeader>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Platform Status</CardTitle>
            <CardDescription>Real-time system health and monitoring</CardDescription>
          </CardHeader>
        </Card>
      </div>
    </DashboardLayout>
  )
}

export default SuperAdminDashboard
